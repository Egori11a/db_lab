from quart import Blueprint, render_template, request, redirect, url_for, flash, current_app, session, abort
from app.auth_token_utils import store_token, get_user_by_token
from app.cache_utils import get_or_cache_json
from app.pubsub import publish_event
import json
from app.redis_client import get_redis
import uuid
from app.db import *
import bcrypt
import logging
from quart import g

logger = logging.getLogger(__name__)
main = Blueprint("main", __name__)

from app.auth_token_utils import get_user_by_token

@main.before_app_request
async def load_user_roles():
    token = session.get("auth_token")
    user_id = session.get("user_id")

    # Проверка токена через Redis
    if token:
        redis_user_id = await get_user_by_token(token)
        if not redis_user_id or redis_user_id != user_id:
            # Токен невалиден — принудительно выходим
            session.pop("user_id", None)
            session.pop("auth_token", None)
            g.user_roles = []
            return  # пропускаем дальнейшие проверки
    elif user_id:
        # Нет токена, но есть user_id — тоже невалидно
        session.pop("user_id", None)
        g.user_roles = []
        return
    else:
        g.user_roles = []
        return

    # Если всё ок — загружаем роли
    try:
        g.user_roles = await get_user_roles(current_app.db_pool, user_id)
    except Exception as e:
        # БД может быть отключена — для Redis-страниц пропускаем
        g.user_roles = []

@main.route("/", methods=["GET"])
async def home():
    """
    Главная страница интернет-магазина с возможностью поиска и фильтрации.
    """
    try:
        query = request.args.get('q', '').strip()
        category_id = request.args.get('category', '')
        manufacturer = request.args.get('manufacturer', '').strip()

        #categories = await get_all_categories(current_app.db_pool)
        categories = await get_or_cache_json("cache:categories", lambda: get_all_categories(current_app.db_pool))
        #manufacturers = await get_all_manufacturers(current_app.db_pool)
        manufacturers = await get_or_cache_json("cache:manufacturers", lambda: get_all_manufacturers(current_app.db_pool))

        products = await search_products(
            current_app.db_pool,
            query=query,
            category_id=category_id,
            manufacturer=manufacturer
        )
    
        if query or category_id or manufacturer:
            search_message = "Результаты поиска"
        else:
            search_message = None

        return await render_template(
            "home.html",
            products=products,
            categories=categories,
            manufacturers=manufacturers,
            search_message=search_message
        )
    except Exception as e:
        logger.error(f"Ошибка при загрузке главной страницы: {e}")
        return f"Ошибка при загрузке главной страницы: {e}", 500


@main.route("/profile")
async def profile():
    """
    Страница профиля пользователя.
    """
    user_id = session.get("user_id")
    if not user_id:
        await flash("Пожалуйста, войдите в систему.", "warning")
        return redirect(url_for("main.login"))

    try:
        user = await get_user_by_id(current_app.db_pool, user_id)
        if not user:
            await flash("Информация о пользователе не найдена.", "danger")
            return redirect(url_for("main.login"))

        last_orders = await get_last_orders(current_app.db_pool, user_id)

        return await render_template(
            "profile.html",
            username=user["username"],
            email=user["email"],
            last_orders=last_orders
        )
    except Exception as e:
        current_app.logger.error(f"Ошибка при загрузке профиля пользователя {user_id}: {e}")
        await flash("Произошла ошибка при загрузке профиля.", "danger")
        return redirect(url_for("main.home"))


@main.route("/register", methods=["GET", "POST"])
async def register():
    """
    Регистрация нового пользователя.
    """
    if request.method == "POST":
        logger.info("Начат процесс регистрации.")
        form = await request.form
        username = form.get("username")
        email = form.get("email")
        password = form.get("password")

        if not username or not email or not password:
            logger.warning("Не все поля формы регистрации заполнены.")
            await flash("Все поля обязательны для заполнения!", "warning")
            return redirect(url_for("main.register"))

        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        async with current_app.db_pool.acquire():
            try:
                existing_user = await get_user_by_email(current_app.db_pool, email)
                if existing_user:
                    logger.warning(f"Пользователь с email {email} уже существует.")
                    await flash("Пользователь с таким email уже существует.", "danger")
                    return redirect(url_for("main.register"))

                user_id = await create_user(current_app.db_pool, username, hashed_password, email)
                logger.info(f"Пользователь {email} успешно зарегистрирован с ID: {user_id}.")

                await flash("Регистрация прошла успешно! Теперь вы можете войти.", "success")
                return redirect(url_for("main.login"))
            except Exception as e:
                logger.error(f"Ошибка при регистрации пользователя {email}: {e}")
                await flash("Произошла ошибка. Попробуйте ещё раз.", "danger")
                return redirect(url_for("main.register"))

    return await render_template("register.html")

