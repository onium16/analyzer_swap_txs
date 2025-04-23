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
    ],
    install_requires=[
            "aioredis==2.0.1",
            "asyncio==3.4.3",
            "web3==7.10.0",
            "requests==2.32.3",
            "pytest==8.2.2",
            "pytest-asyncio==0.21.0",
            "fastapi==0.115.12",
            "celery==5.5.1",
            "redis==5.2.1",
            "asyncpg==0.30.0",
            "loguru==0.7.3",
            "uvicorn==0.34.2",
            "sqlalchemy==2.0.40",
            "dotenv==0.9.9",
            "setuptools==79.0.0",
            "python-dotenv==1.1.0",
            "SQLAlchemy==2.0.40",
            "flower==2.0.1",
            "httpx==0.28.1"
    ],
    extras_require={
        "dev": [
            "aioredis==2.0.1",
            "asyncio==3.4.3",
            "web3==7.10.0",
            "requests==2.32.3",
            "pytest==8.2.2",
            "pytest-asyncio==0.21.0",
            "fastapi==0.115.12",
            "celery==5.5.1",
            "redis==5.2.1",
            "asyncpg==0.30.0",
            "loguru==0.7.3",
            "uvicorn==0.34.2",
            "sqlalchemy==2.0.40",
            "dotenv==0.9.9",
            "setuptools==79.0.0",
            "python-dotenv==1.1.0",
            "SQLAlchemy==2.0.40",
            "flower==2.0.1",
            "httpx==0.28.1"
        ],
    },
    python_requires=">=3.9",
    license="MIT",
)