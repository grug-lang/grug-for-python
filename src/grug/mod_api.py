from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, cast

from .error import GrugError, SourceSpan
from .parser import Parameter
from .types import (
    EntityStrType,
    ExistentialType,
    HostFn,
    HostFnReg,
    IdType,
    PrimitiveType,
    ResourceStrType,
    Type,
)


@dataclass
class ModApiGeneric:
    name: str
    constraints: List[str]


@dataclass
class ModApiConstraintImplementor:
    generics: List[ModApiGeneric]
    type: Type


@dataclass
class ModApiConstraint:
    description: str
    implementors: List[ModApiConstraintImplementor]


@dataclass
class ModApiHostFn:
    description: str
    parameters: List[Parameter]
    generics: List[ModApiGeneric]
    return_type: Type
    fn_ptr: Optional[HostFn] = None
    generic_reg_fn: Optional[HostFnReg] = None


@dataclass
class ModApiExportFn:
    description: str
    parameters: List[Parameter]


@dataclass
class ModApiEntity:
    description: str
    export_fns: Dict[str, ModApiExportFn]
    static_methods: Dict[str, ModApiHostFn]


@dataclass
class ModApiClass:
    description: str
    type: Type
    generics: List[ModApiGeneric]
    methods: Dict[str, ModApiHostFn]
    static_methods: Dict[str, ModApiHostFn]


@dataclass
class ModApi:
    entities: Dict[str, ModApiEntity]
    classes: Dict[str, ModApiClass]
    host_fns: Dict[str, ModApiHostFn]
    constraints: Dict[str, ModApiConstraint]

    def static_methods_of(self, type_name: str) -> Optional[Dict[str, ModApiHostFn]]:
        """The static functions declared on a class or entity, or None if the
        name does not belong to either."""
        mod_api_class = self.classes.get(type_name)
        if mod_api_class is not None:
            return mod_api_class.static_methods

        entity = self.entities.get(type_name)
        if entity is not None:
            return entity.static_methods

        return None

    def declares_type(self, type_name: str) -> bool:
        return type_name in self.classes or type_name in self.entities

    @staticmethod
    def new_registration_error(message: str) -> GrugError:
        error_string = f"""\
Error: {message}
"""
        return GrugError(
            function_name="",
            file_path=Path(""),
            source_line="",
            span=SourceSpan(0, 0),
            error_message=message,
            error_string=error_string,
        )

    def register_fn(self, class_name: Optional[str], fn_name: str, ptr: HostFn) -> None:
        if class_name is not None:
            kind, host_fn_data = self._lookup_on_type(class_name, fn_name)

            if host_fn_data.fn_ptr is not None:
                raise self.new_registration_error(
                    f"Host {kind} named '{fn_name}' on class '{class_name}' has already been registered"
                )

            host_fn_data.fn_ptr = ptr
            return

        host_fn_data = self.host_fns.get(fn_name)
        if host_fn_data is None:
            raise self.new_registration_error(
                f"Host function named '{fn_name}' is not found in mod_api.json"
            )

        if host_fn_data.fn_ptr is not None:
            raise self.new_registration_error(
                f"Host function named '{fn_name}' has already been registered"
            )

        host_fn_data.fn_ptr = ptr

    def register_generic_fn(
        self, class_name: Optional[str], fn_name: str, ptr: HostFnReg
    ) -> None:
        if class_name is not None:
            kind, host_fn_data = self._lookup_on_type(class_name, fn_name)

            if len(host_fn_data.generics) == 0:
                raise self.new_registration_error(
                    f"{kind.capitalize()} {class_name}.{fn_name} is not generic"
                )

            if host_fn_data.generic_reg_fn is not None:
                raise self.new_registration_error(
                    f"{kind.capitalize()} {class_name}.{fn_name} has already been registered"
                )

            host_fn_data.generic_reg_fn = ptr
            return

        host_fn_data = self.host_fns.get(fn_name)
        if host_fn_data is None:
            raise self.new_registration_error(
                f"Host function '{fn_name}' is not found in mod_api.json"
            )

        if len(host_fn_data.generics) == 0:
            raise self.new_registration_error(
                f"Host function '{fn_name}' is not generic"
            )

        if host_fn_data.generic_reg_fn is not None:
            raise self.new_registration_error(
                f"Host function '{fn_name}' has already been registered"
            )

        host_fn_data.generic_reg_fn = ptr

    def _lookup_on_type(self, type_name: str, fn_name: str) -> Tuple[str, ModApiHostFn]:
        """The method or static method `type_name.fn_name` names, and which of
        the two it is.

        A name identifies at most one of them, because a class or entity that
        declares both is rejected when mod_api.json is parsed. That is what lets
        registering one take a name and nothing else."""
        mod_api_class = self.classes.get(type_name)
        if mod_api_class is not None:
            host_fn_data = mod_api_class.methods.get(fn_name)
            if host_fn_data is not None:
                return "method", host_fn_data

        static_methods = self.static_methods_of(type_name)
        if static_methods is None:
            raise self.new_registration_error(
                f"Class with name '{type_name}' is not found in mod_api.json"
            )

        host_fn_data = static_methods.get(fn_name)
        if host_fn_data is None:
            raise self.new_registration_error(
                f"Class with name '{type_name}' does not contain method with name '{fn_name}'"
            )

        return "static method", host_fn_data


