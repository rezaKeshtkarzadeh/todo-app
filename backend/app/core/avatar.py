from pathlib import Path
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AvatarSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    max_bytes: int = Field(default=5242880, alias="AVATAR_MAX_BYTES")
    uploads_dir: str = Field(default="./uploads", alias="UPLOADS_DIR")

    @computed_field
    @property
    def uploads_path(self) -> Path:
        return Path(self.uploads_dir).resolve()