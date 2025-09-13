from pydantic import BaseModel, Field, model_validator
from typing import Any, Dict, List, Optional, Union


class APIRequest(BaseModel):
    module_name: str = Field(..., alias="module")
    function: str
    args: Dict[str, Any] = Field(default_factory=dict)
    response: Optional["APIResponse"] = None

    @model_validator(mode="before")
    @classmethod
    def _validate(cls, data):
        """Validate request structure"""
        required = {"module", "function"}
        if not required.issubset(data.keys()):
            raise ValueError("Invalid request structure")
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "APIRequest":
        return cls(**data)


class APIError(BaseModel):
    code: int = 0
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"code": self.code, "message": self.message}


class APIException(Exception):
    def __init__(self, error: APIError):
        self.error = error
        super().__init__(f"APIException {error.code}: {error.message}")


class APIResponse(BaseModel):
    data: Union[Dict, List] = Field(default_factory=dict)
    error: APIError = Field(default_factory=APIError)

    @property
    def formatted(self) -> Dict[str, Any]:
        return {"data": self.data, "error": self.error.to_dict()}
