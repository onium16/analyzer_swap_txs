# tasks/data_tasks.py

import sys
import os
import asyncio
import logging
from typing import Optional, List, Dict

from celery import Celery
from analyzer_transactions.db_worker import DatabaseWorker
from config.settings import REDIS_URL
from redis.asyncio import Redis

# Add parent directory to system path to enable module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure logging
logger = logging.getLogger(__name__)

# Create and configure Celery app
app = Celery('analyzer')
app.config_from_object('tasks.celery_config')

@app.task(bind=True, max_retries=3)
def fetch_data(self, tx_hash: Optional[str] = None) -> List[Dict]:
    """
    Celery task that asynchronously fetches transaction data from the database using a given transaction hash.

    Args:
        self: Reference to the task instance, required for retry mechanism.
        tx_hash (Optional[str]): Transaction hash to query for. If None, fetches all transactions.

    Returns:
        List[Dict]: A list of transaction records retrieved from the database.

    Raises:
        self.retry: Retries the task in case of failure, up to the max_retries limit.
    """
    try:
        async def run_fetch() -> List[Dict]:
            # Establish Redis connection
            redis = Redis.from_url(REDIS_URL)
            db_worker = DatabaseWorker()

            # Fetch data from the database
            data = await db_worker.fetch_transactions(redis, tx_hash)

            # Close Redis connection
            await redis.close()
            return data

        # Run the async function in a synchronous context
        return asyncio.run(run_fetch())
    except Exception as exc:
        logger.error(f"Task failed: {exc}")
        raise self.retry(exc=exc, countdown=60)
