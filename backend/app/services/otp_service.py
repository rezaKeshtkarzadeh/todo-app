import secrets
import hashlib
from typing import Optional
from redis.asyncio import Redis

from app.core.config import settings


async def generate_otp() -> str:
    """Generate a cryptographically secure 4-digit OTP."""
    return f"{secrets.randbelow(10000):04d}"


def _hash_otp(otp: str) -> str:
    """Create a secure hash of the OTP for storage."""
    return hashlib.sha256(otp.encode()).hexdigest()


# Login OTP keys
def _otp_key(phone: str) -> str:
    return f"otp:login:{phone}"


def _attempts_key(phone: str) -> str:
    return f"otp_attempts:login:{phone}"


def _cooldown_key(phone: str) -> str:
    return f"otp_cooldown:login:{phone}"


# Phone change - current phone OTP keys
def _phone_current_otp_key(user_id: str) -> str:
    return f"otp:phone_current:{user_id}"


def _phone_current_attempts_key(user_id: str) -> str:
    return f"otp_attempts:phone_current:{user_id}"


def _phone_current_cooldown_key(user_id: str) -> str:
    return f"otp_cooldown:phone_current:{user_id}"


# Phone change - new phone OTP keys
def _phone_new_otp_key(user_id: str) -> str:
    return f"otp:phone_new:{user_id}"


def _phone_new_attempts_key(user_id: str) -> str:
    return f"otp_attempts:phone_new:{user_id}"


def _phone_new_cooldown_key(user_id: str) -> str:
    return f"otp_cooldown:phone_new:{user_id}"


# Phone change token key
def _phone_change_token_key(user_id: str) -> str:
    return f"phone_change:{user_id}"


async def check_and_set_cooldown(redis: Redis, phone: str) -> None:
    """Check if cooldown is active, set it if not. Raise if still cooling down."""
    cooldown_key = _cooldown_key(phone)
    if await redis.exists(cooldown_key):
        ttl = await redis.ttl(cooldown_key)
        raise ValueError(f"AUTH_OTP_RATE_LIMITED: Please wait {ttl} seconds before requesting a new OTP")
    await redis.set(cooldown_key, "1", ex=settings.otp.resend_cooldown_seconds)


async def store_otp(redis: Redis, phone: str, otp: str) -> None:
    """Store OTP hash with TTL and initialize attempt counter."""
    otp_hash = _hash_otp(otp)
    await redis.set(_otp_key(phone), otp_hash, ex=settings.otp.ttl_seconds)
    await redis.set(_attempts_key(phone), "0", ex=settings.otp.ttl_seconds)


async def get_otp_hash(redis: Redis, phone: str) -> Optional[str]:
    """Get stored OTP hash."""
    otp_hash = await redis.get(_otp_key(phone))
    return otp_hash.decode() if isinstance(otp_hash, bytes) else otp_hash


async def verify_otp(redis: Redis, phone: str, code: str) -> tuple[bool, Optional[str]]:
    """
    Verify OTP with constant-time comparison.
    Returns (success, error_code).
    On success, deletes OTP and counter.
    On failure, increments counter. On 5th failure, deletes OTP.
    """
    stored_hash = await get_otp_hash(redis, phone)
    if not stored_hash:
        return False, "AUTH_OTP_EXPIRED"
    
    # Constant-time comparison of hashes
    code_hash = _hash_otp(code)
    if not secrets.compare_digest(stored_hash, code_hash):
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


# Phone change - current phone OTP functions
async def check_and_set_phone_current_cooldown(redis: Redis, user_id: str) -> None:
    """Check if cooldown is active for current phone OTP, set it if not. Raise if still cooling down."""
    cooldown_key = _phone_current_cooldown_key(user_id)
    if await redis.exists(cooldown_key):
        ttl = await redis.ttl(cooldown_key)
        raise ValueError(f"AUTH_OTP_RATE_LIMITED: Please wait {ttl} seconds before requesting a new OTP")
    await redis.set(cooldown_key, "1", ex=settings.otp.resend_cooldown_seconds)


async def store_phone_current_otp(redis: Redis, user_id: str, otp: str) -> None:
    """Store OTP hash for current phone with TTL and initialize attempt counter."""
    otp_hash = _hash_otp(otp)
    await redis.set(_phone_current_otp_key(user_id), otp_hash, ex=settings.otp.ttl_seconds)
    await redis.set(_phone_current_attempts_key(user_id), "0", ex=settings.otp.ttl_seconds)


async def get_phone_current_otp_hash(redis: Redis, user_id: str) -> Optional[str]:
    """Get stored OTP hash for current phone."""
    otp_hash = await redis.get(_phone_current_otp_key(user_id))
    return otp_hash.decode() if isinstance(otp_hash, bytes) else otp_hash


