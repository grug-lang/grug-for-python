from __future__ import annotations

from typing import TYPE_CHECKING, Callable, List, Optional, Union

if TYPE_CHECKING:
    from .parser import Type

GrugValue = Union[float, bool, str, object]
HostFn = Callable[..., Optional[GrugValue]]
HostFnReg = Callable[[List["Type"]], Optional[HostFn]]
