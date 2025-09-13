from abc import ABC, abstractmethod
from typing import Any, Dict
from .module import Module
from .encoder import LazyJSONEncoder


class LazyApp(ABC):
    def __init__(self) -> None:
        self.modules: Dict[str, Module] = dict()
        self.json_encoder = LazyJSONEncoder

    def register_module(self, module: Module) -> None:
        if module.name in self.modules:
            raise ValueError(f"Module {module.name} already registered")
        self.modules[module.name] = module

    def get_module(self, name: str) -> Module:
        if name not in self.modules:
            raise KeyError(f"Module {name} not found")
        return self.modules[name]

    @abstractmethod
    def handle_request(self) -> Any:
        pass
