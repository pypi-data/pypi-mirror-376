"""Example demonstrating secure device ID comparison to prevent timing attacks."""

import time
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException

from fastapi_device_id import DeviceId, DeviceMiddleware, compare_device_ids

app = FastAPI(title="Secure Device ID Comparison Example")

# Add device ID middleware
app.add_middleware(DeviceMiddleware)

# Simulated database of authorized devices
AUTHORIZED_DEVICES: Dict[str, Dict[str, any]] = {
    "550e8400-e29b-41d4-a716-446655440000": {
        "name": "Admin Device",
        "permissions": ["read", "write", "admin"],
    },
    "660e8400-e29b-41d4-a716-446655440001": {
        "name": "User Device",
        "permissions": ["read"],
    },
}

# Track device access attempts (for demo purposes)
access_attempts: Dict[str, int] = {}


@app.get("/")
async def root(device_id: DeviceId):
    """Public endpoint - no authorization needed."""
    return {"message": "Welcome!", "device_id": device_id, "status": "public_access"}


@app.get("/vulnerable-admin")
async def vulnerable_admin_access(device_id: DeviceId):
    """
    ❌ VULNERABLE ENDPOINT - Uses direct string comparison.

    This endpoint is vulnerable to timing attacks because the == operator
    returns False as soon as it finds a character mismatch, potentially
    revealing information about the authorized device IDs.
    """
    # Track access attempts
    access_attempts[device_id] = access_attempts.get(device_id, 0) + 1

    # ❌ VULNERABLE: Direct string comparison
    # Execution time varies based on how many characters match
    for authorized_id in AUTHORIZED_DEVICES:
        if device_id == authorized_id:  # Timing attack vulnerability!
            device_info = AUTHORIZED_DEVICES[authorized_id]
            return {
                "status": "authorized",
                "device_name": device_info["name"],
                "permissions": device_info["permissions"],
                "warning": "This endpoint uses vulnerable comparison!",
            }

    raise HTTPException(status_code=403, detail="Unauthorized device")


@app.get("/secure-admin")
async def secure_admin_access(device_id: DeviceId):
    """
    ✅ SECURE ENDPOINT - Uses constant-time comparison.

    This endpoint is protected against timing attacks by using
    compare_device_ids() which internally uses secrets.compare_digest()
    for constant-time comparison.
    """
    # Track access attempts
    access_attempts[device_id] = access_attempts.get(device_id, 0) + 1

    # ✅ SECURE: Constant-time comparison
    # Execution time is consistent regardless of input
    for authorized_id in AUTHORIZED_DEVICES:
        if compare_device_ids(device_id, authorized_id):  # Secure comparison!
            device_info = AUTHORIZED_DEVICES[authorized_id]
            return {
                "status": "authorized",
                "device_name": device_info["name"],
                "permissions": device_info["permissions"],
                "security": "Protected with constant-time comparison",
            }

    raise HTTPException(status_code=403, detail="Unauthorized device")


@app.get("/check-permission/{permission}")
async def check_permission(permission: str, device_id: DeviceId):
    """
    Check if device has a specific permission using secure comparison.
    """
    # Find device using secure comparison
    device_info: Optional[Dict] = None
    for authorized_id, info in AUTHORIZED_DEVICES.items():
        if compare_device_ids(device_id, authorized_id):
            device_info = info
            break

    if not device_info:
        raise HTTPException(status_code=403, detail="Unknown device")

    has_permission = permission in device_info.get("permissions", [])

    return {
        "device_id": device_id,
        "permission": permission,
        "granted": has_permission,
        "all_permissions": device_info.get("permissions", []),
    }


