# api/endpoints/data.py

import sys
import os
from typing import Optional, Dict, Any

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from redis.asyncio import Redis

from analyzer_transactions.db_worker import DatabaseWorker
from tasks.data_tasks import fetch_data
from config.settings import REDIS_URL

router = APIRouter()


class DataRequest(BaseModel):
    """
    Schema for data request. Currently used as a placeholder for future POST/PUT usage.
    """
    tx_hash: Optional[str] = None


@router.get("/transaction/{tx_hash}")
async def get_transaction(tx_hash: str) -> Dict[str, Any]:
    """
    Retrieve transaction data by transaction hash.

    Input:
        - tx_hash (str): Transaction hash to look up.

    Output:
        - If transaction exists:
            {
                "status": "completed",
                "transaction": { ... }  # Transaction data
            }
        - If not found:
            HTTP 404 error with detail "Transaction not found or not yet processed"
    """
    db_worker = DatabaseWorker()
    redis: Redis = Redis.from_url(REDIS_URL)

    # Fetch transaction data from Redis or DB
    transactions = await db_worker.fetch_transactions(redis, tx_hash)

    await redis.close()

    if not transactions:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found or not yet processed"
        )

    return {
        "status": "completed",
        "transaction": transactions[0]
    }