@main.route("/login", methods=["GET", "POST"])
async def login():
    """
    Авторизация пользователя.
    """
    if request.method == "POST":
        logger.info("Начат процесс авторизации.")
        form = await request.form
        email = form.get("email")
        password = form.get("password")

        if not email or not password:
            logger.warning("Не все поля формы авторизации заполнены.")
            await flash("Все поля обязательны для заполнения!", "warning")
            return redirect(url_for("main.login"))

        user = await get_user_by_email(current_app.db_pool, email)
        if not user:
            logger.warning(f"Не найден пользователь с email {email}.")
            await flash("Неверный email или пароль.", "danger")
            return redirect(url_for("main.login"))

        hashed_password = user["hashed_password"]
        if not bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8")):
            logger.warning(f"Неверный пароль для email {email}.")
            await flash("Неверный email или пароль.", "danger")
            return redirect(url_for("main.login"))

        logger.info(f"Пользователь {email} успешно авторизовался.")
        session["user_id"] = str(user["user_id"])

        # Генерируем уникальный токен и сохраняем его в Redis с TTL
        token = str(uuid.uuid4())
        await store_token(token, str(user["user_id"]))
        session["auth_token"] = token

        await flash(f"Добро пожаловать, {user['username']}!", "success")
        return redirect(url_for("main.home"))

    logger.info("Отображение страницы авторизации.")
    return await render_template("login.html")

@main.route("/logout")
async def logout():
    """
    Выход из системы.
    """
    logger.info("Пользователь вышел из системы.")
    session.pop("user_id", None)
    await flash("Вы вышли из системы.", "info")
    return redirect(url_for("main.login"))

@main.route("/cart", methods=["GET"])
async def cart():
    """
    Страница корзины пользователя.
    """
    user_id = session.get("user_id")
    if not user_id:
        await flash("Пожалуйста, войдите в систему.", "warning")
        return redirect(url_for("main.login"))

    try:
        cart_items = await get_cart_items(current_app.db_pool, user_id)

        total_cost = sum(item["total_cost"] for item in cart_items)

        return await render_template("cart.html", cart_items=cart_items, total_cost=total_cost)
    except Exception as e:
        logger.error(f"Ошибка при загрузке корзины пользователя {user_id}: {e}")
        await flash("Произошла ошибка при загрузке корзины.", "danger")
        return redirect(url_for("main.home"))

@main.route("/cart/update", methods=["POST"])
async def update_cart():
    """
    Обновить количество товаров в корзине.
    """
    user_id = session.get("user_id")
    if not user_id:
        await flash("Пожалуйста, войдите в систему.", "warning")
        return redirect(url_for("main.login"))

    form = await request.form
    quantities = {}
    for key in form:
        if key.startswith('quantities[') and key.endswith(']'):
            product_id = key[len('quantities['):-1]
            quantities[product_id] = form.get(key)

    try:
        await update_cart_quantities(current_app.db_pool, user_id, quantities)
        await flash("Корзина обновлена.", "success")
    except Exception as e:
        logger.error(f"Ошибка при обновлении корзины: {e}")
        await flash(str(e), "danger")

    return redirect(url_for("main.cart"))


@main.route("/order", methods=["POST"])
async def place_order():
    """
    Оформить заказ.
    """
    user_id = session.get("user_id")
    if not user_id:
        await flash("Пожалуйста, войдите в систему.", "warning")
        return redirect(url_for("main.login"))

    try:
        await process_order(current_app.db_pool, user_id)
        #################################################
        await publish_event("orders", {
            "type": "new_order",
            "user_id": user_id
        })
        await flash("Заказ успешно оформлен!", "success")
    except Exception as e:
        logger.error(f"Ошибка при оформлении заказа: {e}")
        await flash(str(e), "danger")

    return redirect(url_for("main.home"))

@main.route("/repeat_order", methods=["POST"])
async def repeat_order():
    """
    Повторить заказ.
    """
    user_id = session.get("user_id")
    if not user_id:
        await flash("Пожалуйста, войдите в систему.", "warning")
        return redirect(url_for("main.login"))

    order_id = (await request.form).get("order_id")
    if not order_id:
        await flash("Неверный запрос.", "danger")
        return redirect(url_for("main.profile"))

    try:
        async with current_app.db_pool.acquire() as conn:
            products = await conn.fetch("""
                SELECT product_id, quantity
                FROM order_items
                WHERE order_id = $1
            """, order_id)

            for product in products:
                await add_to_cart(current_app.db_pool, user_id, product["product_id"], product["quantity"])

        await flash("Заказ успешно добавлен в корзину.", "success")
    except Exception as e:
        current_app.logger.error(f"Ошибка при повторении заказа {order_id}: {e}")
        await flash("Произошла ошибка при повторении заказа.", "danger")

    return redirect(url_for("main.cart"))


