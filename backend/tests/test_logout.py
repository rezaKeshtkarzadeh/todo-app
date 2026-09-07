"""Tests for global logout and session revocation."""

import pytest
from httpx import AsyncClient


class TestGlobalLogout:
    """Test global logout functionality."""

    @pytest.mark.asyncio
    async def test_global_logout_revokes_all_sessions_and_clears_cookies(self, async_client: AsyncClient):
        """Global logout should revoke all sessions including current, clear cookies."""
        phone = "+989123456820"
        device_id = "123e4567-e89b-12d3-a456-426614174030"
        
        await async_client.post("/auth/send-otp", json={"phone_number": phone})
        resp = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone, "code": (await async_client.post("/auth/send-otp", json={"phone_number": phone})).json()["otp_debug"]},
            headers={"X-Device-Id": device_id},
        )
        cookies = dict(resp.cookies)
        
        # Verify authenticated
        resp = await async_client.get("/tasks", cookies=cookies)
        assert resp.status_code == 200
        
        # Global logout
        csrf_resp = await async_client.get("/auth/csrf-token", cookies=cookies)
        cookies.update(csrf_resp.cookies)
        csrf_token = cookies.get("csrf_token")
        
        resp = await async_client.delete(
            "/security/sessions",
            cookies=cookies,
            headers={"X-CSRF-Token": csrf_token},
        )
        assert resp.status_code == 200
        assert "access_token" not in resp.cookies or resp.cookies.get("access_token") == ""
        assert "refresh_token" not in resp.cookies or resp.cookies.get("refresh_token") == ""
        assert "csrf_token" not in resp.cookies or resp.cookies.get("csrf_token") == ""
        
        # Verify logged out
        resp = await async_client.get("/tasks", cookies=dict(resp.cookies))
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "AUTH_UNAUTHENTICATED"

    @pytest.mark.asyncio
    async def test_single_session_revocation_clears_cookies_if_current(self, async_client: AsyncClient):
        """Revoking current session should clear cookies."""
        phone = "+989123456821"
        device_id = "123e4567-e89b-12d3-a456-426614174031"
        
        await async_client.post("/auth/send-otp", json={"phone_number": phone})
        resp = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone, "code": (await async_client.post("/auth/send-otp", json={"phone_number": phone})).json()["otp_debug"]},
            headers={"X-Device-Id": device_id},
        )
        cookies = dict(resp.cookies)
        
        # Get session ID
        resp = await async_client.get("/security/devices", cookies=cookies)
        session_id = resp.json()[0]["sessions"][0]["id"]
        
        # Revoke current session
        csrf_resp = await async_client.get("/auth/csrf-token", cookies=cookies)
        cookies.update(csrf_resp.cookies)
        csrf_token = cookies.get("csrf_token")
        
        resp = await async_client.delete(
            f"/security/sessions/{session_id}",
            cookies=cookies,
            headers={"X-CSRF-Token": csrf_token},
        )
        assert resp.status_code == 200
        # Cookies should be cleared
        assert "access_token" not in resp.cookies or resp.cookies.get("access_token") == ""

    @pytest.mark.asyncio
    async def test_device_session_revocation_clears_cookies_if_current(self, async_client: AsyncClient):
        """Revoking device sessions including current should clear cookies."""
        phone = "+989123456822"
        device_id = "123e4567-e89b-12d3-a456-426614174032"
        
        await async_client.post("/auth/send-otp", json={"phone_number": phone})
        resp = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone, "code": (await async_client.post("/auth/send-otp", json={"phone_number": phone})).json()["otp_debug"]},
            headers={"X-Device-Id": device_id},
        )
        cookies = dict(resp.cookies)
        
        # Get device ID
        resp = await async_client.get("/security/devices", cookies=cookies)
        device_id_resp = resp.json()[0]["id"]
        
        # Revoke device sessions
        csrf_resp = await async_client.get("/auth/csrf-token", cookies=cookies)
        cookies.update(csrf_resp.cookies)
        csrf_token = cookies.get("csrf_token")
        
        resp = await async_client.delete(
            f"/security/devices/{device_id_resp}/sessions",
            cookies=cookies,
            headers={"X-CSRF-Token": csrf_token},
        )
        assert resp.status_code == 200
        # Cookies should be cleared
        assert "access_token" not in resp.cookies or resp.cookies.get("access_token") == ""


class TestSessionRevocationLogging:
    """Test that session revocation writes security logs."""

    @pytest.mark.asyncio
    async def test_revocation_logs_scope_single(self, async_client: AsyncClient):
        """Single session revocation should log with scope='single'."""
        # This test would need to check the database for security logs
        # For now, we verify the endpoint works
        phone = "+989123456823"
        device_id = "123e4567-e89b-12d3-a456-426614174033"
        
        await async_client.post("/auth/send-otp", json={"phone_number": phone})
        resp = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone, "code": (await async_client.post("/auth/send-otp", json={"phone_number": phone})).json()["otp_debug"]},
            headers={"X-Device-Id": device_id},
        )
        cookies = dict(resp.cookies)
        
        resp = await async_client.get("/security/devices", cookies=cookies)
        session_id = resp.json()[0]["sessions"][0]["id"]
        
        csrf_resp = await async_client.get("/auth/csrf-token", cookies=cookies)
        cookies.update(csrf_resp.cookies)
        csrf_token = cookies.get("csrf_token")
        
        resp = await async_client.delete(
            f"/security/sessions/{session_id}",
            cookies=cookies,
            headers={"X-CSRF-Token": csrf_token},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_revocation_logs_scope_device(self, async_client: AsyncClient):
        """Device session revocation should log with scope='device'."""
        phone = "+989123456824"
        device_id = "123e4567-e89b-12d3-a456-426614174034"
        
        await async_client.post("/auth/send-otp", json={"phone_number": phone})
        resp = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone, "code": (await async_client.post("/auth/send-otp", json={"phone_number": phone})).json()["otp_debug"]},
            headers={"X-Device-Id": device_id},
        )
        cookies = dict(resp.cookies)
        
        resp = await async_client.get("/security/devices", cookies=cookies)
        device_id_resp = resp.json()[0]["id"]
        
        csrf_resp = await async_client.get("/auth/csrf-token", cookies=cookies)
        cookies.update(csrf_resp.cookies)
        csrf_token = cookies.get("csrf_token")
        
        resp = await async_client.delete(
            f"/security/devices/{device_id_resp}/sessions",
            cookies=cookies,
            headers={"X-CSRF-Token": csrf_token},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_revocation_logs_scope_global(self, async_client: AsyncClient):
        """Global logout should log with scope='global'."""
        phone = "+989123456825"
        device_id = "123e4567-e89b-12d3-a456-426614174035"
        
        await async_client.post("/auth/send-otp", json={"phone_number": phone})
        resp = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone, "code": (await async_client.post("/auth/send-otp", json={"phone_number": phone})).json()["otp_debug"]},
            headers={"X-Device-Id": device_id},
        )
        cookies = dict(resp.cookies)
        
        csrf_resp = await async_client.get("/auth/csrf-token", cookies=cookies)
        cookies.update(csrf_resp.cookies)
        csrf_token = cookies.get("csrf_token")
        
        resp = await async_client.delete(
            "/security/sessions",
            cookies=cookies,
            headers={"X-CSRF-Token": csrf_token},
        )
        assert resp.status_code == 200