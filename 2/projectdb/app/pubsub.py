import asyncio
import json
from app.redis_client import get_redis
import logging

logger = logging.getLogger(__name__)

async def publish_event(channel: str, message: dict):
    r = await get_redis()
    await r.publish(channel, json.dumps(message))

async def listen_to_orders():
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