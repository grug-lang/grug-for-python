import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any


class Serializer:
    # TODO: Document
    @staticmethod
    def ast_to_json_text(ast: Any):
        def json_serializer(obj: Any):
            # Check if it is a dataclass AND an instance (not the class itself)
            if is_dataclass(obj) and not isinstance(obj, type):
                # Exclude the 'result' key
                return asdict(
                    obj,
                    dict_factory=lambda items: {
                        k: v for k, v in items if k != "result"
                    },
                )

            if isinstance(obj, Enum):
                return obj.name

            raise TypeError(f"Type {type(obj)} is not JSON serializable")

        json_text = json.dumps(ast, default=json_serializer, indent=4)
        return json_text

    # TODO: Document
    @staticmethod
    def ast_to_grug(ast: Any):
        return ""  # TODO: Unhardcode
