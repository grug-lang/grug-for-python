from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from .parser import Type, Parameter


HostFn = Callable[..., Any]

@dataclass
class ModApiHostFn:
    description: Optional[str]
    parameters: List[Parameter]
    return_type: Optional[Type] = None
    return_type_name: Optional[str] = None
    fn_ptr: Optional[HostFn] = None


@dataclass
class ModApiExportFn:
    description: Optional[str]
    parameters: List[Parameter]


@dataclass
class ModApiEntity:
    description: Optional[str]
    export_fns: List[Tuple[str, ModApiExportFn]]

    def get_export_fn(self, name: str) -> Optional[Tuple[int, ModApiExportFn]]:
        for index, (fn_name, export_fn) in enumerate(self.export_fns):
            if fn_name == name:
                return index, export_fn
        return None


@dataclass
class ModApiClass:
    description: Optional[str]
    type: Type
    type_name: str
    methods: List[Tuple[str, ModApiHostFn]]

@dataclass
class ModApi:
    entities: Dict[str, ModApiEntity] = field(default_factory=lambda: {})
    classes: Dict[str, ModApiClass] = field(default_factory=lambda: {})
    host_fns: Dict[str, ModApiHostFn] = field(default_factory=lambda: {})

class ModApiParseContext:
    path: List[str] = field(default_factory=lambda: [])

    def push_path(self, path: str):
        self.path.append(path)

    def pop_path(self, path: str):
        self.path.remove(path)

def parse_mod_api_from_text(text: str, path: Path) -> ModApi:
    pass
