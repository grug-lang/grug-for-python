import importlib
import tomllib
from importlib.metadata import entry_points
from pathlib import Path


def _load_from_config(name: str):
    """Return class from grug.toml in cwd, or None if not set."""
    path = Path.cwd() / "grug.toml"
    if not path.exists():
        return None

    try:
        data = tomllib.loads(path.read_text())
    except Exception:
        return None

    mod_path = data.get("grug", {}).get(name)
    if not mod_path:
        return None

    module_name, _, attr = mod_path.partition(":")
    module = importlib.import_module(module_name)
    return getattr(module, attr)


def _load_from_entrypoints(group: str):
    """Return first non-default entrypoint if available, otherwise default."""
    eps = entry_points().select(group=group)
    eps_list = list(eps)

    for ep in eps_list:
        if ep.name != "default":
            return ep.load()

    for ep in eps_list:
        return ep.load()

    raise RuntimeError(f"No entrypoints registered for group: {group!r}")


def load_component(name: str, group: str, default_cls: type):
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
