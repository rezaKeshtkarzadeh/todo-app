from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SessionSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    frontend_origin: str = Field(default="http://localhost:3000", alias="FRONTEND_ORIGIN")