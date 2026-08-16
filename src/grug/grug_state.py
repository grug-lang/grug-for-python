from __future__ import annotations

import json
import inspect
import sys
import weakref
import types
from functools import wraps
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import (
    TypeVar,
    get_type_hints,
    cast,
    TYPE_CHECKING,
    Tuple,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Set,
)

from .grug_value import HostFn, HostFnReg, GrugValue

from .mod_api import ModApi
from .error import GrugError
from .parser import HelperFn, OnFn, Parser, Type, VariableStatement
from .serializer import Serializer
from .tokenizer import Tokenizer
from .type_propagator import TypePropagator
from .mod_api import ModApi, get_mod_api

if TYPE_CHECKING:  # pragma: no cover
    from .entity import Entity

    EntitiesSet = weakref.WeakSet["Entity"]
else:
    EntitiesSet = weakref.WeakSet


class GrugRuntimeErrorType(Enum):
    STACK_OVERFLOW = 0  # Using auto() here would assign 1
    TIME_LIMIT_EXCEEDED = auto()
    GAME_FN_ERROR = auto()


GrugRuntimeErrorHandler = Callable[[str, GrugRuntimeErrorType, str, str], None]


class GrugPackage:
    def __init__(self, *, prefix: str, host_fns: Sequence[HostFn], generic_fns: Sequence[HostFnReg], methods: Sequence[Tuple[str, HostFn]], generic_methods: Sequence[Tuple[str, HostFnReg]]):
        self.prefix = prefix
        self.host_fns = host_fns
        self.generic_fns = generic_fns
        self.methods = methods
        self.generic_methods = generic_methods

    def no_prefix(self):
        self.prefix = ""
        return self

    def set_prefix(self, new_prefix: str):
        self.prefix = new_prefix
        return self


@dataclass
class GrugFile:
    relative_path: str
    mod: str

    global_variables: List[VariableStatement]
    on_fns: Dict[str, OnFn]
    helper_fns: Dict[str, HelperFn]

    mod_api: ModApi

    state: "GrugState"
    mtime: float

    entities: EntitiesSet = field(default_factory=EntitiesSet)

    def create_entity(self):
        from .entity import Entity

        return Entity(self)

    def __getitem__(self, key: str):
        """Files are not indexable; this exists to satisfy the type checker for chained lookups."""
        raise TypeError(
            f"GrugFile '{self.relative_path}' is not a directory and cannot be indexed"
        )


@dataclass
class GrugDir:
    """Represents a directory of grug files and subdirectories."""

    name: str
    files: Dict[str, GrugFile] = field(default_factory=lambda: {})
    dirs: Dict[str, "GrugDir"] = field(default_factory=lambda: {})

    def create_entity(self):
        """
        Satisfies the type checker for GrugDir | GrugFile unions.
        Raises TypeError if you actually try to treat a directory as a single entity.
        """
        raise TypeError(f"'{self.name}' is a directory, not a file")

    def __getitem__(self, key: str):
        if key in self.dirs:
            return self.dirs[key]
        if key in self.files:
            return self.files[key]
        raise KeyError(f"{key} not found. Available: {list(self.files.keys())}")


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

