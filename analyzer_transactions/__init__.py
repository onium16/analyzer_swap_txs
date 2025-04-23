# analyzer_transactions/__init__.py

from loguru import logger
import sys
import os

# Импорты внутренних модулей
from analyzer_transactions.analyzer import AnalyzerTransactions

# Экспортируемые объекты
__all__ = ["AnalyzerTransactions", "logger"]

# Настройка логгера
LOG_PATH = os.getenv("LOG_PATH", "logs/log_analyzer.log")

# Добавляем вывод в файл
logger.add(
    sink=LOG_PATH,
    format="{time} :: {level} :: {file} :: {name} :: {line} :: {message}",
    rotation="1 MB",
    retention="5 days",
    compression="zip",
    level="DEBUG",
    encoding="utf-8",
    enqueue=True
)