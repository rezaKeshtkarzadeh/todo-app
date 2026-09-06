from pydantic import Field
from .base_settings import BaseAppSettings

class SessionSettings(BaseAppSettings):
    frontend_origin: str = Field(alias="FRONTEND_ORIGIN")