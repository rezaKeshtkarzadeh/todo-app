from pydantic import Field
from .base_settings import BaseAppSettings


class AppSettings(BaseAppSettings):
    name: str = Field(alias="APP_NAME")
    env: str = Field(alias="ENV")
    debug: bool = Field(alias="DEBUG")
    host: str = Field(alias="HOST")
    port: int = Field(alias="PORT")

    @property
    def is_production(self) -> bool:
        return self.env == "production"