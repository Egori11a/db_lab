-- Лабораторная 1.2: Транзакции в PostgreSQL
-- Примеры транзакций с использованием реальных данных

-- Пример 1: Обычная транзакция — добавление товара в корзину и оформление заказа
BEGIN;

-- Добавим товар в корзину пользователя
INSERT INTO cart (user_id, product_id, quantity)
VALUES ('867e5f02-ba17-4f06-8b7e-f0f464bfa3dc', '8149336b-96c9-4d36-9763-5f02900d2d20', 2)
ON CONFLICT (user_id, product_id) DO UPDATE SET quantity = cart.quantity + 2;

-- Создание нового заказа
INSERT INTO orders (order_id, user_id, total_cost, status)
VALUES (
    uuid_generate_v4(),
    '867e5f02-ba17-4f06-8b7e-f0f464bfa3dc',
    199.98,
    'Pending'
);

COMMIT;

-- Пример 2: Транзакция с ошибкой — проверка отката
BEGIN;

-- Попытка вставки отзыва с недопустимым рейтингом (ошибка)
INSERT INTO reviews (review_id, product_id, user_id, rating, comment)
VALUES (
    uuid_generate_v4(),
    '8149336b-96c9-4d36-9763-5f02900d2d20',
    '867e5f02-ba17-4f06-8b7e-f0f464bfa3dc',
    10,  -- Ошибка: рейтинг должен быть от 1 до 5
    'Excellent product!'
);

-- Эта строка не выполнится из-за ошибки выше
INSERT INTO cart (user_id, product_id, quantity)
VALUES ('867e5f02-ba17-4f06-8b7e-f0f464bfa3dc', '8149336b-96c9-4d36-9763-5f02900d2d20', 1);

ROLLBACK;

-- Пример 3: Транзакция с уровнем изоляции REPEATABLE READ
BEGIN ISOLATION LEVEL REPEATABLE READ;

-- Чтение текущего остатка товара
SELECT stock FROM products WHERE product_id = '8149336b-96c9-4d36-9763-5f02900d2d20';

-- Списание товара со склада
UPDATE products
SET stock = stock - 1
WHERE product_id = '8149336b-96c9-4d36-9763-5f02900d2d20';

COMMIT;

-- Пример 4: Оформление заказа с уровнем изоляции READ COMMITTED
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;

BEGIN;

-- Предположим: пользователь хочет купить 2 шт. товара
-- Указываем ID вручную или подставим из приложения

-- Проверка остатков товара
SELECT stock FROM products WHERE product_id = '8149336b-96c9-4d36-9763-5f02900d2d20' FOR UPDATE;

-- Проверка, что товара достаточно
UPDATE products
SET stock = stock - 2
WHERE product_id = '8149336b-96c9-4d36-9763-5f02900d2d20';

-- Создаем заказ
INSERT INTO orders (order_id, user_id, total_cost, status)
VALUES (
    uuid_generate_v4(),
    '867e5f02-ba17-4f06-8b7e-f0f464bfa3dc',
    199.98,
    'Pending'
);

COMMIT;