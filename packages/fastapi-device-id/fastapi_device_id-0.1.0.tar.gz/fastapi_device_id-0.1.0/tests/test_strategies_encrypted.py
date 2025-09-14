"""Unit tests for EncryptedStrategy.

EncryptedStrategy provides confidentiality through encryption.
Tests cover all supported algorithms and error conditions.
"""

from unittest.mock import patch

import pytest

from fastapi_device_id.strategies import EncryptedStrategy


def test_encrypted_strategy_requires_cryptography_library():
    """Given cryptography library is not available
    When creating EncryptedStrategy
    Then it should raise ImportError"""
    # Given
    with patch("fastapi_device_id.strategies.Fernet", None):
        # When/Then
        with pytest.raises(ImportError) as exc_info:
            EncryptedStrategy("key")
        assert "cryptography is required" in str(exc_info.value)


def test_encrypted_strategy_rejects_unsupported_algorithm():
    """Given an unsupported algorithm
    When creating EncryptedStrategy
    Then it should raise ValueError"""
    # Given/When/Then
    with pytest.raises(ValueError) as exc_info:
        EncryptedStrategy("key", algorithm="unsupported")
    assert "Unsupported algorithm" in str(exc_info.value)


@pytest.mark.parametrize("algorithm", ["fernet", "aes-256-gcm", "aes-128-gcm"])
def test_supported_algorithms_can_be_instantiated(algorithm):
    """Given supported algorithms
    When creating EncryptedStrategy
    Then it should succeed without errors"""
    # Given/When
    strategy = EncryptedStrategy("test-key", algorithm=algorithm)

    # Then
    assert strategy.algorithm == algorithm


@pytest.fixture
def fernet_strategy():
    """Fixture providing EncryptedStrategy with Fernet algorithm."""
    return EncryptedStrategy("test-fernet-key", algorithm="fernet")


@pytest.fixture
def aes256_strategy():
    """Fixture providing EncryptedStrategy with AES-256-GCM algorithm."""
    return EncryptedStrategy("test-aes256-key", algorithm="aes-256-gcm")


@pytest.fixture
def aes128_strategy():
    """Fixture providing EncryptedStrategy with AES-128-GCM algorithm."""
    return EncryptedStrategy("test-aes128-key", algorithm="aes-128-gcm")


def test_fernet_encode_produces_encrypted_output(fernet_strategy):
    """Given a device ID
    When encoding with Fernet strategy
    Then output should be different from input (encrypted)"""
    # Given
    device_id = "fernet-test-device-123"

    # When
    encoded = fernet_strategy.encode(device_id)

    # Then
    assert encoded != device_id
    assert isinstance(encoded, str)
    assert len(encoded) > len(device_id)  # Encrypted data is larger


def test_fernet_decode_recovers_original_device_id(fernet_strategy):
    """Given an encrypted device ID
    When decoding with Fernet strategy
    Then it should recover the original device ID"""
    # Given
    device_id = "fernet-decode-test-456"
    encoded = fernet_strategy.encode(device_id)

    # When
    decoded = fernet_strategy.decode(encoded)

    # Then
    assert decoded == device_id


def test_aes256_encode_decode_roundtrip(aes256_strategy):
    """Given a device ID
    When encoding then decoding with AES-256-GCM
    Then it should preserve the original device ID"""
    # Given
    device_id = "aes256-roundtrip-789"

    # When
    encoded = aes256_strategy.encode(device_id)
    decoded = aes256_strategy.decode(encoded)

    # Then
    assert decoded == device_id
    assert encoded != device_id  # Should be encrypted


def test_aes128_encode_decode_roundtrip(aes128_strategy):
    """Given a device ID
    When encoding then decoding with AES-128-GCM
    Then it should preserve the original device ID"""
    # Given
    device_id = "aes128-roundtrip-abc"

    # When
    encoded = aes128_strategy.encode(device_id)
    decoded = aes128_strategy.decode(encoded)

    # Then
    assert decoded == device_id
    assert encoded != device_id  # Should be encrypted


def test_decode_invalid_encrypted_data_returns_none(fernet_strategy):
    """Given invalid encrypted data
    When decoding with EncryptedStrategy
    Then it should return None"""
    # Given
    invalid_data = "not-valid-encrypted-data"

    # When
    decoded = fernet_strategy.decode(invalid_data)

    # Then
    assert decoded is None


def test_decode_tampered_encrypted_data_returns_none(fernet_strategy):
    """Given tampered encrypted data
    When decoding with EncryptedStrategy
    Then it should return None (integrity protection)"""
    # Given
    device_id = "tamper-test-def"
    valid_encrypted = fernet_strategy.encode(device_id)
    # Tamper with encrypted data
    tampered_encrypted = valid_encrypted[:-5] + "XXXXX"

    # When
    decoded = fernet_strategy.decode(tampered_encrypted)

    # Then
    assert decoded is None


def test_different_keys_cannot_decrypt_each_others_data():
    """Given EncryptedStrategies with different keys
    When one encrypts and another tries to decrypt
    Then decryption should return None (security boundary)"""
    # Given
    strategy1 = EncryptedStrategy("key-one", algorithm="fernet")
    strategy2 = EncryptedStrategy("key-two", algorithm="fernet")
    device_id = "cross-key-test-ghi"

    # When
    encrypted_by_1 = strategy1.encode(device_id)
    decrypted_by_2 = strategy2.decode(encrypted_by_1)

    # Then
    assert decrypted_by_2 is None


