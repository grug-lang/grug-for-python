from __future__ import annotations

from typing import Callable, List, Optional, Union
from enum import Enum, auto
from dataclasses import dataclass, field

GrugValue = Union[float, bool, str, object]
HostFn = Callable[..., Optional[GrugValue]]
HostFnReg = Callable[[List["Type"]], Optional[HostFn]]

class PrimitiveType(Enum):
    VOID = auto()
    BOOL = auto()
    NUMBER = auto()
    STRING = auto()

    def __str__(self) -> str:
        # there should be no reason to print "void"
        if self == PrimitiveType.VOID: # pragma: no cover
            return "void"
        elif self == PrimitiveType.BOOL:
            return "bool"
        elif self == PrimitiveType.NUMBER:
            return "number"
        return "string"

@dataclass(frozen=True)
class ExistentialType:
    idx: int

    # we never print an existential type, but a user might
    def __str__(self): # pragma: no cover
        return f"${self.idx}"

@dataclass(frozen=True)
class IdType:
    name: str
    generics: List[Type] = field(default_factory=lambda: [])

    def __str__(self):
        if len(self.generics) != 0:
            generics = ", ".join(f"{generic}" for generic in self.generics)
            return f"{self.name}[{generics}]"
        return self.name

@dataclass(frozen=True)
class ResourceStrType:
    extension: str

    # We never print "resource" using this function
    def __str__(self): #pragma: no cover
        return "resource"

@dataclass(frozen=True)
class EntityStrType:
    entity_type: Optional[str]

    # We never print "entity" using this function
    def __str__(self): #pragma: no cover
        return "entity"

Type = Union[
    PrimitiveType,
    IdType,
    ResourceStrType,
    EntityStrType,
    ExistentialType,
]
