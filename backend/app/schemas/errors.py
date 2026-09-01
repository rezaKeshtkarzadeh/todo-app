from typing import Any, Optional
from pydantic import BaseModel, ConfigDict


class ApiErrorDetail(BaseModel):
    model_config = ConfigDict(extra="allow")

    code: str
    message: str
    details: Optional[dict[str, Any]] = None
    request_id: Optional[str] = None


class ApiErrorResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    error: ApiErrorDetail