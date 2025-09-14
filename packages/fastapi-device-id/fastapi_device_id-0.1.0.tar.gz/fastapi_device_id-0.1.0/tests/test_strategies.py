"""Shared unit tests for device ID security strategies.

Following TDD principles: F.I.R.S.T (Fast, Independent, Repeatable, Self-Validating, Timely)
Each test follows AAA pattern: Arrange, Act, Assert
Tests focus on behavior, not implementation details.

This module contains tests that apply across multiple strategies or test abstract behavior.
"""

import time

import pytest

from fastapi_device_id.strategies import (
    DeviceIDSecurityStrategy,
    EncryptedStrategy,
    JWTStrategy,
    PlaintextStrategy,
)

# Strategy configurations for all parametrized tests
STRATEGY_CONFIGS = [
    ("plaintext", PlaintextStrategy, ()),
    ("jwt", JWTStrategy, ("secret1",)),
    ("encrypted", EncryptedStrategy, ("key1", "fernet")),
]


# Abstract base class tests
def test_strategy_is_abstract_class():
    """Given DeviceIDSecurityStrategy is abstract
    When trying to instantiate it directly
    Then it should raise TypeError"""
    # Given/When/Then
    with pytest.raises(TypeError):
        DeviceIDSecurityStrategy()


def test_strategy_requires_encode_method():
    """Given a strategy subclass without encode method
    When trying to instantiate it
    Then it should raise TypeError"""

    # Given
    class IncompleteStrategy(DeviceIDSecurityStrategy):
        def decode(self, encoded_value: str) -> str | None:
            return encoded_value

    # When/Then
    with pytest.raises(TypeError):
        IncompleteStrategy()


def test_strategy_requires_decode_method():
    """Given a strategy subclass without decode method
    When trying to instantiate it
    Then it should raise TypeError"""

    # Given
    class IncompleteStrategy(DeviceIDSecurityStrategy):
        def encode(self, device_id: str) -> str:
            return device_id

    # When/Then
    with pytest.raises(TypeError):
        IncompleteStrategy()


# Cross-strategy performance tests
@pytest.mark.parametrize("strategy_name,strategy_class,strategy_args", STRATEGY_CONFIGS)
def test_strategies_are_fast(strategy_name, strategy_class, strategy_args):
    """Test that each strategy executes quickly.
    This verifies F.I.R.S.T principles: Fast."""
    # Given
    strategy = strategy_class(*strategy_args)
    device_id = "fast-test-123"

    # When - measure execution time
    start_time = time.time()
    encoded = strategy.encode(device_id)
    decoded = strategy.decode(encoded)
    execution_time = time.time() - start_time

    # Then
    assert decoded == device_id
    # Each strategy should be fast (< 50ms for unit tests)
    assert (
        execution_time < 0.05
    ), f"{strategy_class.__name__} took {execution_time:.3f}s, should be < 0.05s"


def test_strategies_are_independent():
    """Test that strategies produce different outputs and work independently.
    This verifies F.I.R.S.T principles: Independent."""
    # Given
    device_id = "independence-test-123"

    # When
    results = []
    for name, strategy_class, args in STRATEGY_CONFIGS:
        strategy = strategy_class(*args)
        encoded = strategy.encode(device_id)
        decoded = strategy.decode(encoded)
        results.append((name, encoded, decoded))

    # Then
    # All strategies should work independently
    assert all(decoded == device_id for _, _, decoded in results)

    # All strategies should produce different encoded values
    encoded_values = [(name, encoded) for name, encoded, _ in results]

    # For ASCII device IDs, PlaintextStrategy returns same value (URL encoding doesn't change ASCII)
    plaintext_encoded = next(
        encoded for name, encoded in encoded_values if name == "plaintext"
    )
    jwt_encoded = next(encoded for name, encoded in encoded_values if name == "jwt")
    encrypted_encoded = next(
        encoded for name, encoded in encoded_values if name == "encrypted"
    )

    if device_id.encode("ascii", errors="ignore").decode("ascii") == device_id:
        assert plaintext_encoded == device_id  # Plaintext unchanged for ASCII
    else:
        assert plaintext_encoded != device_id  # Plaintext URL-encoded for non-ASCII
    assert jwt_encoded != device_id  # JWT different
    assert encrypted_encoded != device_id  # Encrypted different


@pytest.mark.parametrize("strategy_name,strategy_class,strategy_args", STRATEGY_CONFIGS)
def test_individual_strategy_independence(strategy_name, strategy_class, strategy_args):
    """Test that each individual strategy works independently.
    This verifies F.I.R.S.T principles: Independent."""
    # Given
    strategy = strategy_class(*strategy_args)
    device_id = "individual-independence-test-456"

    # When
    encoded = strategy.encode(device_id)
    decoded = strategy.decode(encoded)

    # Then
    assert decoded == device_id

    # Test multiple encode/decode cycles work consistently
    for _ in range(3):
        encoded_cycle = strategy.encode(device_id)
        decoded_cycle = strategy.decode(encoded_cycle)
        assert decoded_cycle == device_id

    # Deterministic strategies should produce same output
    if strategy_name in ("plaintext", "jwt"):
        encoded2 = strategy.encode(device_id)
        assert encoded == encoded2  # Deterministic strategies
    # Non-deterministic strategies (encrypted with random IVs) may differ
    # but should still decode correctly


# Cross-strategy security boundary tests
@pytest.mark.parametrize("strategy_name,strategy_class,strategy_args", STRATEGY_CONFIGS)
def test_strategies_handle_none_input_gracefully(
    strategy_name, strategy_class, strategy_args
):
    """Given None as input to encode methods
    When encoding with any strategy
    Then it should handle gracefully without crashing"""
    strategy = strategy_class(*strategy_args)

    # This test verifies that strategies don't crash on invalid input
    # The exact behavior (exception vs None return) is implementation-defined
    try:
        strategy.encode(None)  # type: ignore[arg-type]
    except (TypeError, AttributeError):
        # Expected for strategies that call string methods on input
        pass


@pytest.mark.parametrize("strategy_name,strategy_class,strategy_args", STRATEGY_CONFIGS)
def test_strategies_handle_empty_decode_input_consistently(
    strategy_name, strategy_class, strategy_args
):
    """Given empty string as decode input
    When decoding with strategies
    Then behavior should be consistent"""
    strategy = strategy_class(*strategy_args)

    # When
    result = strategy.decode("")

    # Then
    # All strategies should return None for empty input
    assert result is None


@pytest.mark.parametrize("strategy_name,strategy_class,strategy_args", STRATEGY_CONFIGS)
@pytest.mark.parametrize(
    "malicious_input",
    [
        "../../etc/passwd",  # Path traversal
        "<script>alert('xss')</script>",  # XSS attempt
        "'; DROP TABLE users; --",  # SQL injection attempt
        "\x00\x01\x02\x03",  # Binary data
        "A" * 10000,  # Very large input
    ],
)
def test_strategies_handle_malicious_input_safely(
    strategy_name, strategy_class, strategy_args, malicious_input
):
    """Given potentially malicious input
    When processing with strategies
    Then they should handle it safely without security issues"""
    strategy = strategy_class(*strategy_args)

    encoded = strategy.encode(malicious_input)
    decoded = strategy.decode(encoded)
    # If successful, should preserve the input exactly
    assert decoded == malicious_input
