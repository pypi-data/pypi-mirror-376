"""Analytics and tracking demo for FastAPI Device ID middleware."""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List

from fastapi import FastAPI

from fastapi_device_id import DeviceId, DeviceMiddleware

app = FastAPI(title="Device ID Analytics Demo")

# Add the device middleware
app.add_middleware(DeviceMiddleware)

# In-memory storage (use a real database in production)
page_views: Dict[str, List[datetime]] = defaultdict(list)
event_tracker: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
device_sessions: Dict[str, datetime] = {}


@app.get("/")
async def homepage(device_id: DeviceId):
    """Homepage with visit tracking."""
    await track_page_view(device_id, "/")

    return {
        "message": "Welcome to the analytics demo!",
        "device_id": device_id,
        "endpoints": [
            "/analytics/summary - View your analytics",
            "/page/{page_name} - Visit different pages",
            "/event/{event_name} - Trigger custom events",
        ],
    }


@app.get("/page/{page_name}")
async def visit_page(page_name: str, device_id: DeviceId):
    """Track page visits."""
    await track_page_view(device_id, f"/page/{page_name}")

    return {
        "page": page_name,
        "device_id": device_id,
        "message": f"You visited {page_name}",
    }


@app.post("/event/{event_name}")
async def trigger_event(event_name: str, device_id: DeviceId):
    """Track custom events."""
    event_tracker[device_id][event_name] += 1

    print(f"Event '{event_name}' triggered by device {device_id}")

    return {
        "event": event_name,
        "device_id": device_id,
        "total_count": event_tracker[device_id][event_name],
        "status": "tracked",
    }


@app.get("/analytics/summary")
async def analytics_summary(device_id: DeviceId):
    """Get analytics summary for the current device."""
    # Update last seen
    device_sessions[device_id] = datetime.now()

    # Calculate page views
    device_page_views = page_views.get(device_id, [])
    total_page_views = len(device_page_views)

    # Calculate unique pages
    unique_pages = len({view.strftime("%Y-%m-%d") for view in device_page_views})

    # Get events
    device_events = dict(event_tracker.get(device_id, {}))

    # Calculate session duration (simplified)
    first_visit = min(device_page_views) if device_page_views else datetime.now()
    last_visit = max(device_page_views) if device_page_views else datetime.now()

    return {
        "device_id": device_id,
        "summary": {
            "total_page_views": total_page_views,
            "unique_days_visited": unique_pages,
            "custom_events": device_events,
            "first_visit": first_visit.isoformat(),
            "last_visit": last_visit.isoformat(),
            "session_active": True,
        },
    }


@app.get("/analytics/global")
async def global_analytics():
    """Get global analytics across all devices."""
    total_devices = len(set(list(page_views.keys()) + list(event_tracker.keys())))
    total_page_views = sum(len(views) for views in page_views.values())
    total_events = sum(sum(events.values()) for events in event_tracker.values())

    # Active devices (visited in last 24 hours)
    now = datetime.now()
    active_devices = sum(
        1
        for device_id, last_seen in device_sessions.items()
        if now - last_seen < timedelta(hours=24)
    )

    return {
        "global_analytics": {
            "total_devices": total_devices,
            "active_devices_24h": active_devices,
            "total_page_views": total_page_views,
            "total_custom_events": total_events,
        }
    }


async def track_page_view(device_id: str, page: str):
    """Helper function to track page views."""
    page_views[device_id].append(datetime.now())
    device_sessions[device_id] = datetime.now()
    print(f"Page view: {page} by device {device_id}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
