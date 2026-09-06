from pydantic import Field, computed_field
from .base_settings import BaseAppSettings


class RedisSettings(BaseAppSettings):
    host: str = Field(alias="REDIS_HOST")
    port: int = Field(alias="REDIS_PORT")
    db: int = Field(alias="REDIS_DB")
    password: str = Field(alias="REDIS_PASSWORD")

    @computed_field
    @property
    def url(self) -> str:
        if self.password:
            return (
                f"redis://:{self.password}@"
                f"{self.host}:{self.port}/{self.db}"
            )
        return f"redis://{self.host}:{self.port}/{self.db}"