from enum import Enum
from pydantic import BaseModel
from typing import Any, Callable, Optional


class MiddlewareType(Enum):
    Request = "Request"
    Response = "Response"


class Middleware(BaseModel):
    func: Callable[[Any], Any]
    tag: Optional[str] = None
    priority: int = 0
    m_type: MiddlewareType = MiddlewareType.Request