@dataclass
class ModApiParseContext:
    text: str
    file_path: Path
    path: List[str] = field(default_factory=lambda: [])
    constraint_names: List[str] = field(default_factory=lambda: [])

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
  in ({self.file_path})
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

    def get_list(self, obj: Dict[str, Any], key: str) -> List[Any]:
        val = self.get_key(obj, key)
        if not isinstance(val, list):
            raise self.new_error("is not a list")
        return cast(List[Any], val)

    def get_string(self, obj: Dict[str, Any], key: str) -> str:
        self.push_path(f".{key}")
        if key not in obj:
            raise self.new_error("does not exist")
        val = obj[key]
        if not isinstance(val, str):
            raise self.new_error("is not a string")
        return val

    def get_key(self, obj: Dict[str, Any], key: str) -> Any:
        self.push_path(f".{key}")
        if key not in obj:
            raise self.new_error("does not exist")
        return obj[key]

    def parse_used_generics(self, obj: Dict[str, Any]) -> List[ModApiGeneric]:
        generics: List[ModApiGeneric] = []
        if "used_generics" not in obj:
            return generics

        for index, generic in enumerate(self.get_list(obj, "used_generics")):
            self.push_path(f"[{index}]")
            if not isinstance(generic, dict):
                raise self.new_error("is not an object")
            generic = cast(Dict[str, Any], generic)
            name = self.get_string(generic, "name")
            if not name.startswith("$"):
                raise self.new_error("does not begin with '$'")
            self.pop_path()

            constraints: List[str] = []
            if "constraints" in generic:
                for constraint_index, constraint in enumerate(
                    self.get_list(generic, "constraints")
                ):
                    self.push_path(f"[{constraint_index}]")
                    if not isinstance(constraint, str):
                        raise self.new_error("is not a string")
                    self.pop_path()
                    self.push_path(f'["{constraint}"]')
                    if constraint not in self.constraint_names:
                        raise self.new_error("is an unknown constraint")
                    constraints.append(constraint)
                    self.pop_path()
                self.pop_path()

            generics.append(ModApiGeneric(name, constraints))
            self.pop_path()
        self.pop_path()
        return generics

    def parse_type(self, obj: Any, used_generics: List[ModApiGeneric]) -> Type:
        if not isinstance(obj, dict):
            raise self.new_error("is not an object")
        obj = cast(Dict[str, Any], obj)

        ty = self.get_string(obj, "name")
        self.pop_path()

        if ty == "bool":
            return PrimitiveType.BOOL
        if ty == "number":
            return PrimitiveType.NUMBER
        if ty == "string":
            return PrimitiveType.STRING
        if ty == "entity":
            entity_type = self.get_string(obj, "entity_type")
            self.pop_path()
            return EntityStrType(entity_type if entity_type else None)
        if ty == "resource":
            resource_extension = self.get_string(obj, "resource_extension")
            self.pop_path()
            return ResourceStrType(resource_extension)
        if ty.startswith("$"):
            for index, generic in enumerate(used_generics):
                if generic.name == ty:
                    return ExistentialType(index)

            self.push_path(".name")
            raise self.new_error("is an undeclared generic")

        generics: List[Type]
        if "generics" in obj:
            generics_value = self.get_list(obj, "generics")
            generics = []
            for index, generic in enumerate(generics_value):
                self.push_path(f"[{index}]")
                generics.append(self.parse_type(generic, used_generics))
                self.pop_path()
            self.pop_path()
        else:
            generics = []

        return IdType(ty, generics)

    def parse_parameters(
        self, parameters: List[Any], generics: List[ModApiGeneric]
    ) -> List[Parameter]:
        parsed_parameters: List[Parameter] = []
        for index, param_values in enumerate(parameters):
            self.push_path(f"[{index}]")
            if not isinstance(param_values, dict):
                raise self.new_error("is not an object")
            param_values = cast(Dict[str, Any], param_values)

            param_name = self.get_string(param_values, "name")
            self.pop_path()

            self.pop_path()
            self.push_path(f'["{param_name}"]')

            ty_value = self.get_key(param_values, "type")
            ty = self.parse_type(ty_value, generics)
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
        self, host_fn_values: Dict[str, Any], parent_generics: List[ModApiGeneric]
    ) -> ModApiHostFn:
        description = self.get_string(host_fn_values, "description")
        self.pop_path()

        generics = (
            self.parse_used_generics(host_fn_values)
            if "used_generics" in host_fn_values
            else list(parent_generics)
        )

        if "parameters" in host_fn_values:
            parameters = self.parse_parameters(
                self.get_list(host_fn_values, "parameters"), generics
            )
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

    def parse_static_methods(
        self, owner_values: Dict[str, Any], parent_generics: List[ModApiGeneric]
    ) -> Dict[str, ModApiHostFn]:
        static_methods: Dict[str, ModApiHostFn] = {}
        if "static_methods" not in owner_values:
            return static_methods

        self.push_path(".static_methods")
        static_methods_obj = owner_values["static_methods"]
        if not isinstance(static_methods_obj, dict):
            raise self.new_error("is not an object")
        static_methods_obj = cast(Dict[str, Any], static_methods_obj)

        for static_method_name, static_method_values in static_methods_obj.items():
            self.push_path(f".{static_method_name}")
            if not isinstance(static_method_values, dict):
                raise self.new_error("is not an object")
            static_method_values = cast(Dict[str, Any], static_method_values)

            static_methods[static_method_name] = self.parse_host_fn(
                static_method_values, parent_generics
            )
            self.pop_path()

        self.pop_path()
        return static_methods

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


