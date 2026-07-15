from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, cast

from .error import GrugError, SourceSpan

HostFn = Callable[..., Any]

class PrimitiveType(Enum):
    VOID = auto()
    BOOL = auto()
    NUMBER = auto()
    STRING = auto()

@dataclass(frozen=True)
class ExistentialType:
    idx: int

@dataclass(frozen=True)
class IdType:
    name: str
    generics: List[Type] = field(default_factory=lambda: [])

@dataclass(frozen=True)
class ResourceStrType:
    extension: str

@dataclass(frozen=True)
class EntityStrType:
    entity_type: Optional[str]

Type = Union[
    PrimitiveType, 
    IdType, 
    ResourceStrType, 
    EntityStrType, 
    ExistentialType
]

@dataclass(frozen=True)
class Parameter:
    name: str
    type: Type
    name_span: SourceSpan
    type_span: SourceSpan

@dataclass
class ModApiHostFn:
    description: str
    parameters: List[Parameter]
    generics: List[str]
    return_type: Type = PrimitiveType.VOID
    fn_ptr: Optional[HostFn] = None

@dataclass
class ModApiExportFn:
    description: str
    parameters: List[Parameter]

@dataclass
class ModApiEntity:
    description: str
    export_fns: List[Tuple[str, ModApiExportFn]]

    def get_export_fn(self, name: str) -> Optional[Tuple[int, ModApiExportFn]]:
        for index, (fn_name, export_fn) in enumerate(self.export_fns):
            if fn_name == name:
                return index, export_fn
        return None


@dataclass
class ModApiClass:
    description: str
    type: Type
    methods: List[Tuple[str, ModApiHostFn]]

@dataclass
class ModApi:
    entities: Dict[str, ModApiEntity] = field(default_factory=lambda: {})
    classes: Dict[str, ModApiClass] = field(default_factory=lambda: {})
    host_fns: Dict[str, ModApiHostFn] = field(default_factory=lambda: {})

