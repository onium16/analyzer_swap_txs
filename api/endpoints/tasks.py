# api/endpoints/tasks.py
import json
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from celery.result import AsyncResult
from tasks.analyzer_tasks import analyze_blocks
import redis
import os

router = APIRouter()
redis_client = redis.StrictRedis(
    host=os.getenv('REDIS_HOST', 'redis'),  # Default to 'redis' for Docker
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=int(os.getenv('REDIS_DB', 0)),
    decode_responses=False  # Automatically decode Redis responses to strings
)

class TaskRequest(BaseModel):
    data: dict

@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    task_result = AsyncResult(task_id)
    if task_result.ready():
        if task_result.successful():
            return {
                "task_id": task_id,
                "status": "completed",
                "result": task_result.result
            }
        else:
            try:
                error_msg = str(task_result.get(propagate=False))
            except Exception as e:
                error_msg = str(e)
            return {
                "task_id": task_id,
                "status": "failed",
                "error": error_msg
            }
    return {"task_id": task_id, "status": "processing"}

@router.get("/all")
async def get_tasks(
                start: int = Query(0, ge=0, description="The index to start from"),
                end: int = Query(100, gt=0, le=1000, description="The index to end at (exclusive)")
                ):
    tasks_info = []
    try:
        celery_keys: list = redis_client.keys('celery-task-meta-*')
        selected_keys = celery_keys[start:end]
        for key in selected_keys:
            try:
                task_id = str(key)[1:-1].split('celery-task-meta-')[1]
                task_result = AsyncResult(task_id)
                tasks_info.append({
                    "task_id": task_id,
                    "state": task_result.status
                })
                if task_result.status == 'SUCCESS':
                    tasks_info[-1]["status"] = str(task_result.status)
                    tasks_info[-1]["result"] = str(task_result.result)
                elif task_result.status == 'FAILURE':
                    tasks_info[-1]["error"] = str(task_result.get(propagate=False))

            except Exception as task_error:
                tasks_info.append({"task_id": task_id, "error": str(task_error)})
    except redis.RedisError as e:
        raise HTTPException(status_code=503, detail=f"Redis error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Unexpected error: {str(e)}")
    
    return {"tasks": tasks_info}

@router.get("/health_redis")
async def health_check():
    try:
        redis_client.ping()
        return {"status": "healthy", "redis": "connected"}
    except redis.RedisError as e:
        raise HTTPException(status_code=503, detail=f"Redis unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Unexpected error: {str(e)}") 