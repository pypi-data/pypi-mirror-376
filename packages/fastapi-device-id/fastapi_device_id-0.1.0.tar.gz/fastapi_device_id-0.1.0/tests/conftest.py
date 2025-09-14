"""Pytest configuration and shared fixtures."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_device_id import DeviceId, DeviceMiddleware


@pytest.fixture
def basic_app():
    """Create a basic FastAPI app with DeviceMiddleware."""
    app = FastAPI()
    app.add_middleware(DeviceMiddleware)

    @app.get("/test")
    async def test_endpoint(device_id: DeviceId):
        return {"device_id": device_id, "status": "ok"}

    return app


@pytest.fixture
def basic_client(basic_app):
    """Create a test client with basic app."""
    return TestClient(basic_app)
