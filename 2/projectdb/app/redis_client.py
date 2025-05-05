import redis.asyncio as redis_lib
import os

redis = None

async def init_redis():
    global redis
    redis = redis_lib.from_url(
        os.getenv("REDIS_URL", "redis://localhost"),
        decode_responses=True
    )

async def get_redis():
    return redis