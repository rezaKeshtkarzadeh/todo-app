from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID


class AvatarUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    avatar_path: str
    avatar_url: str