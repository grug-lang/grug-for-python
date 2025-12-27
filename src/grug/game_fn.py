from typing import Callable, Optional

from grug.grug_value import GrugValue

GameFn = Callable[..., Optional[GrugValue]]
