"""Security strategies for device ID encoding/decoding."""

import hashlib
import time
from abc import ABC, abstractmethod
from typing import Any, Dict
from urllib.parse import quote, unquote

try:
    import jwt
except ImportError:
    jwt = None  # type: ignore[assignment]

try:
    import base64
    import os

    from cryptography.fernet import Fernet
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
except ImportError:
    # Cryptography dependencies not available
    Fernet = None  # type: ignore[assignment,misc]
    hashes = None  # type: ignore[assignment]
    Cipher = None  # type: ignore[assignment,misc]
    algorithms = None  # type: ignore[assignment]
    modes = None  # type: ignore[assignment]
    PBKDF2HMAC = None  # type: ignore[assignment,misc]
    default_backend = None  # type: ignore[assignment]
    base64 = None  # type: ignore[assignment]
    os = None  # type: ignore[assignment]


class DeviceIDSecurityStrategy(ABC):
    """Base class for device ID security strategies."""

    @abstractmethod
    def encode(self, device_id: str) -> str:
        """Encode/encrypt the device ID for storage in cookie.

        Args:
            device_id: The raw device ID to encode

        Returns:
            Encoded string suitable for cookie storage
        """
        pass

    @abstractmethod
    def decode(self, encoded_value: str) -> str | None:
        """Decode/decrypt the device ID from cookie value.

        Args:
            encoded_value: The encoded value from the cookie

        Returns:
            The original device ID, or None if decoding failed/invalid
        """
        pass


class PlaintextStrategy(DeviceIDSecurityStrategy):
    """No security strategy - stores device ID as plaintext.

    This is the default strategy for backward compatibility.
    WARNING: Provides no security against cookie tampering.
    """

    def encode(self, device_id: str) -> str:
        """URL-encode device ID to ensure cookie safety."""
        return quote(device_id, safe="")

    def decode(self, encoded_value: str) -> str | None:
        """URL-decode device ID from cookie value."""
        if not encoded_value:
            return None
        try:
            return unquote(encoded_value)
        except Exception:
            return None


class JWTStrategy(DeviceIDSecurityStrategy):
    """JWT-based strategy with signing and optional expiration.

    Provides tamper detection through cryptographic signatures.
    Device ID is visible but integrity-protected.
    """

    def __init__(
        self, secret: str, algorithm: str = "HS256", expiration_hours: int | None = None
    ):
        """Initialize JWT strategy.

        Args:
            secret: Secret key for JWT signing
            algorithm: JWT algorithm (HS256, HS384, HS512, etc.)
            expiration_hours: Token expiration in hours (None = no expiration)

        Raises:
            ImportError: If PyJWT is not installed
        """
        if jwt is None:
            raise ImportError(
                "PyJWT is required for JWTStrategy. "
                "Install with: pip install 'fastapi-device-id[jwt]'"
            )

        self.secret = secret
        self.algorithm = algorithm
        self.expiration_hours = expiration_hours

    def encode(self, device_id: str) -> str:
        """Encode device ID as a JWT token."""
        payload: Dict[str, Any] = {"device_id": device_id}

        if self.expiration_hours:
            payload["exp"] = int(time.time()) + (self.expiration_hours * 3600)

        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def decode(self, encoded_value: str) -> str | None:
        """Decode JWT token to extract device ID."""
        try:
            payload = jwt.decode(
                encoded_value, self.secret, algorithms=[self.algorithm]
            )
            return payload.get("device_id")
        except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, KeyError):
            return None


