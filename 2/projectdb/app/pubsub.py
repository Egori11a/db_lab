import asyncio
import json
from app.redis_client import get_redis
import logging

logger = logging.getLogger(__name__)

async def publish_event(channel: str, message: dict):
    """
    Публикует событие в указанный Redis-канал.
    """
    r = await get_redis()
    await r.publish(channel, json.dumps(message))

async def listen_to_orders():
    """
    Подписывается на Redis-канал и обрабатывает входящие сообщения.
    Эта функция запускается при старте приложения.
    Все события будут здесь ловиться.
    Логируется информация о заказах.
    """
    r = await get_redis()
    pubsub = r.pubsub()
    await pubsub.subscribe("orders")

    logger.info("🔔 Подписка на канал 'orders' запущена")

    async for msg in pubsub.listen():
        if msg['type'] == 'message':
            try:
                data = json.loads(msg['data'])
                logger.info(f"📨 Получено событие: {data}")
            except Exception as e:
                logger.error(f"Ошибка при обработке события: {e}")
