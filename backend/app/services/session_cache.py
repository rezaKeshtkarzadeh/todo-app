import json
from typing import Optional
from datetime import datetime, timezone, timedelta
from redis.asyncio import Redis
from uuid import UUID

from app.models.session import Session
from app.models.user import User
from app.core.config import settings


class SessionCache:
    """
    Redis-backed session cache.
    Stores session data with TTL = session expiry.
    """
    
    def __init__(self, redis: Redis):
        self.redis = redis
        self.prefix = "session:"
        self.user_sessions_prefix = "user_sessions:"
    
    def _session_key(self, session_id: UUID) -> str:
        return f"{self.prefix}{session_id}"
    
    def _user_sessions_key(self, user_id: UUID) -> str:
        return f"{self.user_sessions_prefix}{user_id}"

    @staticmethod
    def _decode_redis_id(value: str | bytes) -> str:
        return value.decode("utf-8") if isinstance(value, bytes) else str(value)
    
    async def set_session(
        self,
        session: Session,
        user: User,
        access_token: str,
        refresh_token: str,
        csrf_token: str,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """Cache session data in Redis."""
        if ttl_seconds is None:
            # session.expires_at is offset-naive, convert to aware for comparison
            now_utc = datetime.now(timezone.utc)
            expires_at_aware = session.expires_at.replace(tzinfo=timezone.utc)
            ttl_seconds = int((expires_at_aware - now_utc).total_seconds())
            if ttl_seconds <= 0:
                ttl_seconds = 1
        
        session_data = {
            "session_id": str(session.id),
            "user_id": str(session.user_id),
            "device_id": str(session.device_id),
            "token_family_id": str(session.token_family_id),
            "expires_at": session.expires_at.isoformat(),
            "last_used_at": session.last_used_at.isoformat() if session.last_used_at else None,
        }
        
        key = self._session_key(session.id)
        await self.redis.setex(key, ttl_seconds, json.dumps(session_data))
        
        # Also add to user's session set
        user_key = self._user_sessions_key(session.user_id)
        await self.redis.sadd(user_key, str(session.id))
        await self.redis.expire(user_key, ttl_seconds)
    
    async def get_session(self, session_id: UUID) -> Optional[dict]:
        """Get cached session data."""
        key = self._session_key(session_id)
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def get_session_by_access_token(self, access_token: str) -> Optional[dict]:
        """Find session by access token (requires scanning - use sparingly)."""
        # This is inefficient - in production, consider maintaining a token->session mapping
        # For now, we rely on the normal flow where we have session_id from JWT
        pass
    
    async def update_session_last_used(self, session_id: UUID) -> None:
        """Update last_used_at timestamp in cache."""
        key = self._session_key(session_id)
        data = await self.redis.get(key)
        if data:
            session_data = json.loads(data)
            session_data["last_used_at"] = datetime.now(timezone.utc).isoformat()
            # Get TTL and reset
            ttl = await self.redis.ttl(key)
            if ttl > 0:
                await self.redis.setex(key, ttl, json.dumps(session_data))
    
    async def revoke_session(self, session_id: UUID) -> None:
        """Remove session from cache."""
        key = self._session_key(session_id)
        data = await self.redis.get(key)
        if data:
            session_data = json.loads(data)
            # Remove from user's session set
            user_key = self._user_sessions_key(UUID(session_data["user_id"]))
            await self.redis.srem(user_key, str(session_id))
        await self.redis.delete(key)
    
    async def revoke_user_sessions(self, user_id: UUID) -> None:
        """Revoke all sessions for a user."""
        user_key = self._user_sessions_key(user_id)
        session_ids = await self.redis.smembers(user_key)
        for session_id in session_ids:
            session_id_str = self._decode_redis_id(session_id)
            await self.revoke_session(UUID(session_id_str))
        await self.redis.delete(user_key)

    async def get_user_session_ids(self, user_id: UUID) -> set[str]:
        """Get all active session IDs for a user."""
        user_key = self._user_sessions_key(user_id)
        session_ids = await self.redis.smembers(user_key)
        return {self._decode_redis_id(session_id) for session_id in session_ids}
    
    