@dataclass
class ModApiParseContext:
    text: str
    file_path: Path
    path: List[str] = field(default_factory=lambda: [])

    def push_path(self, path: str) -> None:
        self.path.append(path)

    def pop_path(self) -> None:
        self.path.pop()

    def location(self) -> str:
        return f"root{''.join(self.path)}"

    def new_error(self, message: str) -> GrugError:
        location = self.location()
        error_message = f"{location} {message}"
        error_string = f"""\
  in ({self.file_path}:0:0)
Error: {error_message}
"""
        return GrugError(
            function_name="",
            file_path=self.file_path,
            source_line="",
            span=SourceSpan(0, 0),
            error_message=error_message,
            error_string=error_string,
        )

    def get_key(self, obj: Dict[str, Any], key: str) -> Any:
        self.push_path(f".{key}")
        if key not in obj:
            raise self.new_error("does not exist")
        return obj[key]

    def parse_type(self, obj: Any, used_generics: List[str]) -> Type:
        if not isinstance(obj, dict):
            raise self.new_error("is not an object")
        obj = cast(Dict[str, Any], obj)

        ty = self.get_key(obj, "name");
        if not isinstance(ty, str):
            raise self.new_error("is not a string")
        self.pop_path()

        if ty == "void":
            return PrimitiveType.VOID
        if ty == "bool":
            return PrimitiveType.BOOL
        if ty == "number":
            return PrimitiveType.NUMBER
        if ty == "string":
            return PrimitiveType.STRING
        if ty == "id":
            return IdType("id")
        if ty == "entity":
            entity_type = self.get_key(obj, "entity_type")
            if not isinstance(entity_type, str):
                raise self.new_error("is not a string")
            self.pop_path()
            return EntityStrType(entity_type if entity_type else None)
        if ty == "resource":
            resource_extension = self.get_key(obj, "resource_extension")
            if not isinstance(resource_extension, str):
                raise self.new_error("is not a string")
            self.pop_path()
            return ResourceStrType(resource_extension)
        if ty.startswith("$"):
            for index, generic in enumerate(used_generics):
                if generic == ty:
                    return ExistentialType(index)

            self.push_path(".name")
            raise self.new_error("is an undeclared generic")

        generics: List[Type]
        if "generics" in obj:
            self.push_path(".generics")
            generics_value = obj["generics"]
            if not isinstance(generics_value, list):
                raise self.new_error("is not an array")
            generics_value = cast(List[Any], generics_value)
            generics = []
            for index, generic in enumerate(generics_value):
                self.push_path(f"[{index}]")
                generics.append(self.parse_type(generic, used_generics))
                self.pop_path()
            self.pop_path()
        else:
            generics = []

        return IdType(ty, generics)

    def parse_parameters(self, parameters: Any, generics: List[str]) -> List[Parameter]:
        if not isinstance(parameters, list):
            raise self.new_error("is not an array")
        parameters = cast(List[Any], parameters)

        parsed_parameters: List[Parameter] = []
        for index, param_values in enumerate(parameters):
            self.push_path(f"[{index}]")
            if not isinstance(param_values, dict):
                raise self.new_error("is not an object")
            param_values = cast(Dict[str, Any], param_values)

            param_name = self.get_key(param_values, "name")
            if not isinstance(param_name, str):
                raise self.new_error("is not a string")
            self.pop_path()

            self.pop_path()
            self.push_path(f'["{param_name}"]')

            ty_value = self.get_key(param_values, "type")
            ty = self.parse_type(ty_value, generics)
            if ty == PrimitiveType.VOID:
                raise self.new_error("cannot be void")
            self.pop_path()

            self.pop_path()
            parsed_parameters.append(
                Parameter(
                    name=param_name,
                    type=ty,
                    name_span=SourceSpan(0, 0),
                    type_span=SourceSpan(0, 0),
                )
            )

        return parsed_parameters

    def parse_host_fn(
        self, host_fn_values: Any, parent_generics: List[str]
    ) -> ModApiHostFn:
        if not isinstance(host_fn_values, dict):
            raise self.new_error("is not an object")
        host_fn_values = cast(Dict[str, Any], host_fn_values)

        description = self.get_key(host_fn_values, "description")
        if not isinstance(description, str):
            raise self.new_error("is not a string")

        generics = list(parent_generics)
        if "used_generics" in host_fn_values:
            self.push_path(".used_generics")
            used_generics = host_fn_values["used_generics"]
            if not isinstance(used_generics, list):
                raise self.new_error("is not an array")
            used_generics = cast(List[Any], used_generics)
            for index, generic in enumerate(used_generics):
                self.push_path(f"[{index}]")
                if not isinstance(generic, str):
                    raise self.new_error("is not a string")
                generics.append(generic)
                self.pop_path()
            self.pop_path()

        if "parameters" in host_fn_values:
            self.push_path(".parameters")
            parameters = self.parse_parameters(host_fn_values["parameters"], generics)
            self.pop_path()
        else:
            parameters: List[Parameter] = []

        if "return_type" in host_fn_values:
            self.push_path(".return_type")
            return_type = self.parse_type(host_fn_values["return_type"], generics)
            if isinstance(return_type, EntityStrType):
                raise self.new_error("cannot be entity")
            if isinstance(return_type, ResourceStrType):
                raise self.new_error("cannot be resource")
            self.pop_path()
        else:
            return_type = PrimitiveType.VOID

        return ModApiHostFn(
            description=description,
            parameters=parameters,
            generics=generics,
            return_type=return_type,
            fn_ptr=None,
        )

    def validate_function(
        self,
        parameters: List[Parameter],
        return_type: Type,
        known_types: Dict[str, int],
    ) -> None:
        self.push_path(".parameters")
        for parameter in parameters:
            self.push_path(f'["{parameter.name}"]')
            self.validate_type(parameter.type, known_types)
            self.pop_path()
        self.pop_path()

        self.push_path(".return_type")
        self.validate_type(return_type, known_types)
        self.pop_path()

    def validate_type(self, ty: Type, known_types: Dict[str, int]) -> None:
        if not isinstance(ty, IdType):
            return

        self.push_path(".generics")
        num_generics = known_types.get(ty.name)

        if num_generics is not None:
            if num_generics != len(ty.generics):
                raise self.new_error(
                    f": {ty.name} was declared to have {num_generics} generics "
                    f"but here it has {len(ty.generics)}"
                )

            for index, generic in enumerate(ty.generics):
                self.push_path(f"[{index}]")
                self.validate_type(generic, known_types)
                self.pop_path()
            self.pop_path()
            return

        if len(ty.generics) != 0:
            raise self.new_error(
                f': {ty.name} was not declared in "classes", so it cannot have generics'
            )
        self.pop_path()

def parse_mod_api_from_text(text: str, path: Path) -> ModApi:
    raise NotImplementedError
