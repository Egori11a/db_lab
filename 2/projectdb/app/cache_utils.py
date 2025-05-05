import os
import json
import uuid
from app.redis_client import get_redis

DEFAULT_TTL = int(os.getenv("CACHE_TTL", 300))  # по умолчанию 5 минут

import uuid
import decimal

def make_json_serializable(obj):
    """
    Преобразует asyncpg.Record или dict с UUID/Decimal в сериализуемую структуру.
    """
    if isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]

    elif isinstance(obj, dict):
        return {
            k: (
                str(v) if isinstance(v, uuid.UUID)
                else float(v) if isinstance(v, decimal.Decimal)
                else v
            )
            for k, v in obj.items()
        }

    elif hasattr(obj, 'items'):
        return {
            k: (
                str(v) if isinstance(v, uuid.UUID)
                else float(v) if isinstance(v, decimal.Decimal)
                else v
            )
            for k, v in dict(obj).items()
        }

    elif isinstance(obj, uuid.UUID):
        return str(obj)

    elif isinstance(obj, decimal.Decimal):
        return float(obj)

    return obj

async def get_or_cache_json(key: str, fetch_fn, ttl: int = DEFAULT_TTL):
    r = await get_redis()
    cached = await r.get(key)
    if cached:
        return json.loads(cached)

    data = await fetch_fn()
    serializable_data = make_json_serializable(data)

    await r.set(key, json.dumps(serializable_data), ex=ttl)
    return serializable_data

async def invalidate_cache(key: str):
    r = await get_redis()
    await r.delete(key)
