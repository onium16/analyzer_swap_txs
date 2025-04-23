# config/node_config.py

import os

initial_node_config = [
    {"url": "https://rpc.flashbots.net", "per_second": 10, "per_day": 1000},
    {"url": "http://192.168.0.10:8545", "per_second": 0, "per_day": 0},
    ]
redis_url = os.getenv("REDIS_URL", "redis://localhost:6380/0")