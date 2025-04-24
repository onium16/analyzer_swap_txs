# config/node_config.py

import os
from typing import List, Dict, Any

# Initial configuration for Ethereum RPC nodes with rate limits
initial_node_config: List[Dict[str, Any]] = [
    {
        "url": "https://rpc.flashbots.net",
        "per_second": 10,   # Max 10 requests per second
        "per_day": 1000     # Max 1000 requests per day
    },
    {
        "url": "http://192.168.0.10:8545",
        "per_second": 0,    # Disabled or unlimited (depending on implementation)
        "per_day": 0
    }
]

# Redis connection URL, can be overridden via environment variable
redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6380/0")
