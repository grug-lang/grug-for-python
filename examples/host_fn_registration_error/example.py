import grug
from grug import GrugState, GrugError, Type, HostFn
from grug.entity import GameFnError
from typing import List

state = grug.init()

def print_string(state: GrugState, string: str): # pragma: no cover
    if string == "":
        raise GameFnError("print_string() received an empty string")
    print(string)

def unknown_fn(state: GrugState): # pragma: no cover
    pass

def unknown_generic_fn(ty: List[Type]): # pragma: no cover
    pass

def print_grug(state: GrugState, obj: object): # pragma: no cover
    print(obj)

def print_grug_gen(types: List[Type]) -> HostFn: # pragma: no cover
    def inner(state: GrugState, obj: object):
        print(object)
    return inner

print_grug.__name__ = "print"
print_grug_gen.__name__ = "print"

class UnknownClass:
    def unknown_method(self, state: GrugState): # pragma: no cover
        pass

class UnknownClass2:
    def unknown_method(self, types: List[Type]) -> HostFn: # pragma: no cover
        def inner (self: UnknownClass2, state: GrugState): 
            pass
        return inner

class KnownClass:
    def known_method(self, state: GrugState): # pragma: no cover
        pass

class KnownClass2:
    def unknown_method(self, state: GrugState): # pragma: no cover
        pass
KnownClass2.__name__ = "KnownClass"

class KnownClass3:
    def supposed_to_be_generic(self, state: GrugState): # pragma: no cover
        pass
KnownClass3.__name__ = "KnownClass"

class KnownClass4:
    @staticmethod
    def unknown_generic_method(types: List[Type]) -> HostFn: # pragma: no cover
        def inner(self: KnownClass4, state: GrugState):
            pass
        return inner
KnownClass4.__name__ = "KnownClass"

class KnownClass5:
    @staticmethod
    def supposed_to_be_non_generic(types: List[Type]) -> HostFn: # pragma: no cover
        def inner(self: KnownClass5, state: GrugState):
            pass
        return inner
KnownClass5.__name__ = "KnownClass"

class KnownClass6:
    @staticmethod
    def known_generic_method(types: List[Type]) -> HostFn: # pragma: no cover
        def inner(self: KnownClass6, state: GrugState):
            pass
        return inner
KnownClass6.__name__ = "KnownClass"

class KnownClass7:
    def invalid_method_signature(self, value: int): # pragma: no cover
        print(value)
KnownClass7.__name__ = "KnownClass"


try:
    state.host_fn(print_string)
    state.host_fn(print_string)
except GrugError as err:
    print(err)

try:
    state.host_fn(print_grug)
except GrugError as err:
    print(err)

try:
    state.host_fn(unknown_fn)
except GrugError as err:
    print(err)

try:
    state.grug_class(UnknownClass)
except GrugError as err:
    print(err)
    
try:
    state.grug_class(UnknownClass2)
except GrugError as err:
    print(err)
    
try:
    state.grug_class(KnownClass)
    state.grug_class(KnownClass)
except GrugError as err:
    print(err)
    
try:
    state.grug_class(KnownClass2)
except GrugError as err:
    print(err)

try:
    state.grug_class(KnownClass3)
except GrugError as err:
    print(err)

try:
    state.grug_class(KnownClass4)
except GrugError as err:
    print(err)

try:
    state.grug_class(KnownClass5)
except GrugError as err:
    print(err)

try:
    state.grug_class(KnownClass6)
    state.grug_class(KnownClass6)
except GrugError as err:
    print(err)

try:
    # We are testing the type mismatch here
    state.generic_fn(unknown_fn) # pyright: ignore
except GrugError as err:
    print(err)

try:
    state.generic_fn(print_grug_gen)
    state.generic_fn(print_grug_gen)
except GrugError as err:
    print(err)

try:
    # We are testing the type mismatch here
    state.generic_fn(print_string) # pyright: ignore
except GrugError as err:
    print(err)

try:
    state.grug_class(KnownClass7)
except GrugError as err:
    print(err)
