import json
import sys
from enum import Enum, auto
from pathlib import Path
from typing import Callable, Dict, Sequence

from grug.game_fn import GameFn
from grug.grug_dir import GrugDir
from grug.grug_file import GrugFile
from grug.grug_package import GrugPackage

from .frontend import Frontend, HelperFn, OnFn, Parser, Tokenizer, VariableStatement
from .serializer import Serializer


class GrugRuntimeErrorType(Enum):
    STACK_OVERFLOW = 0  # Using auto() here would assign 1
    TIME_LIMIT_EXCEEDED = auto()
    GAME_FN_ERROR = auto()


GrugRuntimeErrorHandler = Callable[[str, GrugRuntimeErrorType, str, str], None]


def default_runtime_error_handler(
    reason: str,
    grug_runtime_error_type: GrugRuntimeErrorType,
    on_fn_name: str,
    on_fn_path: str,
):
    print(
        f"grug runtime error in {on_fn_name}(): {reason}, in {on_fn_path}",
        file=sys.stderr,
    )


class GrugState:
    def __init__(
        self,
        *,
        runtime_error_handler: GrugRuntimeErrorHandler,
        mod_api_path: str,
        mods_dir_path: str,
        on_fn_time_limit_ms: float,
        packages: Sequence[GrugPackage],
    ):
        self.runtime_error_handler = runtime_error_handler

        with open(mod_api_path) as f:
            self.mod_api = json.load(f)

        self.mods_dir_path = mods_dir_path

        self.on_fn_time_limit_ms = on_fn_time_limit_ms

        self.frontend = Frontend(self.mod_api)

        self.game_fns: Dict[str, GameFn] = {}
        self._add_game_fns_from_packages(packages)

        self.next_id = 0

        self.fn_depth = 0

    def _add_game_fns_from_packages(self, packages: Sequence[GrugPackage]):
        for pkg in packages:
            for game_fn in pkg.game_fns:
                if game_fn.__name__ in self.game_fns:
                    exit(
                        f"Error: Game function '{game_fn.__name__}' has already been registered, so you either registered it twice, or its grug package prefix clashes with another grug package"
                    )

                name = (
                    f"{pkg.prefix}_{game_fn.__name__}"
                    if pkg.prefix
                    else game_fn.__name__
                )
                self.game_fns[name] = game_fn

    def game_fn(self, fn: GameFn) -> GameFn:
        """Decorator for game functions."""
        self.register_game_fn(fn.__name__, fn)
        return fn

    def register_game_fn(self, name: str, fn: GameFn):
        self.game_fns[name] = fn

    def compile_grug_file(self, grug_file_relative_path: str):
        """Read a file and pass its contents to the frontend."""
        mod = Path(grug_file_relative_path).parts[0]

        grug_file_absolute_path = Path(self.mods_dir_path) / grug_file_relative_path
        text = grug_file_absolute_path.read_text()

        entity_type = self._get_file_entity_type(Path(grug_file_relative_path).name)

        ast = self.frontend.compile_grug_file(text, mod, entity_type)

        global_variables = [s for s in ast if isinstance(s, VariableStatement)]

        on_fns = {s.fn_name: s for s in ast if isinstance(s, OnFn)}

        helper_fns = {s.fn_name: s for s in ast if isinstance(s, HelperFn)}

        return GrugFile(
            grug_file_relative_path,
            mod,
            global_variables,
            on_fns,
            helper_fns,
            self.game_fns,
            self,
        )

    def _get_file_entity_type(self, grug_filename: str) -> str:
        """
        Extract and validate the entity type from a grug filename.

        Args:
            grug_filename: A filename like 'furnace-BlockEntity.grug'

        Returns:
            The entity type string (e.g., 'BlockEntity')

        Raises:
            ValueError: If the filename format is invalid
        """
        # Find the dash
        dash_index = grug_filename.find("-")

        if dash_index == -1 or dash_index + 1 >= len(grug_filename):
            raise ValueError(
                f"'{grug_filename}' is missing an entity type in its name; "
                f"use a dash to specify it, like 'ak47-gun.grug'"
            )

        # Find the period after the dash
        period_index = grug_filename.find(".", dash_index + 1)

        if period_index == -1:
            raise ValueError(f"'{grug_filename}' is missing a period in its filename")

        # Extract entity type (between dash and period)
        entity_type = grug_filename[dash_index + 1 : period_index]

        # Check if entity type is empty
        if len(entity_type) == 0:
            raise ValueError(
                f"'{grug_filename}' is missing an entity type in its name; "
                f"use a dash to specify it, like 'ak47-gun.grug'"
            )

        # Validate PascalCase
        self._check_custom_id_is_pascal(entity_type)

        return entity_type

    def _check_custom_id_is_pascal(self, type_name: str):
        """
        Validate that a custom ID type name is in PascalCase.

        Args:
            type_name: The type name to validate

        Raises:
            ValueError: If the type name is not valid PascalCase
        """
        # The first character must always be uppercase
        if not type_name[0].isupper():
            raise ValueError(
                f"'{type_name}' seems like a custom ID type, but isn't in PascalCase"
            )

        # Custom IDs only consist of uppercase, lowercase characters, and digits
        for c in type_name:
            if not (c.isupper() or c.islower() or c.isdigit()):
                raise ValueError(
                    f"'{type_name}' seems like a custom ID type, but it contains '{c}', "
                    f"which isn't uppercase/lowercase/a digit"
                )

    def compile_all_mods(self) -> GrugDir:
        """
        Compiles all grug mods under self.mods_dir_path recursively.

        Returns:
            GrugDir: Root directory representing the entire mods/ folder.
        """
        mods_path = Path(self.mods_dir_path)

        def compile_dir(current_path: Path, dir_name: str) -> GrugDir:
            grug_dir = GrugDir(name=dir_name)

            for entry in current_path.iterdir():
                if entry.is_dir():
                    subdir = compile_dir(entry, entry.name)
                    grug_dir.dirs[entry.name] = subdir
                elif entry.is_file() and entry.suffix == ".grug":
                    relative_path = entry.relative_to(mods_path).as_posix()
                    grug_file = self.compile_grug_file(relative_path)
                    grug_dir.files[relative_path] = grug_file

            return grug_dir

        root_dir = GrugDir(name="mods")
        for mod_dir in mods_path.iterdir():
            if mod_dir.is_dir():
                root_dir.dirs[mod_dir.name] = compile_dir(mod_dir, mod_dir.name)

        return root_dir

    def update(self):
        # TODO: Implement hot reloading
        pass

    # TODO: Should this method be moved out of this GrugState, so it becomes a free function?
    def dump_file_to_json(self, input_grug_path: str, output_json_path: str):
        grug_text = Path(input_grug_path).read_text()

        tokens = Tokenizer(grug_text).tokenize()

        ast = Parser(tokens).parse()

        json_text = Serializer.ast_to_json_text(ast)

        Path(output_json_path).write_text(json_text)

        return False

    # TODO: Should this method be moved out of this GrugState, so it becomes a free function?
    def generate_file_from_json(self, input_json_path: str, output_grug_path: str):
        json_text = Path(input_json_path).read_text()

        ast = json.loads(json_text)

        grug_text = Serializer.ast_to_grug(ast)

        Path(output_grug_path).write_text(grug_text)

        return False
