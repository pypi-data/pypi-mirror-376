import json
from typing import Any
from .api import APIError, APIResponse
from .middleware import Middleware
from .module import Module


class LazyJSONEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, APIError):
            return o.to_dict()
        if isinstance(o, (APIResponse, Module, Middleware)):
            return vars(o)
        return super().default(o)
