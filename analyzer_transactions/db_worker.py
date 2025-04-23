import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import re
from loguru import logger
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, JSON, BigInteger, text, select
from sqlalchemy.exc import OperationalError, ProgrammingError, SQLAlchemyError
from redis.asyncio import Redis
from config.settings import DATABASE_URL

Base = declarative_base()
POSTGRES_DB = os.getenv("POSTGRES_DB", "analyzer")
POSTGRES_TABLE_SWAP: str = os.getenv("POSTGRES_TABLE_SWAP", "swap_txs")

class Transaction(Base):
    __tablename__ = POSTGRES_TABLE_SWAP
    id = Column(Integer, primary_key=True)
    tx_hash = Column(String, unique=True, index=True)
    block_number = Column(BigInteger)
    decoded_input = Column(JSON)

class DatabaseWorker:
    """Class for working with PostgreSQL database."""
    def __init__(self):
        self.logger = logger
        self.DB_URI = DATABASE_URL
        self.engine = create_async_engine(self.DB_URI, pool_size=20, max_overflow=10)

    async def connect(self):
        """Test database connection."""
        async with self.engine.connect() as conn:
            self.logger.info("Connected to PostgreSQL database.")

    async def close(self):
        """Dispose of the engine."""
        await self.engine.dispose()
        self.logger.info("Database engine disposed.")

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def validate_identifier(self, name: str) -> bool:
        """Validate table or column names to prevent SQL injection."""
        return bool(re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name))

    async def create_database(self, db_name):
        """Create database if it doesn't exist."""
        db_name = db_name
        temp_uri = self.DB_URI.replace(f"/{db_name}", "/postgres")
        temp_engine = create_async_engine(temp_uri)
        try:
            async with temp_engine.connect() as conn:
                await conn.execute(text("COMMIT"))
                result = await conn.execute(text("SELECT 1 FROM pg_database WHERE datname=:db"), {"db": db_name})
                if not result.fetchone():
                    await conn.execute(text(f"CREATE DATABASE {db_name}"))
                    self.logger.info(f"Database '{db_name}' created.")
                else:
                    self.logger.info(f"Database '{db_name}' already exists.")
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to create/check database '{db_name}': {e}")
            raise
        finally:
            await temp_engine.dispose()

    async def init_db(self):
        """Initialize database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.logger.info("Database tables initialized.")

    async def check_and_create_table(self, table_name: str, columns: list[tuple], indexes: list[dict] = None):
        """Check and create table with optional indexes."""
        if not self.validate_identifier(table_name):
            raise ValueError(f"Invalid table name: {table_name}")
        async with self.engine.connect() as conn:
            result = await conn.execute(
                text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = :table_name)"),
                {"table_name": table_name}
            )
            if not result.scalar():
                columns_sql = ", ".join([f"{col[0]} {col[1]}" for col in columns])
                await conn.execute(text(f"CREATE TABLE {table_name} ({columns_sql});"))
                if indexes:
                    for idx in indexes:
                        if self.validate_identifier(idx['name']) and self.validate_identifier(idx['column']):
                            await conn.execute(text(f"CREATE INDEX {idx['name']} ON {table_name} ({idx['column']});"))
                await conn.commit()
                self.logger.info(f"Table '{table_name}' created.")
            else:
                self.logger.info(f"Table '{table_name}' already exists.")

    async def save_transactions(self, redis: Redis, tx_data_list: list[dict]):
        """Save transactions from the provided list to database."""
        async_session = sessionmaker(self.engine, class_=AsyncSession)
        async with async_session() as session:
            saved_count = 0
            for tx_data in tx_data_list:
                tx_hash = tx_data.get("tx_hash")
                if not tx_hash:
                    self.logger.warning("Transaction data missing tx_hash, skipping")
                    continue
                
                # Проверяем, не существует ли транзакция в базе данных
                existing = await session.execute(select(Transaction).filter(Transaction.tx_hash == tx_hash))
                if not existing.scalars().first():
                    transaction = Transaction(
                        tx_hash=tx_hash,
                        block_number=tx_data.get("block_number"),
                        decoded_input=tx_data.get("decoded_input")
                    )
                    session.add(transaction)
                    # Сохраняем данные в Redis (если их там нет)
                    await redis.setex(f"tx:{tx_hash}", 3600, json.dumps(tx_data))
                    # Устанавливаем флаг в Redis
                    await redis.setex(f"tx:{tx_hash}:saved_to_db", 3600, "true")
                    saved_count += 1
            await session.commit()
        self.logger.info(f"Saved {saved_count} transactions from {len(tx_data_list)} provided to table 'swap_txs'.")

    async def fetch_transactions(self, redis: Redis, tx_hash: str = None) -> list[dict]:
        """Fetch transactions from database with Redis caching."""
        if tx_hash:
            # Проверяем, сохранена ли транзакция в базе данных
            saved_to_db = await redis.get(f"tx:{tx_hash}:saved_to_db")
            if not saved_to_db:
                self.logger.debug(f"Transaction {tx_hash} not yet saved to DB")
                return []
            
            # Проверяем кэш
            cached = await redis.get(f"tx_data:{tx_hash}")
            if cached:
                self.logger.debug(f"Cache hit for {tx_hash}")
                return json.loads(cached)
        
        async_session = sessionmaker(self.engine, class_=AsyncSession)
        async with async_session() as session:
            if tx_hash:
                result = await session.execute(select(Transaction).filter(Transaction.tx_hash == tx_hash))
                data = [{"tx_hash": row.tx_hash, "block_number": row.block_number, "decoded_input": row.decoded_input} for row in result.scalars()]
            else:
                result = await session.execute(select(Transaction))
                data = [{"tx_hash": row.tx_hash, "block_number": row.block_number, "decoded_input": row.decoded_input} for row in result.scalars()]
            
            if tx_hash and data:
                await redis.setex(f"tx_data:{tx_hash}", 3600, json.dumps(data))
            return data
        
    async def get_columns_info(self, table_name: str) -> list[str]:
        """Get column names for a table."""
        if not self.validate_identifier(table_name):
            raise ValueError(f"Invalid table name: {table_name}")
        async with self.engine.connect() as conn:
            result = await conn.execute(
                text("SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = :table_name"),
                {"table_name": table_name}
            )
            return [row[0] for row in result.fetchall()]