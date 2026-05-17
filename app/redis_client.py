# switched to async redis client
import redis.asyncio as aioredis
from app.config import settings

# using async-compatible redis
r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
