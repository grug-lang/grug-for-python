"""Every way registering or declaring a static method can go wrong."""

from pathlib import Path
from typing import Any, List

import grug
from grug import GrugError, GrugState, HostFn, Type
from grug.mod_api import get_mod_api_from_text


state = grug.init()


def noop(state: GrugState) -> Any:  # pragma: no cover
    return None


def noop_reg(generics: List[Type]) -> HostFn:  # pragma: no cover
    return noop


def declare(static_methods: str) -> None:
    """Parses a mod_api.json declaring `static_methods` on one class."""
    text = (
        '{"classes": {"VecNumber": {"description": "d", '
        '"methods": {"push": {"description": "d"}}, '
        '"static_methods": ' + static_methods + "}}}"
    )
    get_mod_api_from_text(Path("<inline>"), text)


# static_methods has to be an object of functions.
try:
    declare("42")
except GrugError as err:
    print(err)

try:
    declare('{"new": 42}')
except GrugError as err:
    print(err)

# A name means one thing on a type, which is what lets registering one take a
# name and nothing else.
try:
    declare('{"push": {"description": "d"}}')
except GrugError as err:
    print(err)

# The type has to exist.
try:
    state.mod_api.register_fn("Nonexistent", "new", noop)
except GrugError as err:
    print(err)

# The static method has to be declared.
try:
    state.mod_api.register_fn("VecNumber", "nonexistent", noop)
except GrugError as err:
    print(err)

# A generic static method is registered with a registration function.
try:
    state.mod_api.register_fn("VecNumber", "of", noop)
except GrugError as err:
    print(err)

try:
    state.mod_api.register_generic_fn("VecNumber", "new", noop_reg)
except GrugError as err:
    print(err)

# And neither kind may be registered twice.
try:
    state.mod_api.register_fn("VecNumber", "new", noop)
    state.mod_api.register_fn("VecNumber", "new", noop)
except GrugError as err:
    print(err)

try:
    state.mod_api.register_generic_fn("VecNumber", "of", noop_reg)
    state.mod_api.register_generic_fn("VecNumber", "of", noop_reg)
except GrugError as err:
    print(err)
