# tasks/data_tasks.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from celery import Celery
from analyzer_transactions.db_worker import DatabaseWorker
from config.settings import REDIS_URL
from redis.asyncio import Redis
import logging

logger = logging.getLogger(__name__)
app = Celery('analyzer')
app.config_from_object('tasks.celery_config')

@app.task(bind=True, max_retries=3)
def fetch_data(self, tx_hash: str = None) -> list[dict]:
    try:
        async def run_fetch():
            
            redis = Redis.from_url(REDIS_URL)
            db_worker = DatabaseWorker()
            data = await db_worker.fetch_transactions(redis, tx_hash)
            await redis.close()
            return data
        
        return asyncio.run(run_fetch())
    except Exception as exc:
        logger.error(f"Задача не выполнена: {exc}")
        raise self.retry(exc=exc, countdown=60)