# tasks/celery_config.py

import sys
import os
from typing import List, Dict, Any, Optional, AsyncGenerator
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.settings import REDIS_URL
from kombu import Queue, Exchange

broker_url = REDIS_URL
result_backend = REDIS_URL
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True
task_default_queue = 'default'
task_track_started = True

# Настройки очереди
task_queues = (
    Queue('default', Exchange('default'), routing_key='default'),
    Queue('high_priority', Exchange('high_priority'), routing_key='high_priority')
)