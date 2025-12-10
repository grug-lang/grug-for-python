import importlib
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, cast

# TOML parser
try:
    import tomllib  # type: ignore[reportMissingTypeStubs]  # Python 3.11+
except ImportError:
    import tomli as tomllib  # type: ignore[import, reportMissingTypeStubs]


# Entry points
if sys.version_info >= (3, 10):
    from importlib.metadata import EntryPoint, entry_points
else:
    from importlib_metadata import (
        entry_points,  # type: ignore[reportUnknownVariableType]
    )
    from importlib_metadata import EntryPoint


def _load_from_config(name: str) -> Optional[Type[Any]]:
    """Return class from grug.toml in cwd, or None if not set."""
    path = Path.cwd() / "grug.toml"
    if not path.exists():
        return None

    try:
        raw_data = path.read_text()
        raw_parsed: Any = tomllib.loads(raw_data)  # type: ignore[reportUnknownMemberType]
        data: Dict[str, Any] = cast(Dict[str, Any], raw_parsed)
    except Exception:
        return None

    grug_section: Dict[str, Any] = cast(Dict[str, Any], data.get("grug", {}))
    mod_path: Optional[str] = cast(Optional[str], grug_section.get(name))

    if not mod_path:
        return None

    module_name, _, attr = str(mod_path).partition(":")
    module = importlib.import_module(module_name)
    return cast(Type[Any], getattr(module, attr))


def _load_from_entrypoints(group: str) -> Type[Any]:
    """Return first non-default entrypoint if available, otherwise default."""
    eps_container: Any = entry_points()  # Pyright can't fully type this
    eps_list: List[EntryPoint] = list(
        cast(List[EntryPoint], eps_container.select(group=group))
    )

    for ep in eps_list:
        if ep.name != "default":
            return cast(Type[Any], ep.load())

    for ep in eps_list:
        return cast(Type[Any], ep.load())

    raise RuntimeError(f"No entrypoints registered for group: {group!r}")


def load_component(name: str, group: str, default_cls: Type[Any]) -> Type[Any]:
    """Load component class with overrides."""
    cls = _load_from_config(name)
    if cls:
        return cls

    try:
        cls = _load_from_entrypoints(group)
        if cls:
            return cls
    except Exception:
        pass

    return default_cls