@app.get("/timing-attack-demo")
async def timing_attack_demo():
    """
    Educational demonstration of timing attack differences.

    NOTE: This is for educational purposes only. Real timing attacks
    require statistical analysis over many requests.
    """
    import secrets

    # Generate test IDs
    target = "550e8400-e29b-41d4-a716-446655440000"
    similar = "550e8400-e29b-41d4-a716-446655440001"  # Differs at end
    different = "000e8400-e29b-41d4-a716-446655440000"  # Differs at start

    # Measure vulnerable comparison (simplified - real attacks need more samples)
    iterations = 10000

    # Test similar strings (differ at end)
    start = time.perf_counter_ns()
    for _ in range(iterations):
        _ = target == similar  # Vulnerable comparison
    vulnerable_similar_time = time.perf_counter_ns() - start

    # Test different strings (differ at start)
    start = time.perf_counter_ns()
    for _ in range(iterations):
        _ = target == different  # Vulnerable comparison
    vulnerable_different_time = time.perf_counter_ns() - start

    # Test with secure comparison
    start = time.perf_counter_ns()
    for _ in range(iterations):
        _ = secrets.compare_digest(target, similar)  # Secure comparison
    secure_similar_time = time.perf_counter_ns() - start

    start = time.perf_counter_ns()
    for _ in range(iterations):
        _ = secrets.compare_digest(target, different)  # Secure comparison
    secure_different_time = time.perf_counter_ns() - start

    return {
        "description": "Timing comparison demonstration",
        "iterations": iterations,
        "vulnerable_comparison": {
            "similar_strings_ns": vulnerable_similar_time,
            "different_strings_ns": vulnerable_different_time,
            "time_difference_ns": abs(
                vulnerable_similar_time - vulnerable_different_time
            ),
            "note": "Larger time difference = more vulnerable to timing attacks",
        },
        "secure_comparison": {
            "similar_strings_ns": secure_similar_time,
            "different_strings_ns": secure_different_time,
            "time_difference_ns": abs(secure_similar_time - secure_different_time),
            "note": "Minimal time difference = protected against timing attacks",
        },
        "warning": "Real timing attacks require statistical analysis over many requests",
    }


@app.get("/access-attempts")
async def get_access_attempts():
    """View access attempts for all devices."""
    return {
        "attempts": access_attempts,
        "total_devices": len(access_attempts),
        "total_attempts": sum(access_attempts.values()),
    }


# Security Best Practices Documentation
"""
TIMING ATTACK PREVENTION BEST PRACTICES:

1. **Always Use Constant-Time Comparison for Secrets**
   - Device IDs used for authorization
   - API keys
   - Session tokens
   - Any sensitive identifiers

2. **When to Use compare_device_ids()**
   - Checking if a device is authorized
   - Validating device permissions
   - Comparing stored vs provided device IDs
   - Any security-sensitive comparison

3. **When Regular Comparison is OK**
   - Non-sensitive data
   - Public identifiers
   - Display purposes only
   - Performance-critical non-security code

4. **Additional Security Measures**
   - Rate limiting to prevent brute force
   - Logging suspicious access patterns
   - Using secure cookies (httponly, secure, samesite)
   - Regular rotation of sensitive identifiers

5. **Testing for Timing Vulnerabilities**
   - Use statistical analysis tools
   - Test with many iterations
   - Consider network latency in real environments
   - Regular security audits

Example Implementation Pattern:

    # ❌ VULNERABLE
    if device_id == authorized_device_id:
        grant_access()

    # ✅ SECURE
    if compare_device_ids(device_id, authorized_device_id):
        grant_access()

Remember: Timing attacks are subtle but real vulnerabilities that can
lead to unauthorized access. Always use constant-time comparison for
security-critical operations.
"""

if __name__ == "__main__":
    import uvicorn

    print("Secure Device ID Comparison Example")
    print("=" * 50)
    print("\nAuthorized Device IDs for testing:")
    for device_id, info in AUTHORIZED_DEVICES.items():
        print(f"  - {device_id}: {info['name']}")
    print("\nEndpoints:")
    print("  - GET /                    : Public access")
    print("  - GET /vulnerable-admin    : Admin (vulnerable to timing)")
    print("  - GET /secure-admin        : Admin (secure comparison)")
    print("  - GET /timing-attack-demo  : Timing demonstration")
    print("  - GET /access-attempts     : View access attempts")
    print("\n" + "=" * 50)

    uvicorn.run(app, host="127.0.0.1", port=8000)
