# api/endpoints/example.py

from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis
from api.dependencies import get_redis

router = APIRouter()

@router.get("/example-redis")
async def example_redis_usage(redis: Redis = Depends(get_redis)):
    """
    Example endpoint that checks Redis connection.
    
    Args:
        redis (Redis): Injected Redis connection via Depends.
    
    Returns:
        dict: Simple response showing Redis connection status.
    """
    try:
        pong = await redis.ping()
        return {"redis_status": "connected" if pong else "not responding"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis error: {str(e)}")
