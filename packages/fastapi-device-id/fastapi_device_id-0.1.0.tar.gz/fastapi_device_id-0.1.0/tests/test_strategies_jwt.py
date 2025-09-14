"""Unit tests for JWTStrategy.

JWTStrategy provides tamper detection through cryptographic signatures.
Tests focus on JWT creation, validation, expiration, and error handling.
"""

from unittest.mock import patch

import pytest

from fastapi_device_id.strategies import JWTStrategy


def test_jwt_strategy_requires_jwt_library():
    """Given PyJWT is not available
    When creating JWTStrategy
    Then it should raise ImportError"""
    # Given
    with patch("fastapi_device_id.strategies.jwt", None):
        # When/Then
        with pytest.raises(ImportError) as exc_info:
            JWTStrategy("secret")
        assert "PyJWT is required" in str(exc_info.value)


def test_jwt_encode_creates_jwt_token():
    """Given a device ID
    When encoding with JWTStrategy
    Then it should return a JWT token with correct structure"""
    # Given
    strategy = JWTStrategy("test-secret-key")
    device_id = "test-device-123"

    # When
    encoded = strategy.encode(device_id)

    # Then
    assert isinstance(encoded, str)
    # JWT tokens have 3 parts separated by dots
    parts = encoded.split(".")
    assert len(parts) == 3
    # Each part should be base64-encoded (no spaces)
    for part in parts:
        assert " " not in part


def test_jwt_decode_extracts_device_id_from_valid_jwt():
    """Given a valid JWT token
    When decoding with JWTStrategy
    Then it should extract the original device ID"""
    # Given
    strategy = JWTStrategy("test-secret-key")
    device_id = "original-device-456"
    encoded = strategy.encode(device_id)

    # When
    decoded = strategy.decode(encoded)

    # Then
    assert decoded == device_id


def test_jwt_encode_decode_roundtrip_preserves_device_id():
    """Given a device ID
    When encoding then decoding with JWTStrategy
    Then it should preserve the original device ID"""
    # Given
    strategy = JWTStrategy("test-secret-key")
    original_id = "roundtrip-test-789"

    # When
    encoded = strategy.encode(original_id)
    decoded = strategy.decode(encoded)

    # Then
    assert decoded == original_id


def test_jwt_decode_invalid_jwt_returns_none():
    """Given an invalid JWT token
    When decoding with JWTStrategy
    Then it should return None"""
    # Given
    strategy = JWTStrategy("test-secret-key")
    invalid_jwt = "not.a.valid.jwt.token"

    # When
    decoded = strategy.decode(invalid_jwt)

    # Then
    assert decoded is None


def test_jwt_decode_tampered_jwt_returns_none():
    """Given a tampered JWT token
    When decoding with JWTStrategy
    Then it should return None (tamper detection)"""
    # Given
    strategy = JWTStrategy("test-secret-key")
    device_id = "tamper-test-abc"
    valid_jwt = strategy.encode(device_id)
    # Tamper with the token by changing a character
    tampered_jwt = valid_jwt[:-5] + "XXXXX"

    # When
    decoded = strategy.decode(tampered_jwt)

    # Then
    assert decoded is None


def test_jwt_strategy_with_custom_algorithm():
    """Given JWTStrategy with custom algorithm
    When encoding and decoding
    Then it should work with the specified algorithm"""
    # Given
    strategy = JWTStrategy("secret", algorithm="HS384")
    device_id = "algorithm-test-def"

    # When
    encoded = strategy.encode(device_id)
    decoded = strategy.decode(encoded)

    # Then
    assert decoded == device_id


def test_jwt_strategy_with_expiration():
    """Given JWTStrategy with expiration
    When encoding a device ID
    Then the token should contain expiration claim"""
    # Given
    strategy = JWTStrategy("secret", expiration_hours=1)
    device_id = "expiration-test-ghi"

    # When
    encoded = strategy.encode(device_id)
    decoded = strategy.decode(encoded)

    # Then
    assert decoded == device_id


def test_jwt_expired_jwt_returns_none():
    """Given JWTStrategy with very short expiration
    When token expires
    Then decoding should return None"""
    # Given
    strategy = JWTStrategy("secret", expiration_hours=1)
    device_id = "expired-test-jkl"

    # Mock time to simulate expiration
    with patch("fastapi_device_id.strategies.time") as mock_time:
        # Set current time for encoding
        mock_time.time.return_value = 1000000
        encoded = strategy.encode(device_id)

        # Fast forward time beyond expiration
        mock_time.time.return_value = 1000000 + 3601  # 1 hour + 1 second

        # When
        decoded = strategy.decode(encoded)

        # Then
        assert decoded is None


def test_jwt_different_secrets_cannot_decode_each_others_tokens():
    """Given JWTStrategies with different secrets
    When one encodes and another tries to decode
    Then decoding should return None (security boundary)"""
    # Given
    strategy1 = JWTStrategy("secret-one")
    strategy2 = JWTStrategy("secret-two")
    device_id = "cross-secret-test-mno"

    # When
    encoded_by_1 = strategy1.encode(device_id)
    decoded_by_2 = strategy2.decode(encoded_by_1)

    # Then
    assert decoded_by_2 is None
