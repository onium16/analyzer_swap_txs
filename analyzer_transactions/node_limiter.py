# analyzer_transactions/node_limiter.py

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
import redis.asyncio as aioredis
import json
import logging
from typing import List, Dict
from analyzer_transactions import logger

class NodeRateLimiter:
    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url)
        self.redis_url = redis_url

    async def initialize_nodes(self, initial_config: List[Dict] = None):
        """Инициализация конфигурации нод в Redis."""
        if initial_config:
            await self.redis.set("nodes:config", json.dumps(initial_config))
            logger.info("Initialized node config in Redis")
        else:
            config = await self.redis.get("nodes:config")
            if not config:
                raise ValueError("No node configuration found in Redis")

    async def get_node_config(self) -> List[Dict]:
        """Получение конфигурации нод из Redis."""
        config = await self.redis.get("nodes:config")
        if not config:
            raise ValueError("Node configuration not found in Redis")
        return json.loads(config)

    async def update_node_config(self, node_url: str, per_second: int = None, per_day: int = None):
        """Обновление параметров ноды в Redis."""
        config = await self.get_node_config()
        for node in config:
            if node["url"] == node_url:
                if per_second is not None:
                    node["per_second"] = per_second
                if per_day is not None:
                    node["per_day"] = per_day
                break
        await self.redis.set("nodes:config", json.dumps(config))
        logger.info(f"Updated node config for {node_url}")

    def _node_key(self, node_id: str, period: int) -> str:
        return f"node:{node_id}:{period}"

    async def _increment_and_check(self, node_id: str, max_count: int, period_sec: int) -> bool:
        """Увеличение счетчика запросов и проверка лимита."""
        if max_count == 0:
            return True
        key = self._node_key(node_id, period_sec)
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, period_sec)
        count, _ = await pipe.execute()
        logger.debug(f"Node {node_id}: {count}/{max_count} requests for period {period_sec}s")
        return count <= max_count

    async def get_available_node(self, max_attempts: int = 3) -> str:
        """Выбор доступной ноды."""
        logger.debug(f"Selected node: ")
        for attempt in range(max_attempts):
            config = await self.get_node_config()
            for node in config:
                node_id = node["url"]
                allowed_sec = await self._increment_and_check(node_id, node["per_second"], 1)
                allowed_day = await self._increment_and_check(node_id, node["per_day"], 86400)
                if allowed_sec and allowed_day:
                    logger.debug(f"Selected node: {node_id}")
                    return node_id
            await asyncio.sleep(0.5)
        raise Exception("No available nodes after max attempts")
    

if __name__ == "__main__":
    node_limiter = NodeRateLimiter("redis://localhost:6380/0")
    asyncio.run(node_limiter.get_available_node())