class EncryptedStrategy(DeviceIDSecurityStrategy):
    """Encryption-based strategy with configurable algorithms.

    Provides confidentiality - device ID is hidden from client.
    Supports multiple encryption algorithms via cryptography library.
    """

    SUPPORTED_ALGORITHMS = {
        "fernet": "Fernet symmetric encryption (recommended)",
        "aes-256-gcm": "AES-256 in GCM mode",
        "aes-128-gcm": "AES-128 in GCM mode",
    }

    def __init__(
        self,
        key: str | bytes,
        algorithm: str = "fernet",
        salt: str | bytes | None = None,
        iterations: int = 100000,
    ):
        """Initialize encryption strategy.

        Args:
            key: Encryption key (string or bytes)
            algorithm: Encryption algorithm (fernet, aes-256-gcm, aes-128-gcm)
            salt: Optional salt for key derivation. If not provided, derives from key.
            iterations: Number of PBKDF2 iterations for key derivation (default: 100000).
                       Higher values increase security but also increase computation time.
                       Recommended minimum: 100000 (2024 standards suggest 200000+).

        Raises:
            ImportError: If cryptography is not installed
            ValueError: If algorithm is not supported or iterations is invalid

        Note:
            When no salt is provided, derives a deterministic salt from the key.
            This ensures consistent behavior across multiple application instances,
            enabling horizontal scaling and load balancing. While not optimal from
            a pure cryptographic perspective, this approach is necessary for
            distributed deployments where multiple instances need to decrypt
            each other's device ID cookies.
        """
        if Fernet is None:
            raise ImportError(
                "cryptography is required for EncryptedStrategy. "
                "Install with: pip install 'fastapi-device-id[crypto]'"
            )

        if algorithm not in self.SUPPORTED_ALGORITHMS:
            supported = ", ".join(self.SUPPORTED_ALGORITHMS.keys())
            raise ValueError(
                f"Unsupported algorithm '{algorithm}'. "
                f"Supported algorithms: {supported}"
            )

        if iterations < 10000:
            raise ValueError(
                f"Iterations must be at least 10000 for security. Got: {iterations}"
            )

        self.algorithm = algorithm
        self.iterations = iterations
        self.salt = self._prepare_salt(key, salt)
        self._setup_cipher(key)

    def _prepare_salt(self, key: str | bytes, salt: str | bytes | None) -> bytes:
        """Prepare salt for key derivation.

        If salt is not provided, derives it deterministically from the key.
        This ensures consistent behavior across distributed systems.

        Args:
            key: The encryption key
            salt: Optional custom salt

        Returns:
            Salt as bytes (16 bytes)
        """
        if salt is not None:
            if isinstance(salt, str):
                return salt.encode("utf-8")
            return salt

        # Derive deterministic salt from key if not provided
        if isinstance(key, str):
            key = key.encode("utf-8")

        # Use SHA-256 to derive a deterministic salt from the key
        # This allows distributed systems to decrypt each other's cookies
        return hashlib.sha256(b"fastapi-device-id-salt-v1:" + key).digest()[:16]

    def _setup_cipher(self, key: str | bytes) -> None:
        """Set up the cipher based on the algorithm."""
        if isinstance(key, str):
            key = key.encode("utf-8")

        if self.algorithm == "fernet":
            # For Fernet, we need a URL-safe base64-encoded 32-byte key
            if (
                len(key) != 44
                or not key.replace(b"=", b"")
                .replace(b"-", b"")
                .replace(b"_", b"")
                .isalnum()
            ):
                # Derive proper Fernet key from provided key
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=self.salt,
                    iterations=self.iterations,
                    backend=default_backend(),
                )
                derived_key = base64.urlsafe_b64encode(kdf.derive(key))
            else:
                derived_key = key

            self.cipher = Fernet(derived_key)

        elif self.algorithm.startswith("aes-"):
            # For AES, derive appropriate key length
            key_length = 32 if "256" in self.algorithm else 16
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=key_length,
                salt=self.salt,
                iterations=self.iterations,
                backend=default_backend(),
            )
            self.key = kdf.derive(key)

    def encode(self, device_id: str) -> str:
        """Encrypt the device ID."""
        device_bytes = device_id.encode("utf-8")

        if self.algorithm == "fernet":
            encrypted = self.cipher.encrypt(device_bytes)
            return base64.urlsafe_b64encode(encrypted).decode("ascii")

        elif self.algorithm.endswith("-gcm"):
            # AES-GCM encryption
            iv = os.urandom(12)  # 96-bit IV for GCM

            if "256" in self.algorithm:
                cipher_algo = algorithms.AES(self.key)
            else:
                cipher_algo = algorithms.AES(self.key)

            cipher = Cipher(cipher_algo, modes.GCM(iv), backend=default_backend())
            encryptor = cipher.encryptor()

            ciphertext = encryptor.update(device_bytes) + encryptor.finalize()

            # Combine IV + tag + ciphertext
            encrypted_data = iv + encryptor.tag + ciphertext
            return base64.urlsafe_b64encode(encrypted_data).decode("ascii")

        # This should never be reached due to algorithm validation in __init__
        raise ValueError(f"Unsupported algorithm: {self.algorithm}")

    def decode(self, encoded_value: str) -> str | None:
        """Decrypt the device ID."""
        try:
            encrypted_data = base64.urlsafe_b64decode(encoded_value.encode("ascii"))

            if self.algorithm == "fernet":
                decrypted = self.cipher.decrypt(encrypted_data)
                return decrypted.decode("utf-8")

            elif self.algorithm.endswith("-gcm"):
                # Extract IV (12 bytes) + tag (16 bytes) + ciphertext
                if len(encrypted_data) < 28:  # 12 + 16 minimum
                    return None

                iv = encrypted_data[:12]
                tag = encrypted_data[12:28]
                ciphertext = encrypted_data[28:]

                if "256" in self.algorithm:
                    cipher_algo = algorithms.AES(self.key)
                else:
                    cipher_algo = algorithms.AES(self.key)

                cipher = Cipher(
                    cipher_algo, modes.GCM(iv, tag), backend=default_backend()
                )
                decryptor = cipher.decryptor()

                decrypted = decryptor.update(ciphertext) + decryptor.finalize()
                return decrypted.decode("utf-8")

            # This should never be reached due to algorithm validation in __init__
            return None

        except Exception:
            # Any decryption error means invalid/tampered data
            return None
