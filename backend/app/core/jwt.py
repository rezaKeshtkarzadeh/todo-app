from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import alias


class JWTSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    secret: str = Field(default="21+iCuU=", alias="JWT_SECRET")
    algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")