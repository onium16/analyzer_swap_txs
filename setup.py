from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="analyzer_swap_txs",
    version="0.1.0",
    author="SeriouS",
    author_email="onium16@gmail.com",
    description="Multiservice solution for transaction analysis.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/onium16/analyzer_swap_txs",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3 :: Only",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Blockchain :: Transaction Analysis",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "redis==5.2.1",  # Заменил aioredis на redis для асинхронной работы
        "web3==7.10.0",
        "requests==2.32.3",
        "fastapi==0.115.12",
        "celery==5.5.1",
        "asyncpg==0.30.0",
        "loguru==0.7.3",
        "uvicorn==0.34.2",
        "SQLAlchemy==2.0.40",
        "python-dotenv==1.0.0",  # Обновил до последней версии
        "flower==2.0.1",
        "httpx==0.28.1",
    ],
    extras_require={
        "dev": [
            "pytest==8.2.2",
            "pytest-asyncio==0.21.0",
            "pytest-cov==5.0.0",  # Для покрытия кода
            "black==24.8.0",  # Для форматирования кода
            "flake8==7.1.1",  # Для линтинга
            "pytest-mock==3.14.0",  # Для моков в тестах
        ],
    },
    python_requires=">=3.9",
    license="MIT",
)