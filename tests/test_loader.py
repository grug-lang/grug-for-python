from unittest.mock import MagicMock

import grug


def reset_lazy_components():
    """Reset all lazy-loaded components so they reload in tests."""
    grug.Backend._cls = None
    grug.Frontend._cls = None
    grug.Bindings._cls = None


def test_default_backend_loaded_without_overrides():
    """Ensure that the default Backend class loads when no overrides exist."""
    reset_lazy_components()
    backend_instance = grug.Backend()
    assert backend_instance.__class__.__name__ == "Backend"
    assert backend_instance.__class__.__module__ == "grug.backend"


def test_override_via_grug_toml(tmp_path, monkeypatch):
    """Ensure a grug.toml in cwd overrides the default component."""
    reset_lazy_components()

    # 1. Create a fake module acting as override
    override_mod = tmp_path / "fake_override.py"
    override_mod.write_text(
        "class CustomBackend:\n"
        "    def run(self): return 'override'\n"
    )

    # 2. Prepend temp dir to sys.path BEFORE changing cwd
    monkeypatch.syspath_prepend(tmp_path)
    monkeypatch.chdir(tmp_path)

    # 3. Create a grug.toml pointing to our fake module
    toml_file = tmp_path / "grug.toml"
    toml_file.write_text(
        "[grug]\nbackend = \"fake_override:CustomBackend\"\n"
    )

    # 4. Access Backend triggers lazy loading
    backend_instance = grug.Backend()
    assert backend_instance.run() == "override"
    assert backend_instance.__class__.__name__ == "CustomBackend"


def test_override_via_entrypoints(monkeypatch):
    """Test that entrypoints override defaults when no config file is present."""
    reset_lazy_components()

    # Fake entrypoint returning a dynamic backend class
    fake_ep = MagicMock()
    fake_ep.name = "custom"
    fake_ep.load.return_value = type(
        "EPBackend", (), {"run": lambda self: "ep override"}
    )

    ep_groups = {"grug.backends": [fake_ep]}

    # Patch entry_points BEFORE accessing Backend
    def mock_entry_points():
        class Wrapper:
            def select(self, group):
                return ep_groups.get(group, [])
        return Wrapper()

    monkeypatch.setattr("grug.loader.entry_points", mock_entry_points)

    # Access Backend triggers lazy load
    backend_instance = grug.Backend()
    assert backend_instance.run() == "ep override"
    assert backend_instance.__class__.__name__ == "EPBackend"
