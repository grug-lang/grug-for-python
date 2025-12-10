import importlib
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, cast

# 1. Handle TOML parser
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

# 2. Handle entry_points
if sys.version_info >= (3, 10):
    from importlib.metadata import EntryPoint, entry_points
else:
    from importlib_metadata import (
        entry_points,  # pyright: ignore[reportUnknownVariableType]
    )
    from importlib_metadata import EntryPoint


def _load_from_config(name: str) -> Optional[type]:
    """Return class from grug.toml in cwd, or None if not set."""
    path = Path.cwd() / "grug.toml"
    if not path.exists():
        return None

    try:
        data = tomllib.loads(path.read_text())
    except Exception:
        return None

    grug_section: Dict[str, Any] = data.get("grug", {})
    mod_path: Any = grug_section.get(name)

    if not mod_path:
        return None

    module_name: str
    _: str
    attr: str
    module_name, _, attr = str(mod_path).partition(":")
    module = importlib.import_module(module_name)
    return getattr(module, attr)


def _load_from_entrypoints(group: str) -> type:
    """Return first non-default entrypoint if available, otherwise default."""

    # Cast entry_points() call to Any to bypass library stub's incomplete typing,
    # then immediately cast the result back to EntryPoints for the rest of the function.
    # This avoids the "partially unknown" error on entry_points itself.
    eps_container: Any = cast(Any, entry_points)()

    # Now call select - since eps_container is typed as Any, the select call
    # won't trigger unknown parameter warnings
    eps_list: List[EntryPoint] = list(eps_container.select(group=group))

    for ep in eps_list:
        if ep.name != "default":
            return cast(Type[Any], ep.load())

    for ep in eps_list:
        return cast(Type[Any], ep.load())

    raise RuntimeError(f"No entrypoints registered for group: {group!r}")


def load_component(name: str, group: str, default_cls: Type[type]) -> type:
    """Load component class with overrides."""
    # 1. Try config file
    cls = _load_from_config(name)
    if cls:
        return cls

    # 2. Try entrypoints
    try:
        cls = _load_from_entrypoints(group)
        if cls:
            return cls
    except Exception:
        pass

    # 3. Fallback to default
    return default_cls