@main.route("/cart/add", methods=["POST"])
async def add_item_to_cart():
    """
    Добавить товар в корзину.
    """
    user_id = session.get("user_id")
    if not user_id:
        await flash("Пожалуйста, войдите в систему, чтобы добавить товар в корзину.", "warning")
        return redirect(url_for("main.login"))

    form = await request.form
    product_id = form.get("product_id")
    quantity = int(form.get("quantity", 1))

    try:
        product = await get_product_by_id(current_app.db_pool, product_id)
        if not product:
            await flash("Товар не найден.", "danger")
            return redirect(url_for("main.home"))

        if quantity < 1 or quantity > product["stock"]:
            await flash("Некорректное количество товара.", "warning")
            return redirect(url_for("main.home"))

        await add_to_cart(current_app.db_pool, user_id, product_id, quantity)
        await flash("Товар успешно добавлен в корзину.", "success")
    except Exception as e:
        logger.error(f"Ошибка при добавлении товара в корзину: {e}")
        await flash("Ошибка при добавлении товара в корзину.", "danger")

    return redirect(request.referrer or url_for("main.home"))

@main.route("/cart/remove/<product_id>", methods=["POST"])
async def remove_item_from_cart(product_id):
    """
    Удалить товар из корзины.
    """
    user_id = session.get("user_id")
    if not user_id:
        await flash("Пожалуйста, войдите в систему.", "warning")
        return redirect(url_for("main.login"))

    try:
        await remove_from_cart(current_app.db_pool, user_id, product_id)
        await flash("Товар удалён из корзины.", "success")
    except Exception as e:
        logger.error(f"Ошибка при удалении товара из корзины: {e}")
        await flash("Произошла ошибка при удалении товара из корзины.", "danger")

    return redirect(url_for("main.cart"))

@main.route("/product/<product_id>", methods=["GET", "POST"])
async def product_page(product_id):
    """
    Страница товара с описанием и отзывами.
    """
    user_id = session.get("user_id")

    if request.method == "POST":
        if not user_id:
            await flash("Пожалуйста, войдите в систему, чтобы оставить отзыв.", "warning")
            return redirect(url_for("main.login"))

        form = await request.form
        rating = int(form.get("rating"))
        comment = form.get("comment")

        if rating < 1 or rating > 5:
            await flash("Оценка должна быть от 1 до 5.", "warning")
            return redirect(url_for("main.product_page", product_id=product_id))

        if not comment:
            await flash("Комментарий не может быть пустым.", "warning")
            return redirect(url_for("main.product_page", product_id=product_id))

        try:
            await add_review(current_app.db_pool, product_id, user_id, rating, comment)
            await flash("Ваш отзыв успешно добавлен.", "success")
        except Exception as e:
            logger.error(f"Ошибка при добавлении отзыва: {e}")
            await flash("Ошибка при добавлении отзыва.", "danger")

        return redirect(url_for("main.product_page", product_id=product_id))

    try:
        #product = await get_product_by_id(current_app.db_pool, product_id)
        product = await get_or_cache_json(
            f"cache:product:{product_id}",
            lambda: get_product_by_id(current_app.db_pool, product_id),
            ttl=600
        )
        if not product:
            await flash("Товар не найден.", "danger")
            return redirect(url_for("main.home"))

        reviews = await get_reviews_by_product_id(current_app.db_pool, product_id)
        return await render_template("product.html", product=product, reviews=reviews)
    except Exception as e:
        logger.error(f"Ошибка при загрузке страницы товара: {e}")
        await flash("Произошла ошибка при загрузке страницы товара.", "danger")
        return redirect(url_for("main.home"))

@main.route("/demo_cache_only")
async def demo_cache_only():
    """
    Демонстрация работы кеша без доступа к PostgreSQL.
    Открывает данные только из Redis.
    """
    try:
        # Забираем категории и производителей из кеша
        categories = await get_or_cache_json("cache:categories", lambda: [])
        manufacturers = await get_or_cache_json("cache:manufacturers", lambda: [])

        # Пример продукта — заранее прогретый
        hardcoded_product_id = "94ab27f1-ea29-4127-82a7-d3aa53338e8d"
        product = await get_or_cache_json(
            f"cache:product:{hardcoded_product_id}",
            lambda: {},
            ttl=600
        )

        return await render_template(
            "demo_cache.html",
            categories=categories,
            manufacturers=manufacturers,
            product=product
        )
    except Exception as e:
        return f"Ошибка (скорее всего Redis недоступен): {e}", 500

@main.route("/debug/session_log")
async def session_log():
    user_id = session.get("user_id")
    if not user_id:
        return "Not authorized", 401

    r = await get_redis()
    logs = await r.lrange(f"session_log:{user_id}", 0, -1)
    parsed_logs = [json.loads(entry) for entry in logs]

    return await render_template("session_log.html", logs=parsed_logs)