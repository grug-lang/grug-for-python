from pathlib import Path
from typing import Any, Dict, List, cast
from unittest.mock import MagicMock

import pytest

import grug


def reset_lazy_components() -> None:
    """Reset all lazy-loaded components so they reload in tests."""
    grug.Backend._cls = None  # type: ignore[attr-defined]
    grug.Frontend._cls = None  # type: ignore[attr-defined]
    grug.Bindings._cls = None  # type: ignore[attr-defined]


def test_default_backend_loaded_without_overrides() -> None:
    """Ensure that the default Backend class loads when no overrides exist."""
    reset_lazy_components()
    backend_instance = grug.Backend()
    assert backend_instance.__class__.__name__ == "Backend"
    assert backend_instance.__class__.__module__ == "grug.backend"


def test_override_via_grug_toml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ensure a grug.toml in cwd overrides the default component."""
    reset_lazy_components()

    override_mod = tmp_path / "fake_override.py"
    override_mod.write_text(
        "class CustomBackend:\n" "    def run(self): return 'override'\n"
    )

    cast(Any, monkeypatch).syspath_prepend(tmp_path)
    monkeypatch.chdir(tmp_path)

    toml_file = tmp_path / "grug.toml"
    toml_file.write_text('[grug]\nbackend = "fake_override:CustomBackend"\n')

    backend_instance = grug.Backend()
    assert backend_instance.run() == "override"
    assert backend_instance.__class__.__name__ == "CustomBackend"


def test_override_via_entrypoints(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that entrypoints override defaults when no config file is present."""
    reset_lazy_components()

    fake_ep = MagicMock()
    fake_ep.name = "custom"

    def run_method(self: Any) -> str:
        return "ep override"

    fake_ep.load.return_value = type("EPBackend", (), {"run": run_method})

    ep_groups: Dict[str, List[Any]] = {"grug.backends": [fake_ep]}

    class Wrapper:
        def select(self, group: str) -> List[Any]:
            return ep_groups.get(group, [])

    def mock_entry_points() -> Wrapper:
        return Wrapper()

    monkeypatch.setattr("grug.loader.entry_points", mock_entry_points)

    backend_instance = grug.Backend()
    assert backend_instance.run() == "ep override"
    assert backend_instance.__class__.__name__ == "EPBackend"
