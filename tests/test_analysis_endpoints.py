import pytest
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
@patch("api.endpoints.analysis.analyze_blocks.delay")
async def test_start_block_analysis_valid(mock_delay, client):
    mock_task = MagicMock()
    mock_task.id = "123"
    mock_delay.return_value = mock_task

    response = await client.post("/analysis/blocks", json={"depth_blocks": 10})
    assert response.status_code == 200
    assert response.json()["task_id"] == "123"

@pytest.mark.asyncio
async def test_start_block_analysis_invalid(client):
    response = await client.post("/analysis/blocks", json={"depth_blocks": 0})
    assert response.status_code == 200
    assert "error" in response.json()

@pytest.mark.asyncio
@patch("api.endpoints.analysis.analyze_block_range.delay")
async def test_start_block_range_analysis_valid(mock_delay, client):
    mock_task = MagicMock()
    mock_task.id = "456"
    mock_delay.return_value = mock_task

    response = await client.post("/analysis/block-range", json={"start_block": 1, "end_block": 100})
    assert response.status_code == 200
    assert response.json()["task_id"] == "456"

@pytest.mark.asyncio
async def test_start_block_range_analysis_invalid(client):
    response = await client.post("/analysis/block-range", json={"start_block": 100, "end_block": 1})
    assert response.status_code == 200
    assert "error" in response.json()
