"""Security strategies example for FastAPI Device ID middleware."""

import os
import secrets

from fastapi import FastAPI

from fastapi_device_id import (
    DeviceId,
    DeviceMiddleware,
    EncryptedStrategy,
    JWTStrategy,
)

# ============================================================================
# Example 1: Plaintext Strategy (Default - Backward Compatible)
# ============================================================================

app_plaintext = FastAPI(title="Plaintext Strategy Example")

app_plaintext.add_middleware(
    DeviceMiddleware,
    # Default uses PlaintextStrategy - no security, just URL encoding
    # Good for development or when cookies don't need protection
)


@app_plaintext.get("/")
async def root_plaintext(device_id: DeviceId):
    return {"device_id": device_id, "strategy": "plaintext"}


# ============================================================================
# Example 2: JWT Strategy - Signed Cookies
# ============================================================================

app_jwt = FastAPI(title="JWT Strategy Example")

# Generate a secure secret for JWT signing
JWT_SECRET = os.environ.get("JWT_SECRET", secrets.token_urlsafe(32))

app_jwt.add_middleware(
    DeviceMiddleware,
    security_strategy=JWTStrategy(
        secret=JWT_SECRET,
        algorithm="HS256",  # or HS384, HS512, RS256, etc.
    ),
)


@app_jwt.get("/")
async def root_jwt(device_id: DeviceId):
    return {"device_id": device_id, "strategy": "JWT (signed)"}


# ============================================================================
# Example 3: Encrypted Strategy with Custom Salt
# ============================================================================

app_encrypted = FastAPI(title="Encrypted Strategy Example")

# Generate a secure key for encryption
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", secrets.token_urlsafe(32))

# Option 1: Use a custom salt (recommended for production)
CUSTOM_SALT = os.environ.get("ENCRYPTION_SALT", secrets.token_bytes(16))

app_encrypted.add_middleware(
    DeviceMiddleware,
    security_strategy=EncryptedStrategy(
        key=ENCRYPTION_KEY,
        algorithm="aes-256-gcm",  # or "fernet", "aes-128-gcm"
        salt=CUSTOM_SALT,  # Custom salt for key derivation
        iterations=200000,  # Higher iterations for better security (default: 100000)
    ),
)


@app_encrypted.get("/")
async def root_encrypted(device_id: DeviceId):
    return {"device_id": device_id, "strategy": "encrypted (AES-256-GCM)"}


# ============================================================================
# Example 4: Encrypted Strategy with Auto-Derived Salt
# ============================================================================

app_auto_salt = FastAPI(title="Auto-Salt Example")

# When salt is not provided, it's automatically derived from the key
# This ensures consistent behavior while maintaining unique salts per key
app_auto_salt.add_middleware(
    DeviceMiddleware,
    security_strategy=EncryptedStrategy(
        key=ENCRYPTION_KEY,
        algorithm="fernet",
        # salt parameter omitted - will be derived from key
    ),
)


@app_auto_salt.get("/")
async def root_auto_salt(device_id: DeviceId):
    return {"device_id": device_id, "strategy": "encrypted (auto-salt)"}


# ============================================================================
# Example 5: Multiple Apps with Different Salts
# ============================================================================


def create_app_with_salt(app_name: str, salt: bytes) -> FastAPI:
    """Create an app with a specific salt for multi-tenant scenarios."""
    app = FastAPI(title=f"{app_name} App")

    # Same key but different salt = different encryption
    app.add_middleware(
        DeviceMiddleware,
        security_strategy=EncryptedStrategy(
            key=ENCRYPTION_KEY,
            algorithm="aes-256-gcm",
            salt=salt,  # Tenant-specific salt
        ),
    )

    @app.get("/")
    async def root(device_id: DeviceId):
        return {
            "app": app_name,
            "device_id": device_id,
            "note": "Same key, different salt per tenant",
        }

    return app


# Create tenant-specific apps with different salts
app_tenant1 = create_app_with_salt("Tenant1", b"tenant1-salt-16b")
app_tenant2 = create_app_with_salt("Tenant2", b"tenant2-salt-16b")


# ============================================================================
# Security Best Practices
# ============================================================================

"""
SECURITY RECOMMENDATIONS:

1. **Never use PlaintextStrategy in production**
   - It provides no security against cookie tampering
   - Use it only for development or non-sensitive tracking

2. **For JWT Strategy:**
   - Use a strong, randomly generated secret (at least 256 bits)
   - Store secrets in environment variables or secure vaults
   - Rotate secrets periodically
   - Consider using RS256 for asymmetric signatures

3. **For Encrypted Strategy:**
   - Use a strong encryption key (at least 256 bits)
   - Always use a custom salt in production
   - Different applications should use different salts
   - Use at least 100000 iterations (200000+ recommended for 2024)
   - Store keys and salts securely (environment variables, key vaults)
   - Consider key rotation strategies

4. **Salt Management:**
   - Custom salts prevent rainbow table attacks
   - Use different salts for different environments (dev/staging/prod)
   - Salts don't need to be secret, but should be unique
   - For multi-tenant apps, use tenant-specific salts

5. **Cookie Security:**
   - Always use secure=True in production (HTTPS only)
   - Keep httponly=True to prevent XSS attacks
   - Use samesite="strict" or "lax" to prevent CSRF

Example secure configuration:

    app.add_middleware(
        DeviceMiddleware,
        security_strategy=EncryptedStrategy(
            key=os.environ["DEVICE_ID_KEY"],  # From secure storage
            algorithm="aes-256-gcm",
            salt=bytes.fromhex(os.environ["DEVICE_ID_SALT"]),  # Hex-encoded salt
            iterations=200000,  # High security setting for 2024+
        ),
        cookie_secure=True,  # HTTPS only
        cookie_httponly=True,  # No JS access
        cookie_samesite="strict",  # CSRF protection
        cookie_max_age=30 * 24 * 60 * 60,  # 30 days
    )
"""

if __name__ == "__main__":
    import uvicorn

    print("Choose an example to run:")
    print("1. Plaintext (no security)")
    print("2. JWT (signed)")
    print("3. Encrypted with custom salt")
    print("4. Encrypted with auto-derived salt")
    print("5. Tenant 1 (multi-tenant example)")
    print("6. Tenant 2 (multi-tenant example)")

    choice = input("Enter choice (1-6): ").strip()

    apps = {
        "1": app_plaintext,
        "2": app_jwt,
        "3": app_encrypted,
        "4": app_auto_salt,
        "5": app_tenant1,
        "6": app_tenant2,
    }

    app = apps.get(choice, app_plaintext)
    uvicorn.run(app, host="127.0.0.1", port=8000)
