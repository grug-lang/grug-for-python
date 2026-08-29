"""Tests for static methods: ``VecNumber.new()``, where the receiver is a type.

Each case builds a throwaway mods directory and mod_api.json, so that a case
states everything it depends on and no case can be broken by another one's
declarations.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest  # pyright: ignore[reportMissingImports]

import grug
from grug import GrugState, HostFn, Type
from grug.error import GrugError


VEC_NUMBER: Dict[str, Any] = {
    "description": "A growable list of numbers.",
    "static_methods": {
        "new": {
            "description": "Creates a new empty VecNumber.",
            "parameters": [],
            "return_type": {"name": "VecNumber"},
        },
        "with_capacity": {
            "description": "Creates a VecNumber with a minimum capacity.",
            "parameters": [{"name": "capacity", "type": {"name": "number"}}],
            "return_type": {"name": "VecNumber"},
        },
    },
    "methods": {
        "push": {
            "description": "Pushes a number onto the end.",
            "parameters": [{"name": "value", "type": {"name": "number"}}],
        },
        "pop": {
            "description": "Removes and returns the last number.",
            "parameters": [],
            "return_type": {"name": "number"},
        },
    },
}

BOX: Dict[str, Any] = {
    "description": "Holds one value of any type.",
    "used_generics": ["$T"],
    "static_methods": {
        "of": {
            "description": "Creates a Box holding the given value.",
            "parameters": [{"name": "value", "type": {"name": "$T"}}],
            "return_type": {"name": "Box", "generics": [{"name": "$T"}]},
        }
    },
    "methods": {
        "get": {
            "description": "Returns the held value.",
            "parameters": [],
            "return_type": {"name": "$T"},
        }
    },
}

DOG_ENTITY: Dict[str, Any] = {
    "description": "A dog.",
    "static_methods": {
        "count": {
            "description": "How many dogs exist.",
            "return_type": {"name": "number"},
        }
    },
    "export_functions": [
        {
            "name": "bark",
            "description": "Called when the dog barks.",
            "parameters": [],
        }
    ],
}


def write_mod(
    tmp_path: Path,
    body: str,
    *,
    classes: Optional[Dict[str, Any]] = None,
    entities: Optional[Dict[str, Any]] = None,
) -> Path:
    mod_api = {
        "entities": entities if entities is not None else {"Dog": DOG_ENTITY},
        "classes": classes
        if classes is not None
        else {"VecNumber": VEC_NUMBER, "Box": BOX},
        "host_functions": {
            "record_number": {
                "description": "Records a number.",
                "parameters": [{"name": "value", "type": {"name": "number"}}],
            },
            "record_string": {
                "description": "Records a string.",
                "parameters": [{"name": "value", "type": {"name": "string"}}],
            },
        },
    }

    (tmp_path / "mod_api.json").write_text(json.dumps(mod_api))
    mods = tmp_path / "mods" / "animals"
    mods.mkdir(parents=True)
    (mods / "labrador-Dog.grug").write_text("export bark() {\n" + body + "\n}\n")
    return tmp_path


def make_state(tmp_path: Path) -> Tuple[GrugState, List[object]]:
    """A state with the whole test mod_api registered, plus the list that the
    recording host functions append to."""
    recorded: List[object] = []
    state = grug.init(
        mod_api_path=str(tmp_path / "mod_api.json"),
        mods_dir_path=str(tmp_path / "mods"),
    )

    @state.grug_class
    class VecNumber:  # pyright: ignore[reportUnusedClass]
        values: List[float]
        capacity: float

        # A static method takes the GrugState first, where a method takes the
        # receiver first and the state second.
        @staticmethod
        def new(state: GrugState) -> "VecNumber":
            vec = VecNumber()
            vec.values = []
            vec.capacity = 0
            return vec

        @staticmethod
        def with_capacity(state: GrugState, capacity: float) -> "VecNumber":
            vec = VecNumber.new(state)
            vec.capacity = capacity
            return vec

        def push(self, state: GrugState, value: float) -> None:
            self.values.append(value)

        def pop(self, state: GrugState) -> float:
            return self.values.pop()

    @state.grug_class
    class Box:  # pyright: ignore[reportUnusedClass]
        value: Any

        @grug.static_method
        @staticmethod
        def of(generics: List[Type]) -> HostFn:
            def inner(state: GrugState, value: Any) -> "Box":
                box = Box()
                box.value = value
                return box

            return inner

        @staticmethod
        def get(generics: List[Type]) -> HostFn:
            def inner(self: "Box", state: GrugState) -> Any:
                return self.value

            return inner

    @state.grug_class
    class Dog:  # pyright: ignore[reportUnusedClass]
        @grug.static_method
        @staticmethod
        def count(state: GrugState) -> float:
            return 2.0

    @state.host_fn
    def record_number(state: GrugState, value: float) -> None:  # pyright: ignore[reportUnusedFunction]
        recorded.append(value)

    @state.host_fn
    def record_string(state: GrugState, value: str) -> None:  # pyright: ignore[reportUnusedFunction]
        recorded.append(value)

    return state, recorded


def compile_mod(state: GrugState) -> None:
    """`update()` prints a compile error and carries on, which would let a
    broken case pass quietly. `_update()` is the same work with the error
    raised."""
    state._update()  # pyright: ignore[reportPrivateUsage]


def run(tmp_path: Path, body: str) -> List[object]:
    write_mod(tmp_path, body)
    state, recorded = make_state(tmp_path)
    entity = state.mods["animals"]["labrador-Dog.grug"].create_entity()
    compile_mod(state)
    entity.bark()
    return recorded


def compile_error(tmp_path: Path, body: str, **kwargs: Any) -> str:
    """The message of the error raised while compiling `body`."""
    write_mod(tmp_path, body, **kwargs)
    with pytest.raises(GrugError) as excinfo:
        state, _ = make_state(tmp_path)
        compile_mod(state)
    return excinfo.value.error_message


def test_static_method_constructs_a_value(tmp_path: Path):
    recorded = run(
        tmp_path,
        "    x: VecNumber = VecNumber.new()\n"
        "    x.push(41)\n"
        "    record_number(x.pop())",
    )
    assert recorded == [41.0]


def test_static_method_takes_arguments(tmp_path: Path):
    recorded = run(
        tmp_path,
        "    x: VecNumber = VecNumber.with_capacity(8)\n"
        "    x.push(7)\n"
        "    record_number(x.pop())",
    )
    assert recorded == [7.0]


def test_static_method_call_is_an_expression(tmp_path: Path):
    recorded = run(tmp_path, "    record_number(Dog.count())")
    assert recorded == [2.0]


def test_static_method_on_an_entity(tmp_path: Path):
    recorded = run(
        tmp_path,
        "    n: number = Dog.count()\n    record_number(n + 1)",
    )
    assert recorded == [3.0]


def test_generic_static_method_infers_from_its_argument(tmp_path: Path):
    recorded = run(
        tmp_path,
        '    b: Box[string] = Box.of("hello")\n    record_string(b.get())',
    )
    assert recorded == ["hello"]


def test_calling_a_method_statically_is_an_error(tmp_path: Path):
    message = compile_error(tmp_path, "    VecNumber.push(3)")
    assert message == (
        "'push' is a method on 'VecNumber', so it must be called on a value of "
        "that type, like 'x.push()'"
    )


def test_calling_a_static_method_on_a_value_is_an_error(tmp_path: Path):
    message = compile_error(
        tmp_path,
        "    x: VecNumber = VecNumber.new()\n    x.new()",
    )
    assert message == (
        "'new' is a static method on 'VecNumber', so it must be called as "
        "'VecNumber.new()'"
    )


def test_unknown_static_method_is_an_error(tmp_path: Path):
    message = compile_error(tmp_path, "    VecNumber.nonexistent()")
    assert message == "Cannot find static method 'nonexistent' on 'VecNumber'"


def test_unknown_static_method_on_an_entity_is_an_error(tmp_path: Path):
    message = compile_error(tmp_path, "    Dog.nonexistent()")
    assert message == "Cannot find static method 'nonexistent' on 'Dog'"


def test_a_type_declaring_no_static_methods_reports_the_missing_one(tmp_path: Path):
    classes: Dict[str, Any] = {
        "VecNumber": VEC_NUMBER,
        "Box": BOX,
        "Empty": {"description": "Declares nothing."},
    }
    message = compile_error(tmp_path, "    Empty.new()", classes=classes)
    assert message == "Cannot find static method 'new' on 'Empty'"


def test_an_undeclared_name_is_still_an_unknown_variable(tmp_path: Path):
    message = compile_error(tmp_path, "    NotAType.new()")
    assert message == "The variable 'NotAType' does not exist"


def test_static_method_arguments_are_type_checked(tmp_path: Path):
    message = compile_error(
        tmp_path, '    x: VecNumber = VecNumber.with_capacity("nope")'
    )
    assert "string" in message and "number" in message


def bare_state(tmp_path: Path, **kwargs: Any) -> GrugState:
    """A state whose mod_api is written but whose host functions are not
    registered yet, for exercising registration itself."""
    write_mod(tmp_path, "    record_number(1)", **kwargs)
    return grug.init(
        mod_api_path=str(tmp_path / "mod_api.json"),
        mods_dir_path=str(tmp_path / "mods"),
    )


def noop(state: GrugState) -> float:
    return 0.0  # pragma: no cover


def noop_reg(generics: List[Type]) -> HostFn:
    return noop  # pragma: no cover


def test_registering_a_static_method_on_an_unknown_type(tmp_path: Path):
    state = bare_state(tmp_path)
    with pytest.raises(GrugError) as excinfo:
        state.mod_api.register_fn("Nonexistent", "new", noop, static=True)
    assert (
        excinfo.value.error_message
        == "Class or entity with name 'Nonexistent' is not found in mod_api.json"
    )


def test_registering_an_undeclared_static_method(tmp_path: Path):
    state = bare_state(tmp_path)
    with pytest.raises(GrugError) as excinfo:
        state.mod_api.register_fn("VecNumber", "nonexistent", noop, static=True)
    assert (
        excinfo.value.error_message
        == "'VecNumber' does not contain static method with name 'nonexistent'"
    )


def test_registering_a_generic_static_method_as_non_generic(tmp_path: Path):
    state = bare_state(tmp_path)
    with pytest.raises(GrugError) as excinfo:
        state.mod_api.register_fn("Box", "of", noop, static=True)
    assert excinfo.value.error_message == "Static method 'of' on 'Box' is generic"


def test_registering_a_static_method_twice(tmp_path: Path):
    state = bare_state(tmp_path)
    state.mod_api.register_fn("VecNumber", "new", noop, static=True)
    with pytest.raises(GrugError) as excinfo:
        state.mod_api.register_fn("VecNumber", "new", noop, static=True)
    assert (
        excinfo.value.error_message
        == "Static method named 'new' on 'VecNumber' has already been registered"
    )


def test_registering_a_non_generic_static_method_as_generic(tmp_path: Path):
    state = bare_state(tmp_path)
    with pytest.raises(GrugError) as excinfo:
        state.mod_api.register_generic_fn("VecNumber", "new", noop_reg, static=True)
    assert (
        excinfo.value.error_message == "Static method VecNumber.new is not generic"
    )


def test_registering_a_generic_static_method_twice(tmp_path: Path):
    state = bare_state(tmp_path)
    state.mod_api.register_generic_fn("Box", "of", noop_reg, static=True)
    with pytest.raises(GrugError) as excinfo:
        state.mod_api.register_generic_fn("Box", "of", noop_reg, static=True)
    assert (
        excinfo.value.error_message
        == "Static method Box.of has already been registered"
    )


def test_static_methods_must_be_an_object(tmp_path: Path):
    classes: Dict[str, Any] = {
        "VecNumber": dict(VEC_NUMBER, static_methods=["not an object"])
    }
    with pytest.raises(GrugError) as excinfo:
        bare_state(tmp_path, classes=classes)
    assert excinfo.value.error_message == "root.classes.VecNumber.static_methods is not an object"


def test_a_static_method_must_be_an_object(tmp_path: Path):
    classes: Dict[str, Any] = {
        "VecNumber": dict(VEC_NUMBER, static_methods={"new": "not an object"})
    }
    with pytest.raises(GrugError) as excinfo:
        bare_state(tmp_path, classes=classes)
    assert (
        excinfo.value.error_message
        == "root.classes.VecNumber.static_methods.new is not an object"
    )


def test_a_package_can_provide_static_methods(tmp_path: Path):
    write_mod(
        tmp_path,
        "    x: VecNumber = VecNumber.new()\n"
        "    x.push(5)\n"
        "    record_number(x.pop())\n"
        '    b: Box[string] = Box.of("packaged")\n'
        "    record_string(b.get())",
    )
    recorded: List[object] = []

    class Vec:
        values: List[float]

    def new(state: GrugState) -> Vec:
        vec = Vec()
        vec.values = []
        return vec

    def with_capacity(state: GrugState, capacity: float) -> Vec:
        return new(state)  # pragma: no cover

    def push(state: GrugState, receiver: Vec, value: float) -> None:
        receiver.values.append(value)

    def pop(state: GrugState, receiver: Vec) -> float:
        return receiver.values.pop()

    class Boxed:
        value: object

    def of(generics: List[Type]) -> HostFn:
        def inner(state: GrugState, value: object) -> Boxed:
            boxed = Boxed()
            boxed.value = value
            return boxed

        return inner

    def get(generics: List[Type]) -> HostFn:
        def inner(state: GrugState, receiver: Boxed) -> object:
            return receiver.value

        return inner

    def count(state: GrugState) -> float:
        return 0.0  # pragma: no cover

    def record_number(state: GrugState, value: float) -> None:
        recorded.append(value)

    def record_string(state: GrugState, value: str) -> None:
        recorded.append(value)

    package = grug.GrugPackage(
        prefix="",
        host_fns=[record_number, record_string],
        generic_fns=[],
        methods=[("VecNumber", push), ("VecNumber", pop)],
        generic_methods=[("Box", get)],
        static_methods=[
            ("VecNumber", new),
            ("VecNumber", with_capacity),
            ("Dog", count),
        ],
        generic_static_methods=[("Box", of)],
    )

    state = grug.init(
        mod_api_path=str(tmp_path / "mod_api.json"),
        mods_dir_path=str(tmp_path / "mods"),
        packages=[package],
    )
    entity = state.mods["animals"]["labrador-Dog.grug"].create_entity()
    compile_mod(state)
    entity.bark()

    assert recorded == [5.0, "packaged"]


def test_a_variable_shadows_a_type_of_the_same_name(tmp_path: Path):
    """A variable wins over the type it is named after, so adding a static
    method to a class can never change what existing code means.

    The variable is not in scope yet while its own initializer is being
    checked, which is what lets it be initialized from the static method.
    """
    recorded = run(
        tmp_path,
        "    VecNumber: VecNumber = VecNumber.new()\n"
        "    VecNumber.push(1)\n"
        "    record_number(VecNumber.pop())",
    )
    assert recorded == [1.0]
