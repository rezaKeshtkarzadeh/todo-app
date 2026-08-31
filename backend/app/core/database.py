from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    host: str = Field(default="localhost", alias="DB_HOST")
    port: int = Field(default=5432, alias="DB_PORT")
    database: str = Field(default="todoapp", alias="DB_NAME")
    username: str = Field(default="postgres", alias="DB_USER")
    password: str = Field(default="pass2000", alias="DB_PASSWORD")

    @computed_field
    @property
    def url(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.username}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )