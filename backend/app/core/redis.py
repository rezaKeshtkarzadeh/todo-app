from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    host: str = Field(default="localhost", alias="REDIS_HOST")
    port: int = Field(default=6379, alias="REDIS_PORT")
    db: int = Field(default=0, alias="REDIS_DB")
    password: str = Field(default="", alias="REDIS_PASSWORD")

    @computed_field
    @property
    def url(self) -> str:
        if self.password:
            return (
                f"redis://:{self.password}@"
                f"{self.host}:{self.port}/{self.db}"
            )
        return f"redis://{self.host}:{self.port}/{self.db}"