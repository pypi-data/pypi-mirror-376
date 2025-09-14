"""Device middleware for FastAPI to handle unique browser identifiers.

This middleware provides unique device identification for browsers and serves
as the foundation for anonymous session management.
"""

import inspect
import secrets
import uuid
from typing import Annotated, Any, Awaitable, Callable, Literal, Union

from fastapi import Depends, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .strategies import DeviceIDSecurityStrategy, PlaintextStrategy

# Determine UUID function at import time to avoid runtime checks
_uuid_func = uuid.uuid7 if hasattr(uuid, "uuid7") else uuid.uuid4


def default_id_generator() -> str:
    """Generate a device ID using the best available UUID version."""
    return str(_uuid_func())


class DeviceMiddleware(BaseHTTPMiddleware):
    """Middleware to handle device identification for browsers.

    Sets a unique device identifier cookie for each browser/client.
    This serves as the basis for anonymous session tracking.
    """

    def __init__(
        self,
        app: Any,
        cookie_name: str = "device_id",
        cookie_max_age: int = 365 * 24 * 60 * 60,  # 1 year
        cookie_expires: str | None = None,
        cookie_path: str = "/",
        cookie_domain: str | None = None,
        cookie_secure: bool = True,
        cookie_httponly: bool = True,
        cookie_samesite: Literal["lax", "strict", "none"] = "lax",
        id_generator: Union[
            Callable[[], str], Callable[[], Awaitable[str]]
        ] = default_id_generator,
        security_strategy: DeviceIDSecurityStrategy | None = None,
    ):
        """Initialize the device middleware.

        Args:
            app: FastAPI application instance
            cookie_name: Name of the device identifier cookie
            cookie_max_age: Cookie max age in seconds (default: 1 year)
            cookie_expires: Cookie expiration date string
            cookie_path: Cookie path (default: "/")
            cookie_domain: Cookie domain
            cookie_secure: Whether cookie should be secure (HTTPS only)
            cookie_httponly: Whether cookie should be HTTP-only
            cookie_samesite: SameSite cookie attribute
            id_generator: Function to generate device IDs (defaults to UUID7/UUID4)
            security_strategy: Security strategy for encoding device IDs (defaults to plaintext)
        """
        super().__init__(app)
        self.cookie_name = cookie_name
        self.cookie_max_age = cookie_max_age
        self.cookie_expires = cookie_expires
        self.cookie_path = cookie_path
        self.cookie_domain = cookie_domain
        self.cookie_secure = cookie_secure
        self.cookie_httponly = cookie_httponly
        self.cookie_samesite = cookie_samesite
        self.id_generator = id_generator
        self.security_strategy = security_strategy or PlaintextStrategy()

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request and ensure device ID is set.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response with device ID cookie set if needed
        """
        # Try to decode existing device ID from cookie
        encoded_cookie = request.cookies.get(self.cookie_name)
        device_id: str | None = None

        if encoded_cookie:
            device_id = self.security_strategy.decode(encoded_cookie)

        must_generate = not device_id

        if must_generate:
            # Generate new device ID
            device_id = (
                await result
                if inspect.isawaitable(result := self.id_generator())
                else result
            )

        # Ensure device_id is never None at this point
        assert device_id is not None, "Device ID should not be None after generation"
        request.state.device_id = device_id
        response = await call_next(request)

        # Only set cookie for new device IDs to avoid unnecessary writes
        if must_generate:
            # Encode device ID using security strategy
            encoded_device_id = self.security_strategy.encode(device_id)
            response.set_cookie(
                key=self.cookie_name,
                value=encoded_device_id,
                max_age=self.cookie_max_age,
                expires=self.cookie_expires,
                path=self.cookie_path,
                domain=self.cookie_domain,
                secure=self.cookie_secure,
                httponly=self.cookie_httponly,
                samesite=self.cookie_samesite,
            )

        return response


# Type helpers for dependency injection
def get_device_id(request: Request) -> str:
    """Get device ID from request state."""
    return request.state.device_id


DeviceId = Annotated[str, Depends(get_device_id)]
"""Type alias for device ID dependency injection in FastAPI route handlers.

Usage:
    @app.get("/")
    async def my_handler(device_id: DeviceId):
        return {"device_id": device_id}
"""


def compare_device_ids(id1: str, id2: str) -> bool:
    """Compare two device IDs using constant-time comparison.

    This function prevents timing attacks by ensuring the comparison
    always takes the same amount of time regardless of the input values.

    Args:
        id1: First device ID
        id2: Second device ID

    Returns:
        True if the device IDs match, False otherwise

    Example:
        # ❌ VULNERABLE to timing attacks
        if device_id == stored_device_id:
            grant_access()

        # ✅ SECURE constant-time comparison
        if compare_device_ids(device_id, stored_device_id):
            grant_access()
    """
    return secrets.compare_digest(id1, id2)