TClass = TypeVar("TClass", bound=type)

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

        self.mod_api = get_mod_api(Path(mod_api_path))

        self.mods_dir_path = Path(mods_dir_path)

        self.on_fn_time_limit_ms = on_fn_time_limit_ms

        self.game_fns: Dict[str, HostFn] = {}
        self.classes: Dict[str, Dict[str, HostFn]] = {}
        self._add_game_fns_from_packages(packages)

        self.next_id = 0

        self.fn_depth = 0

        self._mods: Optional[GrugDir] = None

        self.executed_file: Optional[GrugFile] = None
        self.executed_entity: Optional[Entity] = None

    @property
    def mods(self) -> GrugDir:
        if self._mods is None:
            self._update()
        assert self._mods
        return self._mods

    def _add_game_fns_from_packages(self, packages: Sequence[GrugPackage]):
        for pkg in packages:
            for host_fn in pkg.host_fns:
                name = (
                    f"{pkg.prefix}_{host_fn.__name__}"
                    if pkg.prefix
                    else host_fn.__name__
                )
                self.mod_api.register_fn(None, name, host_fn)
            for generic_fn in pkg.generic_fns:
                name = (
                    f"{pkg.prefix}_{generic_fn.__name__}"
                    if pkg.prefix
                    else generic_fn.__name__
                )
                self.mod_api.register_generic_fn(None, name, generic_fn)
            for class_name, method in pkg.methods: 
                name = method.__name__
                self.mod_api.register_fn(class_name, name, method)
            for class_name, generic_method in pkg.generic_methods:
                name = generic_method.__name__
                self.mod_api.register_generic_fn(class_name, name, generic_method)

    def host_fn(self, fn: HostFn) -> HostFn:
        """Decorator for host functions."""
        self.mod_api.register_fn(None, fn.__name__, fn)
        return fn

    def grug_class(self, cls: TClass) -> TClass:
        """Decorator for grug classes."""
        for name, fn in vars(cls).items():
            if isinstance(fn, staticmethod):
                fn = fn.__func__
            elif isinstance(fn, types.FunctionType):
                pass
            # python 3.7 doesn't have any members other than methods
            else: # pragma: no cover
                continue

            hints = get_type_hints(fn) # pyright: ignore
            parameters = list(inspect.signature(fn).parameters.values()) # pyright: ignore

            if (
                len(parameters) == 1
                and hints.get(parameters[0].name) == List[Type]
                and hints.get("return") == HostFn
            ):
                generic_method = cast(HostFnReg, fn)

                @wraps(generic_method)
                def register(
                    generics: List[Type],
                    generic_method: HostFnReg = generic_method,
                ) -> Optional[HostFn]:
                    method = generic_method(generics)
                    return None if method is None else self._adapt_grug_method(method)

                self.mod_api.register_generic_fn(cls.__name__, name, register)
                continue

            # The receiver is implicit from grug's perspective, so `state` is
            # the first method argument even though it is the second parameter
            # in the unbound Python function (`self, state, ...`).
            if len(parameters) >= 2 and hints.get(parameters[1].name) is GrugState:
                self.mod_api.register_fn(
                    cls.__name__, name, self._adapt_grug_method(cast(HostFn, fn))
                )
                continue

            raise GrugError.new_init_error(
                f"Method '{cls.__name__}.{name}' has an unsupported signature. "
                "Expected a normal method whose first argument after the receiver "
                "is annotated as GrugState, or a generic method with signature "
                "(List[Type]) -> HostFn"
            )
        return cls

    @staticmethod
    def _adapt_grug_method(method: HostFn) -> HostFn:
        """Adapt grug's ``(state, receiver, ...)`` call to a Python method call."""

        @wraps(method)
        def adapted(state: GrugState, receiver: GrugValue, *args: GrugValue):
            return method(receiver, state, *args)

        return adapted

    def generic_fn(self, fn: HostFnReg) -> HostFnReg:
        """Decorator for generic game functions."""
        self.mod_api.register_generic_fn(None, fn.__name__, fn)
        return fn

    def _compile_grug_file(self, grug_file_relative_path: str):
        mod = Path(grug_file_relative_path).parts[0]

        grug_file_absolute_path = self.mods_dir_path / grug_file_relative_path

        text = grug_file_absolute_path.read_text()
        if len(text) == 0:
            raise GrugError.new_file_name_error(
                Path(grug_file_relative_path), "File is empty"
            )

        mtime = grug_file_absolute_path.stat().st_mtime

        grug_file_path = Path(grug_file_relative_path)

        entity_type = self._get_file_entity_type(grug_file_path)

        tokens = Tokenizer(text, grug_file_path).tokenize()

        ast = Parser(tokens, grug_file_path, text).parse()

        TypePropagator(
            ast,
            mod,
            entity_type,
            self.mod_api,
            Path(self.mods_dir_path),
            grug_file_path,
            text,
        ).fill()

        global_variables = [s for s in ast if isinstance(s, VariableStatement)]

        on_fns = {s.fn_name: s for s in ast if isinstance(s, OnFn)}

        helper_fns = {s.fn_name: s for s in ast if isinstance(s, HelperFn)}

        return GrugFile(
            grug_file_relative_path,
            mod,
            global_variables,
            on_fns,
            helper_fns,
            self.mod_api,
            self,
            mtime,
        )

    def _get_file_entity_type(self, grug_file_path: Path) -> str:
        """
        Extract and validate the entity type from a grug filename.

        Args:
            grug_filename: A filename like 'furnace-BlockEntity.grug'

        Returns:
            The entity type string (e.g., 'BlockEntity')

        Raises:
            GrugError: If the filename format is invalid
        """
        grug_filename = grug_file_path.name

        # Find the dash
        dash_index = grug_filename.find("-")

        if dash_index == -1 or dash_index + 1 >= len(grug_filename):
            raise GrugError.new_file_name_error(
                grug_file_path,
                f"'{grug_filename}' is missing an entity type in its name",
            )

        # Find the period after the dash
        period_index = grug_filename.find(".", dash_index + 1)

        if period_index == -1:
            raise GrugError.new_file_name_error(
                grug_file_path, f"'{grug_filename}' is missing a period in its name"
            )

        # Extract entity type (between dash and period)
        entity_type = grug_filename[dash_index + 1 : period_index]

        # Check if entity type is empty
        if len(entity_type) == 0:
            raise GrugError.new_file_name_error(
                grug_file_path,
                f"'{grug_filename}' is missing an entity type in its name",
            )

        # Validate PascalCase
        self._check_custom_id_is_pascal(entity_type, grug_file_path)

        return entity_type

    def _check_custom_id_is_pascal(self, type_name: str, grug_file_path: Path):
        """
        Validate that a custom ID type name is in PascalCase.

        Args:
            type_name: The type name to validate

        Raises:
            GrugError: If the type name is not valid PascalCase
        """
        # The first character must always be uppercase
        if not type_name[0].isupper():
            raise GrugError.new_file_name_error(
                grug_file_path,
                f"'{type_name}' seems like a custom ID type, but it doesn't start in Uppercase",
            )

        # Custom IDs only consist of uppercase, lowercase characters, and digits
        for c in type_name:
            if not (c.isupper() or c.islower() or c.isdigit()):
                raise GrugError.new_file_name_error(
                    grug_file_path,
                    f"'{type_name}' seems like a custom ID type, but it contains '{c}', "
                    f"which isn't uppercase, lowercase, or a digit",
                )

    # Q(nikhil): Why is this a separate function?
    def update(self):
        """This (re)compiles grug files using mark-and-sweep, and prints any error."""
        try:
            self._update()
        except Exception as e:  # pragma: no cover
            print(e)

    def _update(self):
        """This (re)compiles grug files using mark-and-sweep."""
        if self._mods is None:
            self._mods = GrugDir(name="mods")

        seen_files: Set[str] = set()
        seen_dirs: Set[str] = set()

        def update_dir(current_path: Path, grug_dir: GrugDir):
            # Mark this directory as visited
            seen_dirs.add(current_path.as_posix())

            # Mark phase: scan disk
            for entry in current_path.iterdir():
                if entry.is_dir():
                    sub = grug_dir.dirs.get(entry.name)
                    if sub is None:
                        sub = GrugDir(name=entry.name)
                        grug_dir.dirs[entry.name] = sub
                    update_dir(entry, sub)

                elif entry.is_file() and entry.suffix == ".grug":
                    rel = entry.relative_to(self.mods_dir_path).as_posix()
                    seen_files.add(rel)

                    current_mtime = entry.stat().st_mtime
                    existing = grug_dir.files.get(entry.name)

                    if existing is None or existing.mtime < current_mtime:
                        new_file = self._compile_grug_file(rel)

                        # Transfer entities from the old file to the new file
                        if existing is not None:
                            for entity in existing.entities:
                                entity.file = new_file
                                entity._init_globals(new_file.global_variables)  # type: ignore
                                new_file.entities.add(entity)

                        grug_dir.files[entry.name] = new_file

            # Sweep files
            for name, file in list(grug_dir.files.items()):
                if file.relative_path not in seen_files:
                    del grug_dir.files[name]  # pragma: no cover

            # Sweep subdirectories
            for name in list(grug_dir.dirs.keys()):
                sub_path_str = (current_path / name).as_posix()
                if sub_path_str not in seen_dirs:
                    del grug_dir.dirs[name]  # pragma: no cover

        root = self._mods

        # Process each top-level mod directory
        for mod_dir in self.mods_dir_path.iterdir():
            if mod_dir.is_dir():  # pragma: no cover
                sub = root.dirs.get(mod_dir.name)
                if sub is None:
                    sub = GrugDir(name=mod_dir.name)
                    root.dirs[mod_dir.name] = sub
                update_dir(mod_dir, sub)

        # Sweep removed top-level dirs
        for name in list(root.dirs.keys()):
            root_path_str = (self.mods_dir_path / name).as_posix()
            if root_path_str not in seen_dirs:
                del root.dirs[name]  # pragma: no cover

    def run_all_package_tests(self):
        self._update()

        tests_ran = 0

        def run(dir: GrugDir):
            for subdir in sorted(dir.dirs.values(), key=lambda d: d.name):
                run(subdir)
            for file in sorted(dir.files.values(), key=lambda f: f.relative_path):
                print(f"Testing {file.relative_path}...")
                test = file.create_entity()
                test.run()
                nonlocal tests_ran
                tests_ran += 1

        run(self.mods)

        print(f"All {tests_ran} tests passed!")

    # TODO: Should this method be moved out of this GrugState, so it becomes a free function?
    def grug_to_json(self, input_grug_text: str):
        # TODO: path to file should be a parameter
        tokens = Tokenizer(input_grug_text, Path("<input>")).tokenize()
        ast = Parser(tokens, Path("<input>"), input_grug_text).parse()
        return Serializer.ast_to_json_text(ast)

    # TODO: Should this method be moved out of this GrugState, so it becomes a free function?
    def json_to_grug(self, input_json_text: str):
        ast = json.loads(input_json_text)
        return Serializer.ast_to_grug(ast)
