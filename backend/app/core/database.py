from pydantic import Field, computed_field
from .base_settings import BaseAppSettings


class DatabaseSettings(BaseAppSettings):
    host: str = Field(alias="DB_HOST")
    port: int = Field(alias="DB_PORT")
    database: str = Field(alias="DB_NAME")
    username: str = Field(alias="DB_USER")
    password: str = Field(alias="DB_PASSWORD")

    @computed_field
    @property
    def url(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.username}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )