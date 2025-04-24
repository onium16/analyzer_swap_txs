# config/settings.py

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from a .env file (if present)
load_dotenv()

# Redis connection URL (default: localhost on non-standard port 6380, DB 0)
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6380/0")

# Database connection URL (must be defined in the environment or .env file)
DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")

# Logging level (default: INFO)
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
