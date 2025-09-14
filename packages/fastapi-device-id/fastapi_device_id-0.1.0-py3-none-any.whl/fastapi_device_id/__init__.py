"""FastAPI Device ID Middleware.

A simple middleware for FastAPI applications that provides persistent device
identification through secure HTTP cookies. Perfect for analytics, anonymous
session tracking, and device differentiation.
"""

from .middleware import DeviceId, DeviceMiddleware, compare_device_ids, get_device_id
from .strategies import (
    DeviceIDSecurityStrategy,
    EncryptedStrategy,
    JWTStrategy,
    PlaintextStrategy,
)

__version__ = "0.1.0"
__all__ = [
    "DeviceMiddleware",
    "DeviceId",
    "get_device_id",
    "compare_device_ids",
    "DeviceIDSecurityStrategy",
    "PlaintextStrategy",
    "JWTStrategy",
    "EncryptedStrategy",
]
