from . import backend as default_backend
from . import bindings as default_bindings
from . import frontend as default_frontend
from .loader import load_component


class _LazyComponent:
    """Lazy-load a class from grug.toml, entrypoints, or defaults."""

    def __init__(self, name, group, default_cls):
        self._name = name
        self._group = group
        self._default_cls = default_cls
        self._cls = None

    def _load(self):
        if self._cls is None:
            self._cls = load_component(self._name, self._group, self._default_cls)
        return self._cls

    def __call__(self, *args, **kwargs):
        cls = self._load()
        return cls(*args, **kwargs)

    def __getattr__(self, item):
        # Forward attribute access to the class
        cls = self._load()
        return getattr(cls, item)


Backend = _LazyComponent("backend", "grug.backends", default_backend.Backend)
Frontend = _LazyComponent("frontend", "grug.frontends", default_frontend.Frontend)
Bindings = _LazyComponent("bindings", "grug.bindings", default_bindings.Bindings)

__all__ = ["Backend", "Frontend", "Bindings"]