async def verify_phone_current_otp(redis: Redis, user_id: str, code: str) -> tuple[bool, Optional[str]]:
    """
    Verify OTP for current phone with constant-time comparison.
    Returns (success, error_code).
    On success, deletes OTP and counter.
    On failure, increments counter. On 5th failure, deletes OTP.
    """
    stored_hash = await get_phone_current_otp_hash(redis, user_id)
    if not stored_hash:
        return False, "AUTH_OTP_EXPIRED"
    
    # Constant-time comparison of hashes
    code_hash = _hash_otp(code)
    if not secrets.compare_digest(stored_hash, code_hash):
        # Increment attempt counter
        attempts = await redis.incr(_phone_current_attempts_key(user_id))
        if attempts >= settings.otp.max_attempts:
            # Delete OTP and counter on 5th failure
            await redis.delete(_phone_current_otp_key(user_id), _phone_current_attempts_key(user_id))
            return False, "AUTH_OTP_MAX_ATTEMPTS"
        return False, "AUTH_INVALID_OTP"
    
    # Success - delete OTP and counter
    await redis.delete(_phone_current_otp_key(user_id), _phone_current_attempts_key(user_id), _phone_current_cooldown_key(user_id))
    return True, None


async def delete_phone_current_otp(redis: Redis, user_id: str) -> None:
    """Delete current phone OTP and attempt counter."""
    await redis.delete(_phone_current_otp_key(user_id), _phone_current_attempts_key(user_id), _phone_current_cooldown_key(user_id))


# Phone change - new phone OTP functions
async def check_and_set_phone_new_cooldown(redis: Redis, user_id: str) -> None:
    """Check if cooldown is active for new phone OTP, set it if not. Raise if still cooling down."""
    cooldown_key = _phone_new_cooldown_key(user_id)
    if await redis.exists(cooldown_key):
        ttl = await redis.ttl(cooldown_key)
        raise ValueError(f"AUTH_OTP_RATE_LIMITED: Please wait {ttl} seconds before requesting a new OTP")
    await redis.set(cooldown_key, "1", ex=settings.otp.resend_cooldown_seconds)


async def store_phone_new_otp(redis: Redis, user_id: str, otp: str) -> None:
    """Store OTP hash for new phone with TTL and initialize attempt counter."""
    otp_hash = _hash_otp(otp)
    await redis.set(_phone_new_otp_key(user_id), otp_hash, ex=settings.otp.ttl_seconds)
    await redis.set(_phone_new_attempts_key(user_id), "0", ex=settings.otp.ttl_seconds)


async def get_phone_new_otp_hash(redis: Redis, user_id: str) -> Optional[str]:
    """Get stored OTP hash for new phone."""
    otp_hash = await redis.get(_phone_new_otp_key(user_id))
    return otp_hash.decode() if isinstance(otp_hash, bytes) else otp_hash


async def verify_phone_new_otp(redis: Redis, user_id: str, code: str) -> tuple[bool, Optional[str]]:
    """
    Verify OTP for new phone with constant-time comparison.
    Returns (success, error_code).
    On success, deletes OTP and counter.
    On failure, increments counter. On 5th failure, deletes OTP.
    """
    stored_hash = await get_phone_new_otp_hash(redis, user_id)
    if not stored_hash:
        return False, "AUTH_OTP_EXPIRED"
    
    # Constant-time comparison of hashes
    code_hash = _hash_otp(code)
    if not secrets.compare_digest(stored_hash, code_hash):
        # Increment attempt counter
        attempts = await redis.incr(_phone_new_attempts_key(user_id))
        if attempts >= settings.otp.max_attempts:
            # Delete OTP and counter on 5th failure
            await redis.delete(_phone_new_otp_key(user_id), _phone_new_attempts_key(user_id))
            return False, "AUTH_OTP_MAX_ATTEMPTS"
        return False, "AUTH_INVALID_OTP"
    
    # Success - delete OTP and counter
    await redis.delete(_phone_new_otp_key(user_id), _phone_new_attempts_key(user_id), _phone_new_cooldown_key(user_id))
    return True, None


async def delete_phone_new_otp(redis: Redis, user_id: str) -> None:
    """Delete new phone OTP and attempt counter."""
    await redis.delete(_phone_new_otp_key(user_id), _phone_new_attempts_key(user_id), _phone_new_cooldown_key(user_id))


# Phone change token functions
async def store_phone_change_token(redis: Redis, user_id: str, token: str, new_phone: str) -> None:
    """Store phone change token bound to new phone number with TTL."""
    import json
    data = json.dumps({"token": token, "new_phone": new_phone})
    await redis.set(_phone_change_token_key(user_id), data, ex=settings.otp.phone_change_token_ttl_seconds)


async def get_phone_change_token(redis: Redis, user_id: str) -> Optional[dict]:
    """Get phone change token data."""
    data = await redis.get(_phone_change_token_key(user_id))
    if not data:
        return None
    import json
    return json.loads(data)


async def delete_phone_change_token(redis: Redis, user_id: str) -> None:
    """Delete phone change token."""
    await redis.delete(_phone_change_token_key(user_id))