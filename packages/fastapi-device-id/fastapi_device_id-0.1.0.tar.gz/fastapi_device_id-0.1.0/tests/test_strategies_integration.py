"""Integration tests for security strategies with DeviceMiddleware.

These tests verify that strategies work correctly when integrated with the middleware,
following TDD principles for integration testing.
Tests focus on end-to-end behavior through the HTTP interface.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_device_id import (
    DeviceId,
    DeviceMiddleware,
    EncryptedStrategy,
    JWTStrategy,
    PlaintextStrategy,
)


class TestStrategyIntegrationWithMiddleware:
    """Integration tests verifying strategies work with DeviceMiddleware."""

    @pytest.fixture
    def plaintext_app(self):
        """FastAPI app with PlaintextStrategy middleware."""
        app = FastAPI()
        app.add_middleware(DeviceMiddleware, security_strategy=PlaintextStrategy())

        @app.get("/")
        async def root(device_id: DeviceId):
            return {"device_id": device_id}

        return app

    @pytest.fixture
    def jwt_app(self):
        """FastAPI app with JWTStrategy middleware."""
        app = FastAPI()
        app.add_middleware(
            DeviceMiddleware, security_strategy=JWTStrategy("integration-test-secret")
        )

        @app.get("/")
        async def root(device_id: DeviceId):
            return {"device_id": device_id}

        @app.get("/profile")
        async def profile(device_id: DeviceId):
            return {"device_id": device_id, "profile": "user_profile"}

        return app

    @pytest.fixture
    def encrypted_app(self):
        """FastAPI app with EncryptedStrategy middleware."""
        app = FastAPI()
        app.add_middleware(
            DeviceMiddleware,
            security_strategy=EncryptedStrategy("integration-test-key"),
        )

        @app.get("/")
        async def root(device_id: DeviceId):
            return {"device_id": device_id}

        return app

    def test_plaintext_strategy_creates_readable_cookie(self, plaintext_app):
        """Given PlaintextStrategy middleware
        When making a request
        Then cookie should contain readable device ID"""
        # Given
        client = TestClient(plaintext_app)

        # When
        response = client.get("/")

        # Then
        assert response.status_code == 200
        data = response.json()
        device_id = data["device_id"]
        cookie_value = response.cookies["device_id"]

        # With PlaintextStrategy, cookie value equals device ID
        assert cookie_value == device_id
        assert len(device_id) > 10  # Should be a UUID-like string

    def test_jwt_strategy_creates_jwt_cookie(self, jwt_app):
        """Given JWTStrategy middleware
        When making a request
        Then cookie should contain JWT token, not raw device ID"""
        # Given
        client = TestClient(jwt_app)

        # When
        response = client.get("/")

        # Then
        assert response.status_code == 200
        data = response.json()
        device_id = data["device_id"]
        cookie_value = response.cookies["device_id"]

        # With JWTStrategy, cookie value should be JWT (different from device ID)
        assert cookie_value != device_id
        assert "." in cookie_value  # JWT format
        assert len(cookie_value) > len(device_id)  # JWT is longer

    def test_encrypted_strategy_creates_encrypted_cookie(self, encrypted_app):
        """Given EncryptedStrategy middleware
        When making a request
        Then cookie should contain encrypted data, not raw device ID"""
        # Given
        client = TestClient(encrypted_app)

        # When
        response = client.get("/")

        # Then
        assert response.status_code == 200
        data = response.json()
        device_id = data["device_id"]
        cookie_value = response.cookies["device_id"]

        # With EncryptedStrategy, cookie value should be encrypted (different from device ID)
        assert cookie_value != device_id
        assert len(cookie_value) > len(device_id)  # Encrypted data is longer

    def test_jwt_strategy_maintains_device_id_across_requests(self, jwt_app):
        """Given JWTStrategy middleware
        When making multiple requests with the same cookie
        Then device ID should remain consistent"""
        # Given
        client = TestClient(jwt_app)

        # When - First request
        response1 = client.get("/")
        device_id_1 = response1.json()["device_id"]
        cookie = response1.cookies["device_id"]

        # When - Second request with same cookie
        client.cookies.set("device_id", cookie)
        response2 = client.get("/")
        device_id_2 = response2.json()["device_id"]

        # Then
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert device_id_1 == device_id_2

    def test_encrypted_strategy_maintains_device_id_across_requests(
        self, encrypted_app
    ):
        """Given EncryptedStrategy middleware
        When making multiple requests with the same cookie
        Then device ID should remain consistent"""
        # Given
        client = TestClient(encrypted_app)

        # When - First request
        response1 = client.get("/")
        device_id_1 = response1.json()["device_id"]
        cookie = response1.cookies["device_id"]

        # When - Second request with same cookie
        client.cookies.set("device_id", cookie)
        response2 = client.get("/")
        device_id_2 = response2.json()["device_id"]

        # Then
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert device_id_1 == device_id_2

    def test_jwt_strategy_handles_tampered_cookie_gracefully(self, jwt_app):
        """Given JWTStrategy middleware
        When request contains tampered JWT cookie
        Then middleware should generate new device ID"""
        # Given
        client = TestClient(jwt_app)
        # Get a valid cookie first
        response1 = client.get("/")
        valid_cookie = response1.cookies["device_id"]
        original_device_id = response1.json()["device_id"]

        # Tamper with the cookie
        tampered_cookie = valid_cookie[:-5] + "XXXXX"

        # When
        client.cookies.set("device_id", tampered_cookie)
        response2 = client.get("/")

        # Then
        assert response2.status_code == 200
        new_device_id = response2.json()["device_id"]
        # Should generate a new device ID (tampered cookie rejected)
        assert new_device_id != original_device_id
        # Should set a new cookie
        assert "device_id" in response2.cookies

    def test_encrypted_strategy_handles_tampered_cookie_gracefully(self, encrypted_app):
        """Given EncryptedStrategy middleware
        When request contains tampered encrypted cookie
        Then middleware should generate new device ID"""
        # Given
        client = TestClient(encrypted_app)
        # Get a valid cookie first
        response1 = client.get("/")
        valid_cookie = response1.cookies["device_id"]
        original_device_id = response1.json()["device_id"]

        # Tamper with the cookie
        tampered_cookie = valid_cookie[:-5] + "XXXXX"

        # When
        client.cookies.set("device_id", tampered_cookie)
        response2 = client.get("/")

        # Then
        assert response2.status_code == 200
        new_device_id = response2.json()["device_id"]
        # Should generate a new device ID (tampered cookie rejected)
        assert new_device_id != original_device_id
        # Should set a new cookie
        assert "device_id" in response2.cookies

    def test_strategies_work_with_multiple_endpoints(self, jwt_app):
        """Given JWT strategy middleware with multiple endpoints
        When accessing different endpoints with same cookie
        Then device ID should be consistent across endpoints"""
        # Given
        client = TestClient(jwt_app)

        # When - First endpoint
        response1 = client.get("/")
        device_id_1 = response1.json()["device_id"]
        cookie = response1.cookies["device_id"]

        # When - Second endpoint with same cookie
        client.cookies.set("device_id", cookie)
        response2 = client.get("/profile")
        device_id_2 = response2.json()["device_id"]

        # Then
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert device_id_1 == device_id_2
        assert response2.json()["profile"] == "user_profile"

    def test_strategy_handles_missing_cookie_gracefully(self, jwt_app):
        """Given any strategy middleware
        When request has no device_id cookie
        Then middleware should generate new device ID and set cookie"""
        # Given
        client = TestClient(jwt_app)

        # When - Request without any cookies
        response = client.get("/")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "device_id" in data
        assert len(data["device_id"]) > 10
        assert "device_id" in response.cookies

    def test_strategies_are_independent_per_app(self):
        """Given multiple apps with different strategies
        When making requests to each
        Then each should use its own strategy independently"""
        # Given
        plaintext_app = FastAPI()
        plaintext_app.add_middleware(
            DeviceMiddleware, security_strategy=PlaintextStrategy()
        )

        jwt_app = FastAPI()
        jwt_app.add_middleware(
            DeviceMiddleware, security_strategy=JWTStrategy("secret")
        )

        @plaintext_app.get("/")
        @jwt_app.get("/")
        async def root(device_id: DeviceId):
            return {"device_id": device_id}

        plaintext_client = TestClient(plaintext_app)
        jwt_client = TestClient(jwt_app)

        # When
        plaintext_response = plaintext_client.get("/")
        jwt_response = jwt_client.get("/")

        # Then
        assert plaintext_response.status_code == 200
        assert jwt_response.status_code == 200

        # Cookie formats should be different
        plaintext_cookie = plaintext_response.cookies["device_id"]
        jwt_cookie = jwt_response.cookies["device_id"]

        # Plaintext cookie equals device ID
        assert plaintext_cookie == plaintext_response.json()["device_id"]
        # JWT cookie is different from device ID
        assert jwt_cookie != jwt_response.json()["device_id"]
        assert "." in jwt_cookie  # JWT format

    def test_default_middleware_uses_plaintext_strategy(self):
        """Given DeviceMiddleware without explicit strategy
        When making a request
        Then it should use PlaintextStrategy by default"""
        # Given
        app = FastAPI()
        app.add_middleware(DeviceMiddleware)  # No explicit strategy

        @app.get("/")
        async def root(device_id: DeviceId):
            return {"device_id": device_id}

        client = TestClient(app)

        # When
        response = client.get("/")

        # Then
        assert response.status_code == 200
        device_id = response.json()["device_id"]
        cookie_value = response.cookies["device_id"]

        # Should behave like PlaintextStrategy (cookie equals device ID)
        assert cookie_value == device_id

    @pytest.mark.parametrize(
        "strategy_class,strategy_args",
        [
            (PlaintextStrategy, ()),
            (JWTStrategy, ("test-secret",)),
            (EncryptedStrategy, ("test-key",)),
        ],
    )
    def test_all_strategies_handle_unicode_device_ids(
        self, strategy_class, strategy_args
    ):
        """Given any strategy
        When device ID contains unicode characters
        Then it should handle them correctly"""
        # Given
        app = FastAPI()
        strategy = strategy_class(*strategy_args)

        # Custom ID generator that produces unicode
        def unicode_generator():
            return "测试-device-🔐-123"

        app.add_middleware(
            DeviceMiddleware, security_strategy=strategy, id_generator=unicode_generator
        )

        @app.get("/")
        async def root(device_id: DeviceId):
            return {"device_id": device_id}

        client = TestClient(app)

        # When
        response = client.get("/")

        # Then
        assert response.status_code == 200
        device_id = response.json()["device_id"]
        assert "测试" in device_id
        assert "🔐" in device_id


class TestStrategyPerformanceIntegration:
    """Integration tests focusing on performance characteristics."""

    @pytest.mark.parametrize(
        "strategy_name,strategy_class,strategy_args",
        [
            ("plaintext", PlaintextStrategy, ()),
            ("jwt", JWTStrategy, ("perf-test-secret",)),
            ("encrypted", EncryptedStrategy, ("perf-test-key",)),
        ],
    )
    def test_strategies_perform_within_acceptable_limits(
        self, strategy_name, strategy_class, strategy_args
    ):
        """Given a strategy integrated with middleware
        When making requests
        Then response times should be acceptable for web applications"""
        import time

        # Given
        strategy = strategy_class(*strategy_args)
        app = FastAPI()
        app.add_middleware(DeviceMiddleware, security_strategy=strategy)

        @app.get("/")
        async def root(device_id: DeviceId):
            return {"device_id": device_id}

        client = TestClient(app)

        # When - Measure response time
        start_time = time.time()
        response = client.get("/")
        response_time = time.time() - start_time

        # Then
        assert response.status_code == 200
        # Response should be fast (< 100ms for integration tests)
        assert (
            response_time < 0.1
        ), f"{strategy_name} strategy took {response_time:.3f}s"

    def test_strategies_handle_concurrent_requests(self):
        """Given any strategy
        When handling multiple concurrent requests
        Then each should get a unique device ID"""
        # Given
        app = FastAPI()
        app.add_middleware(
            DeviceMiddleware, security_strategy=JWTStrategy("concurrent-test-secret")
        )

        @app.get("/")
        async def root(device_id: DeviceId):
            return {"device_id": device_id}

        client = TestClient(app)

        # When - Make multiple concurrent requests (simulated)
        responses = [client.get("/") for _ in range(5)]
        device_ids = [r.json()["device_id"] for r in responses]

        # Then
        assert all(r.status_code == 200 for r in responses)
        # All device IDs should be unique
        assert len(set(device_ids)) == len(device_ids)
        # All should have cookies set
        assert all("device_id" in r.cookies for r in responses)
