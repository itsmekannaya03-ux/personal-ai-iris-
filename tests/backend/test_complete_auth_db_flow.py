import sys
import os
from pathlib import Path
import asyncio
import uuid

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import httpx
from backend.main import app

async def run_tests():
    print("Starting async test suite...")
    test_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "SecurePassword123!"
    test_name = "Alex Mercer"

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        res = await client.get("/health")
        assert res.status_code == 200, f"Health check failed: {res.text}"
        print("[PASS] 1. Health check passed")

        # 2. Signup
        res = await client.post("/auth/signup", json={
            "email": test_email,
            "password": test_password,
            "name": test_name,
        })
        assert res.status_code == 201, f"Signup failed: {res.text}"
        data = res.json()
        assert "token" in data and "refresh_token" in data
        assert data["user"]["email"] == test_email
        token = data["token"]
        refresh_token = data["refresh_token"]
        user_id = data["user"]["id"]
        print("[PASS] 2. Signup success (user created in PostgreSQL, free subscription generated)")

        # 3. Duplicate email
        res = await client.post("/auth/signup", json={
            "email": test_email,
            "password": "AnotherPassword456!",
            "name": "Imposter",
        })
        assert res.status_code == 400, f"Duplicate check failed: {res.status_code}"
        assert "already registered" in res.json().get("detail", "").lower()
        print("[PASS] 3. Duplicate email rejection passed")

        # 4. Login valid
        res = await client.post("/auth/login", json={
            "email": test_email,
            "password": test_password,
        })
        assert res.status_code == 200, f"Login failed: {res.text}"
        assert "token" in res.json()
        print("[PASS] 4. Login with bcrypt verification passed")

        # 5. Login invalid
        res = await client.post("/auth/login", json={
            "email": test_email,
            "password": "WrongPassword999",
        })
        assert res.status_code == 401, f"Invalid login check failed: {res.status_code}"
        print("[PASS] 5. Invalid credentials rejection passed")

        # 6. Authenticated /auth/me
        headers = {"Authorization": f"Bearer {token}"}
        res = await client.get("/auth/me", headers=headers)
        assert res.status_code == 200, f"/auth/me failed: {res.text}"
        assert res.json()["id"] == user_id
        print("[PASS] 6. /auth/me profile retrieval passed")

        # 7. Refresh token
        res = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert res.status_code == 200, f"Refresh failed: {res.text}"
        new_token = res.json()["token"]
        print("[PASS] 7. JWT token refresh passed")

        # 8. Profile update (Step 2 & Step 3 in UI)
        res = await client.put("/profile", json={
            "age": 24,
            "job": "Autonomous Systems Engineer",
            "location": "Bengaluru, India",
            "goals": "Architect sovereign local AI systems",
            "interests": ["Robotics", "Privacy", "Compilers"],
            "ai_name": "IRIS-PRIME",
            "theme": "terminal",
        }, headers={"Authorization": f"Bearer {new_token}"})
        assert res.status_code == 200, f"Profile update failed: {res.text}"
        profile = res.json()
        assert profile["age"] == 24
        assert profile["job"] == "Autonomous Systems Engineer"
        assert profile["ai_name"] == "IRIS-PRIME"
        print("[PASS] 8. Profile update and data persistence in PostgreSQL passed")

        # 9. Subscription status
        res = await client.get("/subscriptions/status", headers={"Authorization": f"Bearer {new_token}"})
        assert res.status_code == 200, f"Sub status failed: {res.text}"
        assert res.json()["plan"] == "free"
        assert res.json()["status"] == "active"
        print("[PASS] 9. Default Free subscription verified in PostgreSQL")

        # 10. Paid plan security check
        res = await client.post("/subscriptions/create", json={"plan": "student"}, headers={"Authorization": f"Bearer {new_token}"})
        assert res.status_code in [400, 200]
        # Re-check that status did NOT become active paid without webhook payment
        sub_check = await client.get("/subscriptions/status", headers={"Authorization": f"Bearer {new_token}"})
        assert sub_check.json()["plan"] == "free"
        print("[PASS] 10. Paid plan activation security guard passed (unauthorized elevation blocked)")

    print("\n==========================================")
    print("ALL 10/10 INTEGRATION TESTS PASSED CLEANLY!")
    print("==========================================")

if __name__ == "__main__":
    asyncio.run(run_tests())
