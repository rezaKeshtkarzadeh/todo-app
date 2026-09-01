from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Response
from app.core.config import settings


def _cookie_attrs(
    secure: Optional[bool] = None,
    httponly: bool = True,
    samesite: str = "lax",
    max_age: Optional[int] = None,
    expires: Optional[datetime] = None,
) -> dict:
    if secure is None:
        secure = settings.cookie.secure
    attrs = {
        "httponly": httponly,
        "secure": secure,
        "samesite": samesite,
    }
    if max_age is not None:
        attrs["max_age"] = max_age
    if expires is not None:
        attrs["expires"] = expires
    return attrs


def set_access_token_cookie(response: Response, token: str) -> None:
    max_age = settings.jwt.access_token_expire_minutes * 60
    expires = datetime.now(timezone.utc) + timedelta(seconds=max_age)
    response.set_cookie(
        key="access_token",
        value=token,
        **_cookie_attrs(httponly=True, max_age=max_age, expires=expires),
    )


def set_refresh_token_cookie(response: Response, token: str) -> None:
    max_age = settings.jwt.refresh_token_expire_days * 24 * 60 * 60
    expires = datetime.now(timezone.utc) + timedelta(seconds=max_age)
    response.set_cookie(
        key="refresh_token",
        value=token,
        **_cookie_attrs(httponly=True, max_age=max_age, expires=expires),
    )


def set_csrf_token_cookie(response: Response, token: str) -> None:
    max_age = settings.jwt.refresh_token_expire_days * 24 * 60 * 60
    expires = datetime.now(timezone.utc) + timedelta(seconds=max_age)
    response.set_cookie(
        key="csrf_token",
        value=token,
        **_cookie_attrs(httponly=False, max_age=max_age, expires=expires),
    )


def clear_all_auth_cookies(response: Response) -> None:
    attrs = _cookie_attrs()
    for key in ("access_token", "refresh_token", "csrf_token"):
        response.delete_cookie(key=key, **attrs)


def get_cookie_attrs_for_refresh() -> dict:
    return _cookie_attrs(httponly=True)


def get_cookie_attrs_for_csrf() -> dict:
    return _cookie_attrs(httponly=False)