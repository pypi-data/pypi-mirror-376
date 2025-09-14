"""Advanced configuration example for FastAPI Device ID middleware."""

import secrets

from fastapi import FastAPI

from fastapi_device_id import DeviceId, DeviceMiddleware

app = FastAPI(title="Device ID Advanced Example")


def custom_id_generator() -> str:
    """Generate a custom device ID with specific format."""
    return f"dev_{secrets.token_hex(8)}_{secrets.randbelow(10000):04d}"


# Add middleware with custom configuration
app.add_middleware(
    DeviceMiddleware,
    cookie_name="my_device_tracker",  # Custom cookie name
    cookie_max_age=7 * 24 * 60 * 60,  # 1 week instead of 1 year
    cookie_secure=False,  # Allow HTTP for development
    cookie_httponly=True,  # Keep HTTP-only for security
    cookie_samesite="lax",  # Balanced security policy
    id_generator=custom_id_generator,  # Custom ID format
)


@app.get("/")
async def read_root(device_id: DeviceId):
    """Root endpoint showing custom device ID format."""
    return {
        "message": "Custom device ID format demo",
        "device_id": device_id,
        "format": "dev_{hex}_{number}",
    }


@app.get("/analytics/{event}")
async def track_event(event: str, device_id: DeviceId):
    """Track custom events with device ID."""
    print(f"Event '{event}' tracked for device: {device_id}")

    # In a real application, you might:
    # - Store this in a database
    # - Send to an analytics service
    # - Aggregate metrics

    return {
        "event": event,
        "device_id": device_id,
        "status": "tracked",
        "timestamp": "2025-01-15T10:30:00Z",  # Would use real timestamp
    }


@app.get("/ab-test")
async def ab_test_variant(device_id: DeviceId):
    """Demonstrate consistent A/B testing based on device ID."""
    # Use device ID hash to consistently assign users to variants
    device_hash = hash(device_id)
    variant = "A" if device_hash % 2 == 0 else "B"

    return {
        "device_id": device_id,
        "variant": variant,
        "feature_enabled": variant == "B",
        "description": f"Device consistently assigned to variant {variant}",
    }


@app.get("/device-info")
async def device_info(device_id: DeviceId):
    """Show information about the device tracking."""
    return {
        "device_id": device_id,
        "cookie_name": "my_device_tracker",
        "expiry": "7 days from first visit",
        "secure": False,
        "httponly": True,
        "samesite": "lax",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
