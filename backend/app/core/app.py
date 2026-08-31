from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    name: str = Field(default="Todo App", alias="APP_NAME")
    env: str = Field(default="development", alias="ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    @property
    def is_production(self) -> bool:
        return self.env == "production"