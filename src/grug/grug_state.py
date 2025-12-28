import json
from enum import Enum, auto
from pathlib import Path
from typing import Callable, Dict

from grug.game_fn import GameFn
from grug.grug_file import GrugFile

from .frontend import Frontend, HelperFn, OnFn, Parser, Tokenizer, VariableStatement
from .serializer import Serializer


class GrugRuntimeErrorType(Enum):
    GRUG_ON_FN_STACK_OVERFLOW = auto()
    GRUG_ON_FN_TIME_LIMIT_EXCEEDED = auto()
    GRUG_ON_FN_GAME_FN_ERROR = auto()


GrugRuntimeErrorHandler = Callable[[str, GrugRuntimeErrorType, str, str], None]


def default_runtime_error_handler(
    reason: str,
    grug_runtime_error_type: GrugRuntimeErrorType,
    on_fn_name: str,
    on_fn_path: str,
):
    assert False  # TODO: Implement


class GrugState:
    def __init__(
        self,
        *,
        runtime_error_handler: GrugRuntimeErrorHandler,
        mod_api_path: str,
        mods_dir_path: str,
        on_fn_time_limit_ms: float,
    ):
        with open(mod_api_path) as f:
            self.mod_api = json.load(f)

        self.mods_dir_path = mods_dir_path

        self.frontend = Frontend(self.mod_api)

        self.game_fns: Dict[str, GameFn] = {}

        self.next_id = 0

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

    def update(self):
        # TODO: Implement hot reloading
        pass

    # TODO: MOVE EVERYTHING BELOW HERE SOMEWHERE ELSE!

    def dump_file_to_json(self, input_grug_path: str, output_json_path: str):
        grug_text = Path(input_grug_path).read_text()

        tokens = Tokenizer(grug_text).tokenize()

        ast = Parser(tokens).parse()

        json_text = Serializer.ast_to_json_text(ast)

        Path(output_json_path).write_text(json_text)

        return False

    def generate_file_from_json(self, input_json_path: str, output_grug_path: str):
        json_text = Path(input_json_path).read_text()

        ast = json.loads(json_text)

        grug_text = Serializer.ast_to_grug(ast)

        Path(output_grug_path).write_text(grug_text)

        return False

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

    # TODO: Implement, to make this API possible:
    # mods = grug.get_mods()
    # animals_mod = mods.dirs[0]
    # labrador_file = animals_mod.files[0]
    def get_mods(self):
        assert False

    # TODO: Implement, possibly updating init_globals_fn_dispatcher_t in tests.h
    def init_globals_fn_dispatcher(self, path: str):
        assert False
