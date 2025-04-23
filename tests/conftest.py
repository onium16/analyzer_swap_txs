# tests/conftest.py

import pytest_asyncio
from httpx._transports.asgi import ASGITransport
from httpx import AsyncClient
from fastapi.testclient import TestClient
from fastapi import FastAPI

from api.endpoints import analysis, data, tasks

app = FastAPI()
app.include_router(analysis.router, prefix="/analysis")
app.include_router(data.router, prefix="/data")
app.include_router(tasks.router, prefix="/tasks")

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac