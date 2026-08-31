from functools import lru_cache

from .app import AppSettings
from .database import DatabaseSettings
from .redis import RedisSettings
from .jwt import JWTSettings
from .cookie import CookieSettings
from .otp import OTPSettings
from .session import SessionSettings
from .avatar import AvatarSettings


class Settings:
    def __init__(self):
        self.app = AppSettings()
        self.database = DatabaseSettings()
        self.redis = RedisSettings()
        self.jwt = JWTSettings()
        self.cookie = CookieSettings()
        self.otp = OTPSettings()
        self.session = SessionSettings()
        self.avatar = AvatarSettings()


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()