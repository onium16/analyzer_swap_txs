# api/endpoints/data.py

import sys
import os

from analyzer_transactions.db_worker import DatabaseWorker
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi import APIRouter
from fastapi import HTTPException
from tasks.data_tasks import fetch_data
from pydantic import BaseModel
from config.settings import REDIS_URL
from redis.asyncio import Redis

router = APIRouter()

class DataRequest(BaseModel):
    tx_hash: str = None

@router.get("/transaction/{tx_hash}")
async def get_transaction(tx_hash: str):
    """Получает данные транзакции по хэшу."""
    db_worker = DatabaseWorker()
    redis = Redis.from_url(REDIS_URL)
    
    transactions = await db_worker.fetch_transactions(redis, tx_hash)
    if not transactions:
        raise HTTPException(status_code=404, detail="Transaction not found or not yet processed")
    
    return {"status": "completed", "transaction": transactions[0]}