def get_mod_api(mod_api_path: Path) -> ModApi:
    try:
        mod_api_text = mod_api_path.read_text()
    # No, I am not in fact going to test an os error here, i'm sorry
    except OSError as err:  # pragma: no cover
        error_message = f"IO Error: {err}"
        error_string = f"""\
  in ({mod_api_path})
Error: {error_message}
"""
        raise GrugError(
            function_name="",
            file_path=mod_api_path,
            source_line="",
            span=SourceSpan(0, 0),
            error_message=error_message,
            error_string=error_string,
        ) from err

    return get_mod_api_from_text(mod_api_path, mod_api_text)


def get_mod_api_from_text(mod_api_path: Path, mod_api_text: str) -> ModApi:
    context = ModApiParseContext(mod_api_text, mod_api_path)

    # Parse json into python values
    try:
        mod_api_json = json.loads(mod_api_text)
    except json.JSONDecodeError as err:
        error_message = str(err)
        error_string = f"""\
  in ({mod_api_path})
Error: {error_message}
"""
        raise GrugError(
            function_name="",
            file_path=mod_api_path,
            source_line="",
            span=SourceSpan(0, 0),
            error_message=error_message,
            error_string=error_string,
        ) from err

    # root must be dict
    if not isinstance(mod_api_json, dict):
        raise context.new_error("is not an object")
    mod_api_root = cast(Dict[str, Any], mod_api_json)

    constraints: Dict[str, ModApiConstraint] = {}
    if "constraints" in mod_api_root:
        constraints_obj = context.get_key(mod_api_root, "constraints")
        if not isinstance(constraints_obj, dict):
            raise context.new_error("is not an object")
        constraints_obj = cast(Dict[str, Any], constraints_obj)
        # Collect names first so implementors can refer to any constraint,
        # including themselves and constraints declared later in the file.
        context.constraint_names = list(constraints_obj)
        for constraint_name, constraint_values in constraints_obj.items():
            context.push_path(f".{constraint_name}")
            if not isinstance(constraint_values, dict):
                raise context.new_error("is not an object")
            constraint_values = cast(Dict[str, Any], constraint_values)
            description = context.get_string(constraint_values, "description")
            context.pop_path()

            implementors: List[ModApiConstraintImplementor] = []
            for index, implementor in enumerate(
                context.get_list(constraint_values, "implementors")
            ):
                context.push_path(f"[{index}]")
                if not isinstance(implementor, dict):
                    raise context.new_error("is not an object")
                implementor = cast(Dict[str, Any], implementor)
                implementor_generics = context.parse_used_generics(implementor)
                implementor_type = context.parse_type(
                    context.get_key(implementor, "type"), implementor_generics
                )
                context.pop_path()
                implementors.append(
                    ModApiConstraintImplementor(implementor_generics, implementor_type)
                )
                context.pop_path()
            context.pop_path()
            constraints[constraint_name] = ModApiConstraint(description, implementors)
            context.pop_path()
        context.pop_path()

    # entities
    entities: Dict[str, ModApiEntity] = {}
    if "entities" in mod_api_root:
        context.push_path(".entities")
        entities_obj = mod_api_root["entities"]

        for entity_name, entity_values in entities_obj.items():
            context.push_path(f".{entity_name}")
            if not isinstance(entity_values, dict):
                raise context.new_error("is not an object")
            entity_values = cast(Dict[str, Any], entity_values)

            description = context.get_string(entity_values, "description")
            context.pop_path()

            export_fns: Dict[str, ModApiExportFn] = {}
            if "export_functions" in entity_values:
                export_functions = context.get_list(entity_values, "export_functions")

                for index, export_fn_values in enumerate(export_functions):
                    context.push_path(f"[{index}]")
                    if not isinstance(export_fn_values, dict):
                        raise context.new_error("is not an object")
                    export_fn_values = cast(Dict[str, Any], export_fn_values)

                    name = context.get_string(export_fn_values, "name")
                    context.pop_path()

                    context.pop_path()
                    context.push_path(f'["{name}"]')

                    export_description = context.get_string(
                        export_fn_values, "description"
                    )
                    context.pop_path()

                    if "parameters" in export_fn_values:
                        parameters = context.parse_parameters(
                            context.get_list(export_fn_values, "parameters"), []
                        )
                        context.pop_path()
                    else:
                        parameters: List[Parameter] = []

                    context.pop_path()
                    export_fns[name] = ModApiExportFn(export_description, parameters)

                context.pop_path()

            entity_static_methods = context.parse_static_methods(entity_values, [])

            context.pop_path()
            entities[entity_name] = ModApiEntity(
                description, export_fns, entity_static_methods
            )
        context.pop_path()

    # classes
    classes: Dict[str, ModApiClass] = {}
    if "classes" in mod_api_root:
        context.push_path(".classes")
        classes_obj = mod_api_root["classes"]

        for class_name, class_values in classes_obj.items():
            context.push_path(f".{class_name}")
            if not isinstance(class_values, dict):
                raise context.new_error("is not an object")
            class_values = cast(Dict[str, Any], class_values)

            description = context.get_string(class_values, "description")
            context.pop_path()

            generics = context.parse_used_generics(class_values)

            ty = IdType(class_name, [ExistentialType(i) for i in range(len(generics))])

            methods: Dict[str, ModApiHostFn] = {}
            if "methods" in class_values:
                context.push_path(".methods")
                methods_obj = class_values["methods"]

                for method_name, method_values in methods_obj.items():
                    context.push_path(f".{method_name}")
                    if not isinstance(method_values, dict):
                        raise context.new_error("is not an object")
                    method_values = cast(Dict[str, Any], method_values)

                    methods[method_name] = context.parse_host_fn(
                        method_values, generics
                    )
                    context.pop_path()

                context.pop_path()

            static_methods = context.parse_static_methods(class_values, generics)

            context.pop_path()
            classes[class_name] = ModApiClass(
                description, ty, generics, methods, static_methods
            )

        context.pop_path()

    # host functions
    host_fns: Dict[str, ModApiHostFn] = {}
    if "host_functions" in mod_api_root:
        context.push_path(".host_functions")
        host_fns_obj = mod_api_root["host_functions"]

        for host_fn_name, host_fn_values in host_fns_obj.items():
            context.push_path(f".{host_fn_name}")

            if not isinstance(host_fn_values, dict):
                raise context.new_error("is not an object")
            host_fn_values = cast(Dict[str, Any], host_fn_values)

            host_fns[host_fn_name] = context.parse_host_fn(host_fn_values, [])
            context.pop_path()

        context.pop_path()

    # validate all types in mod_api
    known_types: Dict[str, int] = {}

    context.push_path(".entities")
    for entity_name in entities:
        known_types[entity_name] = 0
    context.pop_path()

    context.push_path(".classes")
    for class_name, class_data in classes.items():
        context.push_path(f".{class_name}")
        if class_name in known_types:
            raise context.new_error("class name already exists")
        known_types[class_name] = len(class_data.generics)
        context.pop_path()

    for class_name, class_data in classes.items():
        context.push_path(f".{class_name}")
        context.push_path(".methods")
        for method_name, host_fn in class_data.methods.items():
            context.push_path(f".{method_name}")
            context.validate_function(
                host_fn.parameters, host_fn.return_type, known_types
            )
            context.pop_path()
        context.pop_path()

        context.push_path(".static_methods")
        for static_method_name, host_fn in class_data.static_methods.items():
            context.push_path(f".{static_method_name}")
            if static_method_name in class_data.methods:
                raise context.new_error("is already declared as a method")
            context.validate_function(
                host_fn.parameters, host_fn.return_type, known_types
            )
            context.pop_path()
        context.pop_path()
        context.pop_path()
    context.pop_path()

    context.push_path(".host_functions")
    for fn_name, host_fn in host_fns.items():
        context.push_path(f".{fn_name}")
        context.validate_function(host_fn.parameters, host_fn.return_type, known_types)
        context.pop_path()
    context.pop_path()

    context.push_path(".entities")
    for entity_name, entity in entities.items():
        context.push_path(f".{entity_name}")
        for fn_name, export_fn in entity.export_fns.items():
            context.push_path(f".{fn_name}")
            context.validate_function(
                export_fn.parameters, PrimitiveType.VOID, known_types
            )
            context.pop_path()

        context.push_path(".static_methods")
        for static_method_name, host_fn in entity.static_methods.items():
            context.push_path(f".{static_method_name}")
            context.validate_function(
                host_fn.parameters, host_fn.return_type, known_types
            )
            context.pop_path()
        context.pop_path()
        context.pop_path()
    context.pop_path()

    context.push_path(".constraints")
    for constraint_name, constraint in constraints.items():
        context.push_path(f".{constraint_name}")
        context.push_path(".implementors")
        for index, implementor in enumerate(constraint.implementors):
            context.push_path(f"[{index}]")
            context.push_path(".type")
            context.validate_type(implementor.type, known_types)
            context.pop_path()
            context.pop_path()
        context.pop_path()
        context.pop_path()
    context.pop_path()

    return ModApi(
        entities=entities, classes=classes, host_fns=host_fns, constraints=constraints
    )
