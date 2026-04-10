"""Tests for coverage of previously uncovered lines."""
import json
import os
import tempfile
from typing import Any

import pytest

import grug
from grug.grug_state import default_runtime_error_handler
from grug.parser import EntityExpr, ResourceExpr
from grug.serializer import Serializer


class TestGrugStateModApiValidation:
    """Tests for mod_api.json validation error paths."""

    def test_invalid_json_root_not_dict(self):
        """Test line 94: JSON root must be a dict."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_api_path = os.path.join(tmpdir, "mod_api.json")
            os.makedirs(os.path.join(tmpdir, "mods"), exist_ok=True)

            with open(mod_api_path, "w") as f:
                json.dump(["not", "a", "dict"], f)

            with pytest.raises(SystemExit) as exc_info:
                grug.init(
                    runtime_error_handler=default_runtime_error_handler,
                    mod_api_path=mod_api_path,
                    mods_dir_path=os.path.join(tmpdir, "mods"),
                )
            assert "must be an object" in str(exc_info.value)

    def test_entity_not_dict(self):
        """Test Line 113: entity must be a JSON object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_api_path = os.path.join(tmpdir, "mod_api.json")
            os.makedirs(os.path.join(tmpdir, "mods"), exist_ok=True)

            mod_api: dict[str, Any] = {
                "entities": {
                    "Dog": "not a dict"
                },
                "game_functions": {}
            }

            with open(mod_api_path, "w") as f:
                json.dump(mod_api, f)

            with pytest.raises(SystemExit) as exc_info:
                grug.init(
                    runtime_error_handler=default_runtime_error_handler,
                    mod_api_path=mod_api_path,
                    mods_dir_path=os.path.join(tmpdir, "mods"),
                )
            assert "must be a JSON object" in str(exc_info.value)

    def test_entity_without_on_functions(self):
        """Test Line 120: entity without on_functions (should continue without error)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_api_path = os.path.join(tmpdir, "mod_api.json")
            os.makedirs(os.path.join(tmpdir, "mods"), exist_ok=True)
            
            mod_api = {
                "entities": {
                    "Dog": {
                        "description": "A dog without on_functions"
                    }
                },
                "game_functions": {}
            }
            
            with open(mod_api_path, "w") as f:
                json.dump(mod_api, f)
            
            # Should not raise
            state = grug.init(
                runtime_error_handler=default_runtime_error_handler,
                mod_api_path=mod_api_path,
                mods_dir_path=os.path.join(tmpdir, "mods"),
            )
            assert state is not None

    def test_game_functions_not_dict(self):
        """Test Line 130: game_functions must be a dict."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_api_path = os.path.join(tmpdir, "mod_api.json")
            os.makedirs(os.path.join(tmpdir, "mods"), exist_ok=True)

            mod_api: dict[str, Any] = {
                "entities": {},
                "game_functions": ["not", "a", "dict"]
            }

            with open(mod_api_path, "w") as f:
                json.dump(mod_api, f)

            with pytest.raises(SystemExit) as exc_info:
                grug.init(
                    runtime_error_handler=default_runtime_error_handler,
                    mod_api_path=mod_api_path,
                    mods_dir_path=os.path.join(tmpdir, "mods"),
                )
            assert "must be a JSON object" in str(exc_info.value)

    def test_unsorted_entities(self):
        """Test Lines 149-155: entities must be sorted alphabetically."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_api_path = os.path.join(tmpdir, "mod_api.json")
            os.makedirs(os.path.join(tmpdir, "mods"), exist_ok=True)

            # 'Zebra' comes before 'Apple' alphabetically - wrong order
            mod_api = {
                "entities": {
                    "Zebra": {"description": "Zebra"},
                    "Apple": {"description": "Apple"}
                },
                "game_functions": {}
            }

            with open(mod_api_path, "w") as f:
                json.dump(mod_api, f)

            with pytest.raises(SystemExit) as exc_info:
                grug.init(
                    runtime_error_handler=default_runtime_error_handler,
                    mod_api_path=mod_api_path,
                    mods_dir_path=os.path.join(tmpdir, "mods"),
                )
            assert "must be sorted alphabetically" in str(exc_info.value)

    def test_unsorted_on_functions(self):
        """Test Lines 164-171: on_functions must be sorted alphabetically."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_api_path = os.path.join(tmpdir, "mod_api.json")
            os.makedirs(os.path.join(tmpdir, "mods"), exist_ok=True)

            mod_api: dict[str, Any] = {
                "entities": {
                    "Dog": {
                        "description": "A dog",
                        "on_functions": {
                            "zzz_bark": {"description": "Bark"},
                            "aaa_eat": {"description": "Eat"}
                        }
                    }
                },
                "game_functions": {}
            }

            with open(mod_api_path, "w") as f:
                json.dump(mod_api, f)

            with pytest.raises(SystemExit) as exc_info:
                grug.init(
                    runtime_error_handler=default_runtime_error_handler,
                    mod_api_path=mod_api_path,
                    mods_dir_path=os.path.join(tmpdir, "mods"),
                )
            assert "must be sorted alphabetically" in str(exc_info.value)

    def test_unsorted_game_functions(self):
        """Test Lines 178-184: game_functions must be sorted alphabetically."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_api_path = os.path.join(tmpdir, "mod_api.json")
            os.makedirs(os.path.join(tmpdir, "mods"), exist_ok=True)

            mod_api = {
                "entities": {},
                "game_functions": {
                    "zzz_function": {"description": "Z function"},
                    "aaa_function": {"description": "A function"}
                }
            }

            with open(mod_api_path, "w") as f:
                json.dump(mod_api, f)

            with pytest.raises(SystemExit) as exc_info:
                grug.init(
                    runtime_error_handler=default_runtime_error_handler,
                    mod_api_path=mod_api_path,
                    mods_dir_path=os.path.join(tmpdir, "mods"),
                )
            assert "must be sorted alphabetically" in str(exc_info.value)


class TestCompileAllMods:
    """Tests for compile_all_mods with nested directories."""

    def test_compile_all_mods_with_nested_dirs(self):
        """Test Lines 320-321: compile_all_mods iterates nested directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_api_path = os.path.join(tmpdir, "mod_api.json")
            mods_dir = os.path.join(tmpdir, "mods")
            
            # Create nested directory structure
            os.makedirs(os.path.join(mods_dir, "mod_a", "subdir"), exist_ok=True)
            os.makedirs(os.path.join(mods_dir, "mod_b"), exist_ok=True)
            
            # Create .grug files (must follow naming convention: name-Entity.grug)
            for path in [
                os.path.join(mods_dir, "mod_a", "file1-Dog.grug"),
                os.path.join(mods_dir, "mod_a", "subdir", "file2-Dog.grug"),
                os.path.join(mods_dir, "mod_b", "file3-Dog.grug"),
            ]:
                with open(path, "w") as f:
                    f.write("")  # empty grug file
            
            # Create minimal mod_api.json
            mod_api: dict[str, Any] = {
                "entities": {
                    "Dog": {
                        "description": "A dog",
                        "on_functions": {}
                    }
                },
                "game_functions": {}
            }
            with open(mod_api_path, "w") as f:
                json.dump(mod_api, f)
            
            state = grug.init(
                runtime_error_handler=default_runtime_error_handler,
                mod_api_path=mod_api_path,
                mods_dir_path=mods_dir,
            )
            
            # This should exercise lines 320-321
            result = state.compile_all_mods()
            assert result is not None
            assert "mod_a" in result.dirs
            assert "mod_b" in result.dirs


class TestSerializerExprTypes:
    """Tests for serializer with ResourceExpr and EntityExpr."""

    def test_resource_expr_serialization(self):
        """Test Line 61: ResourceExpr serialization."""
        expr = ResourceExpr(string="path/to/resource.txt")
        result = Serializer._serialize_expr(expr)  # type: ignore[reportPrivateUsage]

        assert result["type"] == "RESOURCE_EXPR"
        assert result["str"] == "path/to/resource.txt"

    def test_entity_expr_serialization(self):
        """Test Line 63: EntityExpr serialization."""
        expr = EntityExpr(string="SomeEntity")
        result = Serializer._serialize_expr(expr)  # type: ignore[reportPrivateUsage]

        assert result["type"] == "ENTITY_EXPR"
        assert result["str"] == "SomeEntity"
