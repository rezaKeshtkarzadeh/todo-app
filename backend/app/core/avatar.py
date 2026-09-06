from pathlib import Path
from pydantic import Field, computed_field
from .base_settings import BaseAppSettings

class AvatarSettings(BaseAppSettings):
    max_bytes: int = Field(alias="AVATAR_MAX_BYTES")
    uploads_dir: str = Field(alias="UPLOADS_DIR")

    @computed_field
    @property
    def uploads_path(self) -> Path:
        return Path(self.uploads_dir).resolve()