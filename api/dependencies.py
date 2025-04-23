# api/dependencies.py
from redis.asyncio import Redis
from config.settings import REDIS_URL

async def get_redis():
    redis = Redis.from_url(REDIS_URL)
    try:
        yield redis
    finally:
        await redis.close()