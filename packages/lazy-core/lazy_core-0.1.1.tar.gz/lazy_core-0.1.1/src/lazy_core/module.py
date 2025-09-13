from pydantic import BaseModel, PrivateAttr
from functools import wraps
from typing import Callable, Dict, List, Optional
from .middleware import Middleware, MiddlewareType
from .api import APIRequest


class ModuleFunction(BaseModel):
    func: Callable
    tags: Optional[List[str]] = None


class Module(BaseModel):
    name: str
    _middleware: Dict[Optional[str], List[Middleware]] = PrivateAttr(
        default_factory=lambda: {None: []}
    )
    _functions: Dict[str, ModuleFunction] = PrivateAttr(default_factory=dict)
    _functions_registered: bool = PrivateAttr(default=False)

    def __init__(self, *args, **kwargs):
        if args and not kwargs.get("name"):
            kwargs["name"] = args[0]
        super().__init__(**kwargs)

    def register_middleware(self, middleware: Middleware) -> None:
        if self._functions_registered:
            raise RuntimeError("Cannot add middleware after function registration")

        key = middleware.tag or None
        self._middleware.setdefault(key, []).append(middleware)
        self._middleware[key].sort(key=lambda m: -m.priority)

    def request(self, request: "APIRequest") -> None:
        if request.function not in self._functions:
            raise KeyError(f"Function {request.function} not found")

        # Collect relevant middleware
        relevant_middleware = self._middleware[None].copy()
        function_tags = self._functions[request.function].tags or []
        for tag in function_tags:
            relevant_middleware.extend(self._middleware.get(tag, []))

        # Process request middleware
        current_request = request
        for mw in sorted(relevant_middleware, key=lambda m: m.priority, reverse=True):
            if mw.m_type == MiddlewareType.Request:
                if result := mw.func(current_request):
                    current_request = result

        # Execute function
        func = self._functions[request.function].func
        response_data = func(**current_request.args)

        # Process response middleware
        current_response = response_data
        for mw in sorted(relevant_middleware, key=lambda m: m.priority, reverse=True):
            if mw.m_type == MiddlewareType.Response:
                if result := mw.func(current_response):
                    current_response = result

        request.response = current_response

    def function(self, name: str, tags: Optional[List[str]] = None):
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            self._functions_registered = True
            self._functions[name] = ModuleFunction(func=wrapper, tags=tags)
            return wrapper

        return decorator
