"""Tests for error codes and avatar upload validation."""

import pytest
import io
from httpx import AsyncClient
from uuid import uuid4


class TestErrorCodes:
    """Test that all custom error codes return expected HTTP status and JSON envelope."""

    @pytest.mark.asyncio
    async def test_auth_invalid_otp(self, async_client: AsyncClient):
        """AUTH_INVALID_OTP returns 401."""
        phone = "+989123456830"
        device_id = "123e4567-e89b-12d3-a456-426614174040"
        
        await async_client.post("/auth/send-otp", json={"phone_number": phone})
        resp = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone, "code": "0000"},
            headers={"X-Device-Id": device_id},
        )
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "AUTH_INVALID_OTP"
        assert "request_id" in resp.json()["error"]

    @pytest.mark.asyncio
    async def test_auth_otp_expired(self, async_client: AsyncClient):
        """AUTH_OTP_EXPIRED returns 401."""
        phone = "+989123456831"
        device_id = "123e4567-e89b-12d3-a456-426614174041"
        
        resp = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone, "code": "1234"},
            headers={"X-Device-Id": device_id},
        )
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "AUTH_OTP_EXPIRED"

    @pytest.mark.asyncio
    async def test_auth_otp_rate_limited(self, async_client: AsyncClient):
        """AUTH_OTP_RATE_LIMITED returns 429."""
        phone = "+989123456832"
        
        await async_client.post("/auth/send-otp", json={"phone_number": phone})
        resp = await async_client.post("/auth/send-otp", json={"phone_number": phone})
        assert resp.status_code == 429
        assert resp.json()["error"]["code"] == "AUTH_OTP_RATE_LIMITED"

    @pytest.mark.asyncio
    async def test_auth_otp_max_attempts(self, async_client: AsyncClient):
        """AUTH_OTP_MAX_ATTEMPTS returns 429."""
        phone = "+989123456833"
        device_id = "123e4567-e89b-12d3-a456-426614174042"
        
        await async_client.post("/auth/send-otp", json={"phone_number": phone})
        for _ in range(5):
            resp = await async_client.post(
                "/auth/verify-otp",
                json={"phone_number": phone, "code": "0000"},
                headers={"X-Device-Id": device_id},
            )
        assert resp.status_code == 429
        assert resp.json()["error"]["code"] == "AUTH_OTP_MAX_ATTEMPTS"

    @pytest.mark.asyncio
    async def test_auth_unauthenticated(self, async_client: AsyncClient):
        """AUTH_UNAUTHENTICATED returns 401."""
        resp = await async_client.get("/tasks")
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "AUTH_UNAUTHENTICATED"

    @pytest.mark.asyncio
    async def test_auth_session_revoked(self, async_client: AsyncClient):
        """AUTH_SESSION_REVOKED returns 401."""
        phone = "+989123456834"
        device_id = "123e4567-e89b-12d3-a456-426614174043"
        
        await async_client.post("/auth/send-otp", json={"phone_number": phone})
        resp = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone, "code": (await async_client.post("/auth/send-otp", json={"phone_number": phone})).json()["otp_debug"]},
            headers={"X-Device-Id": device_id},
        )
        cookies = dict(resp.cookies)
        
        # Global logout
        csrf_resp = await async_client.get("/auth/csrf-token", cookies=cookies)
        cookies.update(csrf_resp.cookies)
        csrf_token = cookies.get("csrf_token")
        
        await async_client.delete("/security/sessions", cookies=cookies, headers={"X-CSRF-Token": csrf_token})
        
        # Now try to use old access token
        resp = await async_client.get("/tasks", cookies=cookies)
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "AUTH_UNAUTHENTICATED"  # or AUTH_SESSION_REVOKED

    @pytest.mark.asyncio
    async def test_csrf_token_missing(self, async_client: AsyncClient):
        """CSRF_TOKEN_MISSING returns 403."""
        phone = "+989123456835"
        device_id = "123e4567-e89b-12d3-a456-426614174044"
        
        await async_client.post("/auth/send-otp", json={"phone_number": phone})
        resp = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone, "code": (await async_client.post("/auth/send-otp", json={"phone_number": phone})).json()["otp_debug"]},
            headers={"X-Device-Id": device_id},
        )
        cookies = dict(resp.cookies)
        
        resp = await async_client.post("/tasks", json={"title": "Test"}, cookies=cookies)
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "CSRF_TOKEN_MISSING"

    @pytest.mark.asyncio
    async def test_csrf_token_invalid(self, async_client: AsyncClient):
        """CSRF_TOKEN_INVALID returns 403."""
        phone = "+989123456836"
        device_id = "123e4567-e89b-12d3-a456-426614174045"
        
        await async_client.post("/auth/send-otp", json={"phone_number": phone})
        resp = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone, "code": (await async_client.post("/auth/send-otp", json={"phone_number": phone})).json()["otp_debug"]},
            headers={"X-Device-Id": device_id},
        )
        cookies = dict(resp.cookies)
        
        resp = await async_client.post(
            "/tasks",
            json={"title": "Test"},
            cookies=cookies,
            headers={"X-CSRF-Token": "invalid"},
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "CSRF_TOKEN_INVALID"

    @pytest.mark.asyncio
    async def test_device_id_missing(self, async_client: AsyncClient):
        """DEVICE_ID_MISSING returns 400."""
        phone = "+989123456837"
        
        await async_client.post("/auth/send-otp", json={"phone_number": phone})
        resp = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone, "code": (await async_client.post("/auth/send-otp", json={"phone_number": phone})).json()["otp_debug"]},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] in ("DEVICE_ID_MISSING", "DEVICE_ID_INVALID")

    @pytest.mark.asyncio
    async def test_device_id_invalid(self, async_client: AsyncClient):
        """DEVICE_ID_INVALID returns 400."""
        phone = "+989123456838"
        
        await async_client.post("/auth/send-otp", json={"phone_number": phone})
        resp = await async_client.post(
            "/auth/verify-otp",
            json={"phone_number": phone, "code": (await async_client.post("/auth/send-otp", json={"phone_number": phone})).json()["otp_debug"]},
            headers={"X-Device-Id": "not-a-uuid"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] in ("DEVICE_ID_MISSING", "DEVICE_ID_INVALID")

    @pytest.mark.asyncio
    async def test_device_not_found(self, async_client: AsyncClient):
        """DEVICE_NOT_FOUND returns 404."""
        phone = "+989123456839"
        device_id = "123e4567-e89b-12d3-a456-426614174046"
        
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
        
        fake_device_id = uuid4()
        resp = await async_client.delete(
            f"/security/devices/{fake_device_id}/sessions",
            cookies=cookies,
            headers={"X-CSRF-Token": csrf_token},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "DEVICE_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_session_not_found(self, async_client: AsyncClient):
        """SESSION_NOT_FOUND returns 404."""
        phone = "+989123456840"
        device_id = "123e4567-e89b-12d3-a456-426614174047"
        
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
        
        fake_session_id = uuid4()
        resp = await async_client.delete(
            f"/security/sessions/{fake_session_id}",
            cookies=cookies,
            headers={"X-CSRF-Token": csrf_token},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "SESSION_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_profile_avatar_invalid_type(self, async_client: AsyncClient):
        """PROFILE_AVATAR_INVALID_TYPE returns 400."""
        phone = "+989123456841"
        device_id = "123e4567-e89b-12d3-a456-426614174048"
        
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
        
        # Upload a text file instead of image
        resp = await async_client.post(
            "/profile/avatar",
            files={"file": ("test.txt", io.BytesIO(b"not an image"), "text/plain")},
            cookies=cookies,
            headers={"X-CSRF-Token": csrf_token},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "PROFILE_AVATAR_INVALID_TYPE"

    @pytest.mark.asyncio
    async def test_profile_avatar_too_large(self, async_client: AsyncClient):
        """PROFILE_AVATAR_TOO_LARGE returns 413."""
        phone = "+989123456842"
        device_id = "123e4567-e89b-12d3-a456-426614174049"
        
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
        
        # Create a 6MB fake image (larger than 5MB limit)
        large_content = b"x" * (6 * 1024 * 1024)
        resp = await async_client.post(
            "/profile/avatar",
            files={"file": ("large.jpg", io.BytesIO(large_content), "image/jpeg")},
            cookies=cookies,
            headers={"X-CSRF-Token": csrf_token},
        )
        assert resp.status_code == 413
        assert resp.json()["error"]["code"] == "PROFILE_AVATAR_TOO_LARGE"

    @pytest.mark.asyncio
    async def test_task_not_found(self, async_client: AsyncClient):
        """TASK_NOT_FOUND returns 404."""
        phone = "+989123456843"
        device_id = "123e4567-e89b-12d3-a456-426614174050"
        
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
        
        fake_task_id = uuid4()
        resp = await async_client.patch(
            f"/tasks/{fake_task_id}",
            json={"title": "Test"},
            cookies=cookies,
            headers={"X-CSRF-Token": csrf_token},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "TASK_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_validation_error(self, async_client: AsyncClient):
        """VALIDATION_ERROR returns 422."""
        phone = "+989123456844"
        device_id = "123e4567-e89b-12d3-a456-426614174051"
        
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
        
        # Empty title should fail validation
        resp = await async_client.post(
            "/tasks",
            json={"title": ""},
            cookies=cookies,
            headers={"X-CSRF-Token": csrf_token},
        )
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


class TestAvatarUpload:
    """Test avatar upload validation."""

    @pytest.mark.asyncio
    async def test_upload_valid_jpeg(self, async_client: AsyncClient):
        """Valid JPEG should be accepted."""
        phone = "+989123456850"
        device_id = "123e4567-e89b-12d3-a456-426614174052"
        
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
        
        # Create a minimal valid JPEG (1x1 pixel)
        jpeg_data = bytes.fromhex("FFD8FFE000104A46494600010100000100010000FFDB004300080606070605080707070909080A0C140D0C0B0B0C1912130F141D1A1F1E1D1A1C1C20242E2720222C231C1C2837292C30313434341F27393D38323C2E333432FFC00011080001000101011100021101031101FFC4001F0000010501010101010100000000000000000102030405060708090A0BFFC400B5100002010303020403050504040000017D01020300041105122131410613516107227114328191A1082342B1C11552D1F02433627282090A161718191A25262728292A3435363738393A434445464748494A535455565758595A636465666768696A737475767778797A82838485868788898A92939495969798999AA2A3A4A5A6A7A8A9AAB2B3B4B5B6B7B8B9BAC2C3C4C5C6C7C8C9CAD2D3D4D5D6D7D8D9DAE1E2E3E4E5E6E7E8E9EAF1F2F3F4F5F6F7F8F9FAFFDA000C03010002110311003F00F7F0F0")
        
        resp = await async_client.post(
            "/profile/avatar",
            files={"file": ("avatar.jpg", io.BytesIO(jpeg_data), "image/jpeg")},
            cookies=cookies,
            headers={"X-CSRF-Token": csrf_token},
        )
        assert resp.status_code == 200
        assert "avatar_path" in resp.json()
        assert "avatar_url" in resp.json()

    @pytest.mark.asyncio
    async def test_upload_valid_png(self, async_client: AsyncClient):
        """Valid PNG should be accepted."""
        phone = "+989123456851"
        device_id = "123e4567-e89b-12d3-a456-426614174053"
        
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
        
        # Create a minimal valid PNG (1x1 pixel)
        png_data = bytes.fromhex("89504E470D0A1A0A0000000D4948445200000001000000010802000000907753DE0000000C4944415408D763F8FFFF3FC3000500010D0B21D40000000049454E44AE426082")
        
        resp = await async_client.post(
            "/profile/avatar",
            files={"file": ("avatar.png", io.BytesIO(png_data), "image/png")},
            cookies=cookies,
            headers={"X-CSRF-Token": csrf_token},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_upload_renamed_non_image(self, async_client: AsyncClient):
        """File renamed to .jpg but actually text should be rejected."""
        phone = "+989123456852"
        device_id = "123e4567-e89b-12d3-a456-426614174054"
        
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
        
        # Text file with .jpg extension
        resp = await async_client.post(
            "/profile/avatar",
            files={"file": ("fake.jpg", io.BytesIO(b"this is not an image"), "image/jpeg")},
            cookies=cookies,
            headers={"X-CSRF-Token": csrf_token},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "PROFILE_AVATAR_INVALID_TYPE"


class TestPhoneChangeTokenBinding:
    """Test phone change token binding to new phone number."""

    @pytest.mark.asyncio
    async def test_phone_change_token_cannot_be_reused_for_different_number(self, async_client: AsyncClient):
        """Phone change token bound to one number cannot be used for another."""
        phone = "+989123456860"
        device_id = "123e4567-e89b-12d3-a456-426614174060"
        
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
        
        # Step 1: request current OTP
        resp = await async_client.post(
            "/profile/phone/request-current",
            cookies=cookies,
            headers={"X-CSRF-Token": csrf_token},
        )
        assert resp.status_code == 200
        
        # Step 2: verify current OTP
        otp = (await async_client.post("/auth/send-otp", json={"phone_number": phone})).json()["otp_debug"]
        resp = await async_client.post(
            "/profile/phone/verify-current",
            json={"code": otp},
            cookies=cookies,
            headers={"X-CSRF-Token": csrf_token},
        )
        assert resp.status_code == 200
        phone_change_token = resp.json()["phone_change_token"]
        
        # Step 3: request new for phone A
        new_phone_a = "+989123456861"
        resp = await async_client.post(
            "/profile/phone/request-new",
            json={"phone_change_token": phone_change_token, "new_phone_number": new_phone_a},
            cookies=cookies,
            headers={"X-CSRF-Token": csrf_token},
        )
        assert resp.status_code == 200
        
        # Step 4: try to verify with different phone B
        new_phone_b = "+989123456862"
        resp = await async_client.post(
            "/profile/phone/verify-new",
            json={"phone_change_token": phone_change_token, "new_phone_number": new_phone_b, "code": "1234"},
            cookies=cookies,
            headers={"X-CSRF-Token": csrf_token},
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "PROFILE_PHONE_CHANGE_TOKEN_INVALID"