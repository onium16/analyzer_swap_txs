# tasks/analyzer_tasks.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from celery import Celery, shared_task
from analyzer_transactions.analyzer import AnalyzerTransactions, analyzer_main, analyzer_slice_main
from analyzer_transactions.db_worker import DatabaseWorker
from config.settings import REDIS_URL
from redis.asyncio import Redis
import asyncio
from typing import Dict, Any
from loguru import logger


# Настройка Celery
app = Celery('analyzer', broker=REDIS_URL, backend=REDIS_URL)
app.config_from_object('tasks.celery_config')

@shared_task(bind=True, max_retries=3)
def save_transactions_to_db(self, tx_data_list: list[dict]):
    """Асинхронное сохранение транзакций в базу данных."""
    try:
        # Создаём новый событийный цикл для задачи
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        db_worker = DatabaseWorker()
        redis = Redis.from_url(REDIS_URL)
        loop.run_until_complete(db_worker.save_transactions(redis, tx_data_list))
        logger.info(f"Saved {len(tx_data_list)} transactions to database via save_transactions_to_db")
    except Exception as exc:
        logger.error(f"Error saving transactions: {exc}")
        raise self.retry(exc=exc, countdown=60)
    finally:
        if not loop.is_closed():
            loop.close()

@shared_task(bind=True, max_retries=3)
def analyze_blocks(self, depth_blocks: int = 3) -> Dict[str, Any]:
    """Анализ последних блоков с асинхронным сохранением транзакций."""
    try:
        # Создаём новый событийный цикл
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Выполняем анализ транзакций
        transactions = loop.run_until_complete(analyzer_main(depth_blocks))
        
        # Извлекаем хэши и данные транзакций
        tx_data_list = [
            {
                "tx_hash": "0x" + tx["hash"].hex() if isinstance(tx["hash"], bytes) else tx["hash"],
                "block_number": tx.get("blockNumber"),
                "decoded_input": tx.get("decoded_input")
            }
            for tx in transactions if isinstance(tx, dict) and "hash" in tx
        ]
        
        # Проверяем и создаём таблицу
        db_worker = DatabaseWorker()
        POSTGRES_DB = os.getenv("POSTGRES_DB", "analyser")

        loop.run_until_complete(db_worker.create_database(
                                                        POSTGRES_DB,
                                                    ))
        POSTGRES_TABLE_SWAP = os.getenv("POSTGRES_TABLE_SWAP", "swap_txs")
        POSTGRES_COLUMNS_SWAP = [
            ("id", "SERIAL PRIMARY KEY"),
            ("tx_hash", "VARCHAR UNIQUE"),
            ("block_number", "BIGINT"),
            ("decoded_input", "JSONB")
        ]
        POSTGRES_INDEXES_SWAP = [
            {"name": "idx_tx_hash", "column": "tx_hash"},
            {"name": "idx_block_number", "column": "block_number"}
        ]

        loop.run_until_complete(db_worker.check_and_create_table(
            POSTGRES_TABLE_SWAP,
            columns=POSTGRES_COLUMNS_SWAP,
            indexes=POSTGRES_INDEXES_SWAP
        ))

        # Запускаем асинхронное сохранение транзакций
        save_task = save_transactions_to_db.delay(tx_data_list)
        
        # Возвращаем хэши транзакций и ID задачи сохранения
        tx_hashes = [tx["tx_hash"] for tx in tx_data_list]
        return {
            "status": "completed",
            "tx_hashes": tx_hashes,
            "count": len(tx_hashes),
            "save_task_id": save_task.id
        }
    except Exception as exc:
        logger.error(f"Error in analyze_blocks: {exc}")
        raise self.retry(exc=exc, countdown=60)
    finally:
        if not loop.is_closed():
            loop.close()

@shared_task(bind=True, max_retries=3)
def analyze_block_range(self, start_block: int, end_block: int) -> Dict[str, Any]:
    """Анализ транзакций в диапазоне блоков с сохранением в REDIS."""
    try:
        # Создаём новый событийный цикл
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Выполняем анализ транзакций
        transactions = loop.run_until_complete(analyzer_slice_main(start_block, end_block))
        
        # Извлекаем хэши и данные транзакций
        tx_data_list = [
            {
                "tx_hash": "0x" + tx["hash"].hex() if isinstance(tx["hash"], bytes) else tx["hash"],
                "block_number": tx.get("blockNumber"),
                "decoded_input": tx.get("decoded_input")
            }
            for tx in transactions if isinstance(tx, dict) and "hash" in tx
        ]
        
        # Проверяем и создаём таблицу
        db_worker = DatabaseWorker()
        POSTGRES_TABLE_SWAP = os.getenv("POSTGRES_TABLE_SWAP", "swap_txs")
        POSTGRES_COLUMNS_SWAP = [
            ("id", "SERIAL PRIMARY KEY"),
            ("tx_hash", "VARCHAR UNIQUE"),
            ("block_number", "BIGINT"),
            ("decoded_input", "JSONB")
        ]
        POSTGRES_INDEXES_SWAP = [
            {"name": "idx_tx_hash", "column": "tx_hash"},
            {"name": "idx_block_number", "column": "block_number"}
        ]

        loop.run_until_complete(db_worker.check_and_create_table(
            POSTGRES_TABLE_SWAP,
            columns=POSTGRES_COLUMNS_SWAP,
            indexes=POSTGRES_INDEXES_SWAP
        ))

        # Запускаем асинхронное сохранение транзакций
        save_task = save_transactions_to_db.delay(tx_data_list)
        
        # Возвращаем хэши транзакций и ID задачи сохранения
        tx_hashes = [tx["tx_hash"] for tx in tx_data_list]
        return {
            "status": "completed",
            "tx_hashes": tx_hashes,
            "count": len(tx_hashes),
            "save_task_id": save_task.id
        }
    except Exception as exc:
        logger.error(f"Error in analyze_blocks: {exc}")
        raise self.retry(exc=exc, countdown=60)
    finally:
        if not loop.is_closed():
            loop.close()
