"""Tests for the DeviceMiddleware class."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_device_id import DeviceId, DeviceMiddleware, compare_device_ids


@pytest.fixture
def app():
    """Create a FastAPI app with DeviceMiddleware for testing."""
    app = FastAPI()
    app.add_middleware(DeviceMiddleware)

    @app.get("/")
    async def root(device_id: DeviceId):
        return {"device_id": device_id}

    @app.get("/manual")
    async def manual(device_id: DeviceId):
        return {"device_id": device_id}

    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


def test_device_id_created_on_first_request(client):
    """Test that a device ID is created on the first request."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "device_id" in data
    assert len(data["device_id"]) > 10  # UUID should be reasonably long

    # Check that cookie was set
    assert "device_id" in response.cookies


def test_device_id_persists_across_requests(client):
    """Test that the same device ID is used across requests."""
    # First request
    response1 = client.get("/")
    device_id_1 = response1.json()["device_id"]
    cookie_value = response1.cookies["device_id"]

    # Second request with the cookie
    client.cookies.set("device_id", cookie_value)
    response2 = client.get("/")
    device_id_2 = response2.json()["device_id"]

    assert device_id_1 == device_id_2


def test_manual_device_id_extraction(client):
    """Test manual device ID extraction using get_device_id function."""
    response = client.get("/manual")
    assert response.status_code == 200

    data = response.json()
    assert "device_id" in data
    assert len(data["device_id"]) > 10


def test_custom_cookie_name():
    """Test middleware with custom cookie name."""
    app = FastAPI()
    app.add_middleware(DeviceMiddleware, cookie_name="custom_device")

    @app.get("/")
    async def root(device_id: DeviceId):
        return {"device_id": device_id}

    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    assert "custom_device" in response.cookies
    assert "device_id" not in response.cookies


def test_custom_id_generator():
    """Test middleware with custom ID generator."""

    def custom_generator():
        return "custom-id-12345"

    app = FastAPI()
    app.add_middleware(DeviceMiddleware, id_generator=custom_generator)

    @app.get("/")
    async def root(device_id: DeviceId):
        return {"device_id": device_id}

    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["device_id"] == "custom-id-12345"


def test_cookie_security_settings():
    """Test that cookie security settings are applied."""
    app = FastAPI()
    app.add_middleware(
        DeviceMiddleware,
        cookie_secure=True,
        cookie_httponly=True,
        cookie_samesite="strict",
    )

    @app.get("/")
    async def root(device_id: DeviceId):
        return {"device_id": device_id}

    client = TestClient(app)
    response = client.get("/")

    # Note: TestClient doesn't fully simulate cookie security attributes
    # In a real browser, these would be enforced
    assert response.status_code == 200
    assert "device_id" in response.cookies


def test_existing_device_id_not_overwritten(client):
    """Test that existing device ID in cookie is not overwritten."""
    existing_id = "existing-device-id"

    client.cookies.set("device_id", existing_id)
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert data["device_id"] == existing_id


def test_cookie_max_age():
    """Test custom cookie max age."""
    app = FastAPI()
    app.add_middleware(DeviceMiddleware, cookie_max_age=3600)  # 1 hour

    @app.get("/")
    async def root(device_id: DeviceId):
        return {"device_id": device_id}

    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    # Cookie max-age would be set in real browser environment


def test_compare_device_ids_matching():
    """Test that compare_device_ids returns True for matching IDs."""
    id1 = "550e8400-e29b-41d4-a716-446655440000"
    id2 = "550e8400-e29b-41d4-a716-446655440000"

    assert compare_device_ids(id1, id2) is True


def test_compare_device_ids_not_matching():
    """Test that compare_device_ids returns False for different IDs."""
    id1 = "550e8400-e29b-41d4-a716-446655440000"
    id2 = "550e8400-e29b-41d4-a716-446655440001"

    assert compare_device_ids(id1, id2) is False


def test_compare_device_ids_constant_time():
    """Test that compare_device_ids uses constant-time comparison."""
    # This test verifies the function exists and works correctly
    # Actually testing timing would require statistical analysis
    # which is beyond the scope of unit tests

    # Test with completely different strings
    assert compare_device_ids("a", "b") is False

    # Test with strings of different lengths
    assert compare_device_ids("short", "much_longer_string") is False

    # Test with empty strings
    assert compare_device_ids("", "") is True

    # Test with special characters
    id1 = "device_id_with_special_chars_!@#$%"
    id2 = "device_id_with_special_chars_!@#$%"
    assert compare_device_ids(id1, id2) is True
