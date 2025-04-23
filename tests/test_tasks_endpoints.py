# tests/test_tasks_endpoints.py
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from api.endpoints import tasks
from unittest.mock import patch
import redis 

app = FastAPI()
app.include_router(tasks.router)

@patch("api.endpoints.tasks.redis_client")
@patch("api.endpoints.tasks.AsyncResult")
def test_get_task_status_completed_success(mock_async_result, mock_redis):
    mock_instance = mock_async_result.return_value
    mock_instance.ready.return_value = True
    mock_instance.successful.return_value = True
    mock_instance.result = {"message": "done"}

    client = TestClient(app)
    response = client.get("/status/test-task-id")

    assert response.status_code == 200
    assert response.json() == {
        "task_id": "test-task-id",
        "status": "completed",
        "result": {"message": "done"}
    }

@patch("api.endpoints.tasks.redis_client")
@patch("api.endpoints.tasks.AsyncResult")
def test_get_task_status_failed(mock_async_result, mock_redis):
    mock_instance = mock_async_result.return_value
    mock_instance.ready.return_value = True
    mock_instance.successful.return_value = False
    mock_instance.get.return_value = "Task error happened"

    client = TestClient(app)
    response = client.get("/status/test-task-id")

    assert response.status_code == 200
    assert response.json() == {
        "task_id": "test-task-id",
        "status": "failed",
        "error": "Task error happened"
    }

@patch("api.endpoints.tasks.redis_client")
@patch("api.endpoints.tasks.AsyncResult")
def test_get_task_status_processing(mock_async_result, mock_redis):
    mock_instance = mock_async_result.return_value
    mock_instance.ready.return_value = False

    client = TestClient(app)
    response = client.get("/status/test-task-id")

    assert response.status_code == 200
    assert response.json() == {
        "task_id": "test-task-id",
        "status": "processing"
    }


@patch("api.endpoints.tasks.redis_client")
def test_health_check_success(mock_redis):
    mock_redis.ping.return_value = True

    client = TestClient(app)
    response = client.get("/health_redis")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "redis": "connected"
    }


@patch("api.endpoints.tasks.redis_client")
def test_get_all_tasks_redis_error(mock_redis):
    mock_redis.keys.side_effect = redis.RedisError("Redis is down")

    client = TestClient(app)
    response = client.get("/all")

    assert response.status_code == 503
    assert "Redis error" in response.json()["detail"]

@patch("api.endpoints.tasks.redis_client")
def test_health_check_redis_unavailable(mock_redis):
    mock_redis.ping.side_effect = Exception("Redis ping failed")

    client = TestClient(app)
    response = client.get("/health_redis")

    assert response.status_code == 503
    assert "Unexpected error: Redis ping failed" in response.json()["detail"]

@patch("api.endpoints.tasks.AsyncResult")
def test_get_task_status_failed_with_exception(mock_async_result):
    mock_instance = mock_async_result.return_value
    mock_instance.ready.return_value = True
    mock_instance.successful.return_value = False
    mock_instance.get.side_effect = Exception("Database read error")

    client = TestClient(app)
    response = client.get("/status/test-task-id")

    assert response.status_code == 200
    assert response.json() == {
        "task_id": "test-task-id",
        "status": "failed",
        "error": "Database read error"
    }