from typing import Union, Callable, Optional

GrugValue = Union[float, bool, str, object]
HostFn = Callable[..., Optional[GrugValue]]
