from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime


class TaskCreate(BaseModel):
    title: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Task title cannot be empty.")
        if len(v) > 256:
            raise ValueError("Task title cannot exceed 256 characters.")
        return v


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    is_done: Optional[bool] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Task title cannot be empty.")
            if len(v) > 256:
                raise ValueError("Task title cannot exceed 256 characters.")
        return v

    @field_validator("is_done")
    @classmethod
    def validate_is_done(cls, v: Optional[bool]) -> Optional[bool]:
        return v


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    is_done: bool
    created_at: datetime
    updated_at: datetime