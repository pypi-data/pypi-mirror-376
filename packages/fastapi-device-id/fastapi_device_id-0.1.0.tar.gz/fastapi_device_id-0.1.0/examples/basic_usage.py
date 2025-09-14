"""Basic usage example for FastAPI Device ID middleware."""

from fastapi import FastAPI

from fastapi_device_id import DeviceId, DeviceMiddleware

app = FastAPI(title="Device ID Basic Example")

# Add the device middleware with default settings
app.add_middleware(DeviceMiddleware)


@app.get("/")
async def read_root(device_id: DeviceId):
    """Root endpoint that displays the device ID."""
    return {
        "message": "Hello! Your device has been identified.",
        "device_id": device_id,
        "info": "This ID will persist across browser sessions.",
    }


@app.get("/visit")
async def track_visit(device_id: DeviceId):
    """Example endpoint for tracking visits."""
    print(f"Visit tracked for device: {device_id}")
    return {"status": "visit tracked", "device_id": device_id}


@app.get("/profile")
async def user_profile(device_id: DeviceId):
    """Example of building anonymous user profiles."""
    # In a real app, you might store preferences, settings, etc.
    # keyed by device_id in a database
    return {
        "device_id": device_id,
        "profile": {"theme": "auto", "language": "en", "visits_today": 1},
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
