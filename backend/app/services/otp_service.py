import secrets
from typing import Optional
from redis.asyncio import Redis

from app.core.config import settings


async def generate_otp() -> str:
    """Generate a cryptographically secure 4-digit OTP."""
    return f"{secrets.randbelow(10000):04d}"


def _otp_key(phone: str) -> str:
    return f"otp:login:{phone}"


def _attempts_key(phone: str) -> str:
    return f"otp_attempts:login:{phone}"


def _cooldown_key(phone: str) -> str:
    return f"otp_cooldown:login:{phone}"


async def check_and_set_cooldown(redis: Redis, phone: str) -> None:
    """Check if cooldown is active, set it if not. Raise if still cooling down."""
    cooldown_key = _cooldown_key(phone)
    if await redis.exists(cooldown_key):
        ttl = await redis.ttl(cooldown_key)
        raise ValueError(f"AUTH_OTP_RATE_LIMITED: Please wait {ttl} seconds before requesting a new OTP")
    await redis.set(cooldown_key, "1", ex=settings.otp.resend_cooldown_seconds)


async def store_otp(redis: Redis, phone: str, otp: str) -> None:
    """Store OTP with TTL and initialize attempt counter."""
    await redis.set(_otp_key(phone), otp, ex=settings.otp.ttl_seconds)
    await redis.set(_attempts_key(phone), "0", ex=settings.otp.ttl_seconds)


async def get_otp(redis: Redis, phone: str) -> Optional[str]:
    """Get stored OTP."""
    otp = await redis.get(_otp_key(phone))
    return otp.decode() if isinstance(otp, bytes) else otp


async def verify_otp(redis: Redis, phone: str, code: str) -> tuple[bool, Optional[str]]:
    """
    Verify OTP with constant-time comparison.
    Returns (success, error_code).
    On success, deletes OTP and counter.
    On failure, increments counter. On 5th failure, deletes OTP.
    """
    stored_otp = await get_otp(redis, phone)
    if not stored_otp:
        return False, "AUTH_OTP_EXPIRED"
    
    # Constant-time comparison
    if not secrets.compare_digest(stored_otp, code):
        # Increment attempt counter
        attempts = await redis.incr(_attempts_key(phone))
        if attempts >= settings.otp.max_attempts:
            # Delete OTP and counter on 5th failure
            await redis.delete(_otp_key(phone), _attempts_key(phone))
            return False, "AUTH_OTP_MAX_ATTEMPTS"
        return False, "AUTH_INVALID_OTP"
    
    # Success - delete OTP and counter
    await redis.delete(_otp_key(phone), _attempts_key(phone))
    return True, None


async def delete_otp(redis: Redis, phone: str) -> None:
    """Delete OTP and attempt counter."""
    await redis.delete(_otp_key(phone), _attempts_key(phone), _cooldown_key(phone))