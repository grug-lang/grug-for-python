import json
import sys
import traceback
from pathlib import Path

from .frontend import Frontend, FrontendError, Parser, Tokenizer
from .serializer import Serializer

MAX_FILE_ENTITY_TYPE_LENGTH = 420


class Bindings:
    def __init__(self, mod_api_path: str):
        with open(mod_api_path) as f:
            mod_api = json.load(f)
        self.frontend = Frontend(mod_api)

    def compile_grug_file(self, grug_path: str, mod_name: str):
        """Read a file and pass its contents to the frontend."""
        try:
            text = Path(grug_path).read_text()
        except Exception as e:
            return f"Error reading file {grug_path}: {e}"

        if "/" not in grug_path:
            raise ValueError(
                f"The grug file path '{grug_path}' does not contain a '/' character"
            )

        try:
            entity_type = self.get_file_entity_type(Path(grug_path).name)
        except ValueError as e:
            return str(e)

        try:
            self.ast = self.frontend.compile_grug_file(text, mod_name, entity_type)
        except FrontendError as e:
            return str(e)
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
            return "Unhandled error"

        return None

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

    def get_file_entity_type(self, grug_filename: str) -> str:
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

        # Check length
        if len(entity_type) >= MAX_FILE_ENTITY_TYPE_LENGTH:
            raise ValueError(
                f"There are more than {MAX_FILE_ENTITY_TYPE_LENGTH} characters "
                f"in the entity type of '{grug_filename}', exceeding MAX_FILE_ENTITY_TYPE_LENGTH"
            )

        # Validate PascalCase
        self.check_custom_id_is_pascal(entity_type)

        return entity_type

    def check_custom_id_is_pascal(self, type_name: str):
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
