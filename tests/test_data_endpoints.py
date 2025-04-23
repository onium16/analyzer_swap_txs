import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
@patch("api.endpoints.data.DatabaseWorker")
@patch("api.endpoints.data.Redis.from_url")
async def test_get_transaction_found(mock_redis, mock_dbworker, client):
    mock_worker = AsyncMock()
    mock_worker.fetch_transactions.return_value = [{"tx_hash": "abc123"}]
    mock_dbworker.return_value = mock_worker
    mock_redis.return_value = AsyncMock()

    # Просто вызываем клиент напрямую — он уже открыт!
    response = await client.get("/data/transaction/abc123")

    assert response.status_code == 200
    assert response.json()["status"] == "completed"


@pytest.mark.asyncio
@patch("api.endpoints.data.DatabaseWorker")
@patch("api.endpoints.data.Redis.from_url")
async def test_get_transaction_not_found(mock_redis, mock_dbworker, client):
    mock_worker = AsyncMock()
    mock_worker.fetch_transactions.return_value = []
    mock_dbworker.return_value = mock_worker
    mock_redis.return_value = AsyncMock()

    response = await client.get("/data/transaction/notfound")
    print("RESPONSE:", response.status_code, response.json())

    assert response.status_code == 404