@pytest.mark.parametrize(
    "device_id",
    [
        "",  # Empty string
        "a",  # Single character
        "short",  # Short string
        "a" * 100,  # Long string
        "unicode-测试-🔐",  # Unicode characters
        "special!@#$%^&*()_+-=[]{}|;':\",./<>?",  # Special characters
    ],
)
def test_fernet_handles_various_device_id_formats(fernet_strategy, device_id):
    """Given various device ID formats
    When encoding and decoding with Fernet
    Then all should be handled correctly"""
    # Given/When
    encoded = fernet_strategy.encode(device_id)
    decoded = fernet_strategy.decode(encoded)

    # Then
    assert decoded == device_id


def test_encrypted_strategy_default_algorithm_is_fernet():
    """Given EncryptedStrategy without specifying algorithm
    When instantiating
    Then it should default to Fernet algorithm"""
    # Given/When
    strategy = EncryptedStrategy("test-key")

    # Then
    assert strategy.algorithm == "fernet"


def test_encrypted_strategy_custom_salt():
    """Given EncryptedStrategy with custom salt
    When encoding and decoding
    Then it should use the custom salt for key derivation"""
    # Given
    key = "test-key"
    custom_salt = b"my-custom-salt-16b"
    device_id = "test-device-id"

    # When - Create two strategies with same key but different salts
    strategy1 = EncryptedStrategy(key, salt=custom_salt)
    strategy2 = EncryptedStrategy(key, salt=b"different-salt-16")

    # Encode with first strategy
    encoded1 = strategy1.encode(device_id)
    encoded2 = strategy2.encode(device_id)

    # Then - Different salts should produce different encodings
    assert encoded1 != encoded2

    # And decoding with correct strategy should work
    assert strategy1.decode(encoded1) == device_id
    assert strategy2.decode(encoded2) == device_id

    # But cross-decoding should fail
    assert strategy1.decode(encoded2) is None
    assert strategy2.decode(encoded1) is None


def test_encrypted_strategy_salt_derived_from_key():
    """Given EncryptedStrategy without custom salt
    When using same key
    Then it should derive consistent salt from the key"""
    # Given
    key = "test-key"
    device_id = "test-device-id"

    # When - Create two strategies with same key, no custom salt
    strategy1 = EncryptedStrategy(key)
    strategy2 = EncryptedStrategy(key)

    # Encode with both strategies
    encoded1 = strategy1.encode(device_id)
    encoded2 = strategy2.encode(device_id)

    # Then - Same key should produce compatible encodings
    # (they may differ due to Fernet's timestamp, but should be decodable)
    assert strategy1.decode(encoded2) == device_id
    assert strategy2.decode(encoded1) == device_id

    # And salt should be the same
    assert strategy1.salt == strategy2.salt


def test_aes_strategy_with_custom_salt():
    """Given AES strategy with custom salt
    When encoding and decoding
    Then it should use the custom salt for key derivation"""
    # Given
    key = "test-key-for-aes"
    custom_salt = b"aes-custom-salt1"
    device_id = "test-device-id"

    # When - Create AES strategies with different salts
    strategy1 = EncryptedStrategy(key, algorithm="aes-256-gcm", salt=custom_salt)
    strategy2 = EncryptedStrategy(
        key, algorithm="aes-256-gcm", salt=b"different-salt-2"
    )

    # Encode with both strategies
    encoded1 = strategy1.encode(device_id)
    encoded2 = strategy2.encode(device_id)

    # Then - Different salts should produce different encodings
    assert encoded1 != encoded2

    # And each strategy can decode its own encoding
    assert strategy1.decode(encoded1) == device_id
    assert strategy2.decode(encoded2) == device_id

    # But cross-decoding should fail
    assert strategy1.decode(encoded2) is None
    assert strategy2.decode(encoded1) is None


def test_encrypted_strategy_custom_iterations():
    """Given EncryptedStrategy with custom iterations
    When encoding and decoding
    Then it should use the custom iterations for key derivation"""
    # Given
    key = "test-key"
    device_id = "test-device-id"

    # When - Create strategies with different iteration counts
    strategy1 = EncryptedStrategy(key, iterations=100000)  # Default
    strategy2 = EncryptedStrategy(key, iterations=200000)  # Higher security

    # Encode with both strategies
    encoded1 = strategy1.encode(device_id)
    encoded2 = strategy2.encode(device_id)

    # Then - Different iterations should produce different encodings
    assert encoded1 != encoded2

    # Each strategy can decode its own encoding
    assert strategy1.decode(encoded1) == device_id
    assert strategy2.decode(encoded2) == device_id

    # But cross-decoding should fail (different key derivations)
    assert strategy1.decode(encoded2) is None
    assert strategy2.decode(encoded1) is None

    # Verify iterations are stored correctly
    assert strategy1.iterations == 100000
    assert strategy2.iterations == 200000


def test_encrypted_strategy_invalid_iterations():
    """Given EncryptedStrategy with invalid iterations
    When initializing
    Then it should raise ValueError"""
    # Given
    key = "test-key"

    # When/Then - Too low iterations should fail
    with pytest.raises(ValueError, match="Iterations must be at least 10000"):
        EncryptedStrategy(key, iterations=1000)

    with pytest.raises(ValueError, match="Iterations must be at least 10000"):
        EncryptedStrategy(key, iterations=0)
