from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class SessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    last_used_at: Optional[datetime] = None
    expires_at: datetime
    is_current: bool = False


class DeviceWithSessions(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    last_seen_at: Optional[datetime] = None
    sessions: List[SessionRead] = []


class RevokeSessionResponse(BaseModel):
    message: str


class RevokeDeviceSessionsResponse(BaseModel):
    message: str


class RevokeAllSessionsResponse(BaseModel):
    message: str