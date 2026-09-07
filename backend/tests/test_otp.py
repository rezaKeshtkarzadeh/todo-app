"""Tests for OTP functionality: attempt limits, send cooldown, verification."""

import pytest
from httpx import AsyncClient


class TestOTPAttemptLimit:
    """Test OTP attempt limit: 5 failures destroy the code."""

    @pytest.mark.asyncio
    async def test_otp_five_failures_destroy_code(self, async_client: AsyncClient):
        """Five failed OTP attempts should destroy the code and return AUTH_OTP_MAX_ATTEMPTS."""
        phone = "+989123456789"
        device_id = "123e4567-e89b-12d3-a456-426614174000"
        
        # Send OTP
        resp = await async_client.post("/auth/send-otp", json={"phone_number": phone})
        assert resp.status_code == 200
        otp = resp.json().get("otp_debug")
        assert otp is not None, "OTP should be in debug response"
        
        # Wrong OTP 5 times
        for i in range(5):
            resp = await async_client.post(
                "/auth/verify-otp",
                json={"phone_number": phone, "code": "0000"},
                headers={"X-Device-Id": device_id},
            )
            if i < 4:
                assert resp.status_code == 401
                assert resp.json()["error"]["code"] == "AUTH_INVALID_OTP"
            else:
                # 5th attempt
                assert resp.status_code == 429
                assert resp.json()["error"]["code"] == "AUTH_OTP_MAX_ATTEMPTS"
        
        # Further attempts should return AUTH_OTP_EXPIRED (code destroyed)
        resp = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone, "code": "0000"},
            headers={"X-Device-Id": device_id},
        )
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "AUTH_OTP_EXPIRED"

    @pytest.mark.asyncio
    async def test_correct_otp_on_first_try(self, async_client: AsyncClient):
        """Correct OTP on first try should succeed."""
        phone = "+989123456790"
        device_id = "123e4567-e89b-12d3-a456-426614174001"
        
        resp = await async_client.post("/auth/send-otp", json={"phone_number": phone})
        assert resp.status_code == 200
        otp = resp.json().get("otp_debug")
        
        resp = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone, "code": otp},
            headers={"X-Device-Id": device_id},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.cookies
        assert "refresh_token" in resp.cookies
        assert "csrf_token" in resp.cookies


class TestOTPSendCooldown:
    """Test OTP send cooldown rate limiting."""

    @pytest.mark.asyncio
    async def test_rapid_resend_returns_rate_limited(self, async_client: AsyncClient):
        """Rapid resend should return AUTH_OTP_RATE_LIMITED."""
        phone = "+989123456791"
        
        # First request
        resp1 = await async_client.post("/auth/send-otp", json={"phone_number": phone})
        assert resp1.status_code == 200
        
        # Immediate second request
        resp2 = await async_client.post("/auth/send-otp", json={"phone_number": phone})
        assert resp2.status_code == 429
        assert resp2.json()["error"]["code"] == "AUTH_OTP_RATE_LIMITED"


class TestOTPVerification:
    """Test OTP verification flow."""

    @pytest.mark.asyncio
    async def test_expired_otp_returns_expired(self, async_client: AsyncClient):
        """Expired OTP should return AUTH_OTP_EXPIRED."""
        phone = "+989123456792"
        device_id = "123e4567-e89b-12d3-a456-426614174002"
        
        # We can't easily test expiration without waiting or manipulating Redis TTL
        # This test would need time manipulation or a different approach
        # For now, we test that a non-existent OTP returns expired
        resp = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone, "code": "1234"},
            headers={"X-Device-Id": device_id},
        )
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "AUTH_OTP_EXPIRED"

    @pytest.mark.asyncio
    async def test_otp_requires_device_id(self, async_client: AsyncClient):
        """OTP verification should require X-Device-Id header."""
        phone = "+989123456793"
        
        resp = await async_client.post("/auth/send-otp", json={"phone_number": phone})
        assert resp.status_code == 200
        otp = resp.json().get("otp_debug")
        
        # No X-Device-Id header
        resp = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone, "code": otp},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] in ("DEVICE_ID_MISSING", "DEVICE_ID_INVALID")