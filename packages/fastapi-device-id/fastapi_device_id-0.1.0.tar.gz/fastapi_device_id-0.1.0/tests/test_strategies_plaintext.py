"""Unit tests for PlaintextStrategy.

PlaintextStrategy provides no security - device IDs are stored as-is.
Tests focus on passthrough behavior and edge cases.
"""

import pytest

from fastapi_device_id.strategies import PlaintextStrategy


def test_plaintext_encode_returns_url_encoded_device_id():
    """Given a device ID string
    When encoding with PlaintextStrategy
    Then it should return URL-encoded string for cookie safety"""
    # Given
    strategy = PlaintextStrategy()
    device_id = "test-device-id-12345"

    # When
    encoded = strategy.encode(device_id)

    # Then
    # Simple ASCII strings are unchanged by URL encoding
    assert encoded == device_id


def test_plaintext_decode_returns_url_decoded_value():
    """Given an encoded value
    When decoding with PlaintextStrategy
    Then it should return URL-decoded string"""
    # Given
    strategy = PlaintextStrategy()
    encoded_value = "encoded-value-67890"

    # When
    decoded = strategy.decode(encoded_value)

    # Then
    # Simple ASCII strings are unchanged by URL decoding
    assert decoded == encoded_value


def test_plaintext_encode_decode_roundtrip():
    """Given a device ID
    When encoding then decoding
    Then it should return the original device ID"""
    # Given
    strategy = PlaintextStrategy()
    original_id = "uuid-12345-67890-abcdef"

    # When
    encoded = strategy.encode(original_id)
    decoded = strategy.decode(encoded)

    # Then
    assert decoded == original_id


def test_plaintext_decode_empty_string_returns_none():
    """Given an empty string
    When decoding with PlaintextStrategy
    Then it should return None"""
    # Given
    strategy = PlaintextStrategy()
    empty_value = ""

    # When
    decoded = strategy.decode(empty_value)

    # Then
    assert decoded is None


@pytest.mark.parametrize(
    "test_input",
    [
        "simple-id",
        "id-with-dashes-123",
        "id_with_underscores_456",
        "IdWithMixedCase789",
        "id.with.dots.012",
        "very-long-device-id-that-might-be-a-uuid-or-other-identifier-345678901234567890",
    ],
)
def test_plaintext_encode_handles_various_device_id_formats(test_input):
    """Given various device ID formats
    When encoding with PlaintextStrategy
    Then all should be handled correctly"""
    # Given
    strategy = PlaintextStrategy()

    # When
    encoded = strategy.encode(test_input)

    # Then
    # For ASCII inputs, should be unchanged
    assert encoded == test_input


def test_plaintext_handles_unicode_device_ids():
    """Given device ID with unicode characters
    When encoding/decoding with PlaintextStrategy
    Then it should handle them safely for cookies"""
    # Given
    strategy = PlaintextStrategy()
    unicode_device_id = "测试-device-🔐-123"

    # When
    encoded = strategy.encode(unicode_device_id)
    decoded = strategy.decode(encoded)

    # Then
    # Should be URL-encoded for cookie safety
    assert encoded != unicode_device_id  # Should be URL-encoded
    assert decoded == unicode_device_id  # Should decode back to original

    # Encoded value should be ASCII-safe for cookies
    encoded.encode("ascii")  # Should not raise exception
