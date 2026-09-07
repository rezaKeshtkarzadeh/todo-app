"""Tests for cross-user access control and CSRF protection."""

import pytest
from httpx import AsyncClient
from uuid import uuid4


class TestCrossUserAccess:
    """Test that users cannot access other users' resources."""

    @pytest.mark.asyncio
    async def test_cannot_read_another_users_task(self, async_client: AsyncClient):
        """User A cannot read User B's task - returns 404."""
        # Create User A
        phone_a = "+989123456800"
        device_a = "123e4567-e89b-12d3-a456-426614174010"
        
        await async_client.post("/auth/send-otp", json={"phone_number": phone_a})
        resp_a = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone_a, "code": (await async_client.post("/auth/send-otp", json={"phone_number": phone_a})).json()["otp_debug"]},
            headers={"X-Device-Id": device_a},
        )
        cookies_a = dict(resp_a.cookies)
        
        # Create User B
        phone_b = "+989123456801"
        device_b = "123e4567-e89b-12d3-a456-426614174011"
        
        await async_client.post("/auth/send-otp", json={"phone_number": phone_b})
        resp_b = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone_b, "code": (await async_client.post("/auth/send-otp", json={"phone_number": phone_b})).json()["otp_debug"]},
            headers={"X-Device-Id": device_b},
        )
        cookies_b = dict(resp_b.cookies)
        
        # User A creates a task
        csrf_resp = await async_client.get("/auth/csrf-token", cookies=cookies_a)
        cookies_a.update(csrf_resp.cookies)
        csrf_token = cookies_a.get("csrf_token")
        
        resp = await async_client.post(
            "/tasks",
            json={"title": "User A's task"},
            cookies=cookies_a,
            headers={"X-CSRF-Token": csrf_token},
        )
        assert resp.status_code == 201
        task_id = resp.json()["id"]
        
        # User B tries to access User A's task
        csrf_resp = await async_client.get("/auth/csrf-token", cookies=cookies_b)
        cookies_b.update(csrf_resp.cookies)
        csrf_token = cookies_b.get("csrf_token")
        
        # GET /tasks/{id} doesn't exist, but PATCH/DELETE should 404
        resp = await async_client.patch(
            f"/tasks/{task_id}",
            json={"title": "Hacked"},
            cookies=cookies_b,
            headers={"X-CSRF-Token": csrf_token},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "TASK_NOT_FOUND"
        
        resp = await async_client.delete(
            f"/tasks/{task_id}",
            cookies=cookies_b,
            headers={"X-CSRF-Token": csrf_token},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "TASK_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_cannot_revoke_another_users_session(self, async_client: AsyncClient):
        """User A cannot revoke User B's session - returns 404."""
        # Create User A
        phone_a = "+989123456802"
        device_a = "123e4567-e89b-12d3-a456-426614174012"
        
        await async_client.post("/auth/send-otp", json={"phone_number": phone_a})
        resp_a = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone_a, "code": (await async_client.post("/auth/send-otp", json={"phone_number": phone_a})).json()["otp_debug"]},
            headers={"X-Device-Id": device_a},
        )
        cookies_a = dict(resp_a.cookies)
        
        # Create User B
        phone_b = "+989123456803"
        device_b = "123e4567-e89b-12d3-a456-426614174013"
        
        await async_client.post("/auth/send-otp", json={"phone_number": phone_b})
        resp_b = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone_b, "code": (await async_client.post("/auth/send-otp", json={"phone_number": phone_b})).json()["otp_debug"]},
            headers={"X-Device-Id": device_b},
        )
        cookies_b = dict(resp_b.cookies)
        
        # User B gets their session list
        resp = await async_client.get("/security/devices", cookies=cookies_b)
        assert resp.status_code == 200
        devices = resp.json()
        assert len(devices) > 0
        session_id = devices[0]["sessions"][0]["id"]
        
        # User A tries to revoke User B's session
        csrf_resp = await async_client.get("/auth/csrf-token", cookies=cookies_a)
        cookies_a.update(csrf_resp.cookies)
        csrf_token = cookies_a.get("csrf_token")
        
        resp = await async_client.delete(
            f"/security/sessions/{session_id}",
            cookies=cookies_a,
            headers={"X-CSRF-Token": csrf_token},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "SESSION_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_cannot_revoke_another_users_device_sessions(self, async_client: AsyncClient):
        """User A cannot revoke User B's device sessions - returns 404."""
        # Create User A
        phone_a = "+989123456804"
        device_a = "123e4567-e89b-12d3-a456-426614174014"
        
        await async_client.post("/auth/send-otp", json={"phone_number": phone_a})
        resp_a = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone_a, "code": (await async_client.post("/auth/send-otp", json={"phone_number": phone_a})).json()["otp_debug"]},
            headers={"X-Device-Id": device_a},
        )
        cookies_a = dict(resp_a.cookies)
        
        # Create User B
        phone_b = "+989123456805"
        device_b = "123e4567-e89b-12d3-a456-426614174015"
        
        await async_client.post("/auth/send-otp", json={"phone_number": phone_b})
        resp_b = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone_b, "code": (await async_client.post("/auth/send-otp", json={"phone_number": phone_b})).json()["otp_debug"]},
            headers={"X-Device-Id": device_b},
        )
        cookies_b = dict(resp_b.cookies)
        
        # User B gets their device list
        resp = await async_client.get("/security/devices", cookies=cookies_b)
        assert resp.status_code == 200
        devices = resp.json()
        assert len(devices) > 0
        device_id = devices[0]["id"]
        
        # User A tries to revoke User B's device sessions
        csrf_resp = await async_client.get("/auth/csrf-token", cookies=cookies_a)
        cookies_a.update(csrf_resp.cookies)
        csrf_token = cookies_a.get("csrf_token")
        
        resp = await async_client.delete(
            f"/security/devices/{device_id}/sessions",
            cookies=cookies_a,
            headers={"X-CSRF-Token": csrf_token},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "DEVICE_NOT_FOUND"


class TestCSRFProtection:
    """Test CSRF protection on state-changing endpoints."""

    @pytest.mark.asyncio
    async def test_create_task_requires_csrf(self, async_client: AsyncClient):
        """POST /tasks should require CSRF."""
        phone = "+989123456806"
        device_id = "123e4567-e89b-12d3-a456-426614174016"
        
        await async_client.post("/auth/send-otp", json={"phone_number": phone})
        resp = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone, "code": (await async_client.post("/auth/send-otp", json={"phone_number": phone})).json()["otp_debug"]},
            headers={"X-Device-Id": device_id},
        )
        cookies = dict(resp.cookies)
        
        # No CSRF header
        resp = await async_client.post("/tasks", json={"title": "Test"}, cookies=cookies)
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "CSRF_TOKEN_MISSING"
        
        # Invalid CSRF
        resp = await async_client.post(
            "/tasks",
            json={"title": "Test"},
            cookies=cookies,
            headers={"X-CSRF-Token": "invalid"},
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "CSRF_TOKEN_INVALID"

    @pytest.mark.asyncio
    async def test_update_task_requires_csrf(self, async_client: AsyncClient):
        """PATCH /tasks/{id} should require CSRF."""
        phone = "+989123456807"
        device_id = "123e4567-e89b-12d3-a456-426614174017"
        
        await async_client.post("/auth/send-otp", json={"phone_number": phone})
        resp = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone, "code": (await async_client.post("/auth/send-otp", json={"phone_number": phone})).json()["otp_debug"]},
            headers={"X-Device-Id": device_id},
        )
        cookies = dict(resp.cookies)
        
        # Create task first (with CSRF)
        csrf_resp = await async_client.get("/auth/csrf-token", cookies=cookies)
        cookies.update(csrf_resp.cookies)
        csrf_token = cookies.get("csrf_token")
        
        resp = await async_client.post(
            "/tasks",
            json={"title": "Test task"},
            cookies=cookies,
            headers={"X-CSRF-Token": csrf_token},
        )
        task_id = resp.json()["id"]
        
        # Try to update without CSRF
        resp = await async_client.patch(
            f"/tasks/{task_id}",
            json={"title": "Hacked"},
            cookies=cookies,
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "CSRF_TOKEN_MISSING"

    @pytest.mark.asyncio
    async def test_delete_task_requires_csrf(self, async_client: AsyncClient):
        """DELETE /tasks/{id} should require CSRF."""
        phone = "+989123456808"
        device_id = "123e4567-e89b-12d3-a456-426614174018"
        
        await async_client.post("/auth/send-otp", json={"phone_number": phone})
        resp = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone, "code": (await async_client.post("/auth/send-otp", json={"phone_number": phone})).json()["otp_debug"]},
            headers={"X-Device-Id": device_id},
        )
        cookies = dict(resp.cookies)
        
        # Create task
        csrf_resp = await async_client.get("/auth/csrf-token", cookies=cookies)
        cookies.update(csrf_resp.cookies)
        csrf_token = cookies.get("csrf_token")
        
        resp = await async_client.post(
            "/tasks",
            json={"title": "Test task"},
            cookies=cookies,
            headers={"X-CSRF-Token": csrf_token},
        )
        task_id = resp.json()["id"]
        
        # Try to delete without CSRF
        resp = await async_client.delete(f"/tasks/{task_id}", cookies=cookies)
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "CSRF_TOKEN_MISSING"

    @pytest.mark.asyncio
    async def test_refresh_requires_csrf(self, async_client: AsyncClient):
        """POST /auth/refresh should require CSRF."""
        phone = "+989123456809"
        device_id = "123e4567-e89b-12d3-a456-426614174019"
        
        await async_client.post("/auth/send-otp", json={"phone_number": phone})
        resp = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone, "code": (await async_client.post("/auth/send-otp", json={"phone_number": phone})).json()["otp_debug"]},
            headers={"X-Device-Id": device_id},
        )
        cookies = dict(resp.cookies)
        
        # No CSRF
        resp = await async_client.post("/auth/refresh", cookies=cookies)
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "CSRF_TOKEN_MISSING"

    @pytest.mark.asyncio
    async def test_logout_requires_csrf(self, async_client: AsyncClient):
        """POST /auth/logout should require CSRF."""
        phone = "+989123456810"
        device_id = "123e4567-e89b-12d3-a456-426614174020"
        
        await async_client.post("/auth/send-otp", json={"phone_number": phone})
        resp = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone, "code": (await async_client.post("/auth/send-otp", json={"phone_number": phone})).json()["otp_debug"]},
            headers={"X-Device-Id": device_id},
        )
        cookies = dict(resp.cookies)
        
        # No CSRF
        resp = await async_client.post("/auth/logout", cookies=cookies)
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "CSRF_TOKEN_MISSING"

    @pytest.mark.asyncio
    async def test_session_revocation_requires_csrf(self, async_client: AsyncClient):
        """DELETE /security/sessions/{id} should require CSRF."""
        phone = "+989123456811"
        device_id = "123e4567-e89b-12d3-a456-426614174021"
        
        await async_client.post("/auth/send-otp", json={"phone_number": phone})
        resp = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone, "code": (await async_client.post("/auth/send-otp", json={"phone_number": phone})).json()["otp_debug"]},
            headers={"X-Device-Id": device_id},
        )
        cookies = dict(resp.cookies)
        
        # Get a session ID
        resp = await async_client.get("/security/devices", cookies=cookies)
        session_id = resp.json()[0]["sessions"][0]["id"]
        
        # No CSRF
        resp = await async_client.delete(f"/security/sessions/{session_id}", cookies=cookies)
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "CSRF_TOKEN_MISSING"

    @pytest.mark.asyncio
    async def test_global_logout_requires_csrf(self, async_client: AsyncClient):
        """DELETE /security/sessions should require CSRF."""
        phone = "+989123456812"
        device_id = "123e4567-e89b-12d3-a456-426614174022"
        
        await async_client.post("/auth/send-otp", json={"phone_number": phone})
        resp = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone, "code": (await async_client.post("/auth/send-otp", json={"phone_number": phone})).json()["otp_debug"]},
            headers={"X-Device-Id": device_id},
        )
        cookies = dict(resp.cookies)
        
        # No CSRF
        resp = await async_client.delete("/security/sessions", cookies=cookies)
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "CSRF_TOKEN_MISSING"

    @pytest.mark.asyncio
    async def test_avatar_upload_requires_csrf(self, async_client: AsyncClient):
        """POST /profile/avatar should require CSRF."""
        phone = "+989123456813"
        device_id = "123e4567-e89b-12d3-a456-426614174023"
        
        await async_client.post("/auth/send-otp", json={"phone_number": phone})
        resp = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone, "code": (await async_client.post("/auth/send-otp", json={"phone_number": phone})).json()["otp_debug"]},
            headers={"X-Device-Id": device_id},
        )
        cookies = dict(resp.cookies)
        
        # No CSRF
        import io
        resp = await async_client.post(
            "/profile/avatar",
            files={"file": ("test.jpg", io.BytesIO(b"fake image"), "image/jpeg")},
            cookies=cookies,
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "CSRF_TOKEN_MISSING"

    @pytest.mark.asyncio
    async def test_phone_change_requires_csrf(self, async_client: AsyncClient):
        """Phone change endpoints should require CSRF."""
        phone = "+989123456814"
        device_id = "123e4567-e89b-12d3-a456-426614174024"
        
        await async_client.post("/auth/send-otp", json={"phone_number": phone})
        resp = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone, "code": (await async_client.post("/auth/send-otp", json={"phone_number": phone})).json()["otp_debug"]},
            headers={"X-Device-Id": device_id},
        )
        cookies = dict(resp.cookies)
        
        # request-current without CSRF
        resp = await async_client.post("/profile/phone/request-current", cookies=cookies)
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "CSRF_TOKEN_MISSING"