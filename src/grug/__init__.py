from grug.entity import GameFnError

from .grug_state import (
    GrugRuntimeErrorHandler,
    GrugState,
    default_runtime_error_handler,
)


def init(
    *,
    runtime_error_handler: GrugRuntimeErrorHandler = default_runtime_error_handler,
    mod_api_path: str = "mod_api.json",
    mods_dir_path: str = "mods",
    on_fn_time_limit_ms: float = 100,
):
    return GrugState(
        runtime_error_handler=runtime_error_handler,
        mod_api_path=mod_api_path,
        mods_dir_path=mods_dir_path,
        on_fn_time_limit_ms=on_fn_time_limit_ms,
    )


__all__ = ["init", "GameFnError"]
