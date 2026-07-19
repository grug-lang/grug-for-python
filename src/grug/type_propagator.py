from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import os

from .error import GrugError, SourceSpan
from .parser import (
    Ast,
    BinaryExpr,
    CallExpr,
    CallStatement,
    EntityExpr,
    Expr,
    FalseExpr,
    HelperFn,
    IdentifierExpr,
    IfStatement,
    LogicalExpr,
    NumberExpr,
    OnFn,
    ParenthesizedExpr,
    Parameter,
    ResourceExpr,
    ReturnStatement,
    Statement,
    StringExpr,
    TrueExpr,
    Type,
    PrimitiveType,
	IdType,
	EntityStrType,
	ResourceStrType,
    ExistentialType,
    UnaryExpr,
    VariableStatement,
    WhileStatement,
)
from .tokenizer import TokenType
from .mod_api import ModApi, ModApiHostFn
from .grug_value import HostFn


@dataclass
class Variable:
    name: str
    type: Type

@dataclass
class TypeMismatch(Exception):
    span: SourceSpan
    expected: Type
    actual: Type

@dataclass
class ExistentialData:
    function_name: str
    function_name_span: SourceSpan

def type_name(ty: Type) -> str:
    if isinstance(ty, PrimitiveType):
        return str(ty)
    if isinstance(ty, IdType):
        return ty.name
    if isinstance(ty, ResourceStrType):
        return "resource"
    if isinstance(ty, EntityStrType):
        return "entity"
    return "_"

def type_matches(left: Type, right: Type) -> bool:
    if isinstance(left, ExistentialType) or isinstance(right, ExistentialType):
        return True
    if isinstance(left, IdType) and isinstance(right, IdType):
        if left.name != right.name or len(left.generics) != len(right.generics):
            return False
        return all(
            type_matches(left_generic, right_generic)
            for left_generic, right_generic in zip(left.generics, right.generics)
        )
    return left == right

def type_diff(expected: Type, actual: Type) -> str:
    if type_matches(expected, actual):
        return "_"
    if isinstance(expected, IdType) and isinstance(actual, IdType) and expected.name == actual.name:
        inner = ", ".join(
            type_diff(expected_generic, actual_generic)
            for expected_generic, actual_generic in zip(expected.generics, actual.generics)
        )
        return f"{expected.name}[{inner}]"
    return type_name(expected)

def substitute_type(ty: Type, replacements: List[Type]) -> Type:
    if isinstance(ty, ExistentialType):
        return replacements[ty.idx]
    if isinstance(ty, IdType):
        return IdType(ty.name, [substitute_type(generic, replacements) for generic in ty.generics])
    return ty

class TyCtx:
    def __init__(self, function_name: str, type_propagator: "TypePropagator"):
        self.function_name = function_name
        self.type_propagator = type_propagator
        self.existentials: List[ExistentialData] = []
        self.substitutions: List[Type] = []
        self.constraints: List[Tuple[Type, Type]] = []

    def create_existential(self, function_name: str, function_name_span: SourceSpan) -> ExistentialType:
        existential = ExistentialType(len(self.existentials))
        self.existentials.append(ExistentialData(function_name, function_name_span))
        self.substitutions.append(existential)
        return existential

    # Returns the first currently known replacement type for an existential
    def get_current_type(self, ty: Type) -> Optional[Type]:
        seen: List[int] = []
        while isinstance(ty, ExistentialType):
            if ty.idx in seen:
                return None
            seen.append(ty.idx)
            ty = self.substitutions[ty.idx]
        return ty

    def add_constraint(self, span: SourceSpan, first_left: Type, first_right: Type) -> None:
        self.constraints.append((first_left, first_right))
        while self.constraints:
            left, right = self.constraints.pop()

            if left == right:
                continue

            if isinstance(left, ResourceStrType) or isinstance(right, ResourceStrType):
                raise self.type_propagator.new_error(span, "cannot use resource strings in generics")
            if isinstance(left, EntityStrType) or isinstance(right, EntityStrType):
                raise self.type_propagator.new_error(span, "cannot use entity strings in generics")

            if isinstance(left, IdType) and isinstance(right, IdType):
                if left.name != right.name:
                    raise TypeMismatch(span, self._substitute_type(first_left), self._substitute_type(first_right))
                assert len(left.generics) == len(right.generics)
                self.constraints.extend(zip(left.generics, right.generics))
                continue

            if isinstance(left, ExistentialType):
                self._bind_or_constrain(left.idx, right)
                continue
            if isinstance(right, ExistentialType):
                self._bind_or_constrain(right.idx, left)
                continue

            raise TypeMismatch(span, self._substitute_type(first_left), self._substitute_type(first_right))

    def _bind_or_constrain(self, idx: int, other: Type) -> None:
        # If this existential is still unresolved, bind it to the other type.
        # Otherwise, require the existing binding and the new type to agree.
        current = self.substitutions[idx]
        if isinstance(current, ExistentialType) and current.idx == idx:
            self.substitutions[idx] = other
        else:
            self.constraints.append((other, current))

    # recursively substitute all the existential types with their final concrete types
    def substitute(self) -> List[Type]:
        for idx in range(len(self.substitutions)):
            self._check_consistency(self.substitutions[idx], [idx])
        return [self._substitute_type(ty) for ty in self.substitutions]

    # recursively substitute the existentials types within a specific type
    def _substitute_type(self, ty: Type) -> Type:
        if isinstance(ty, ExistentialType):
            replacement = self.substitutions[ty.idx]
            if isinstance(replacement, ExistentialType) and replacement.idx == ty.idx:
                return replacement
            return self._substitute_type(replacement)
        if isinstance(ty, IdType):
            return IdType(ty.name, [self._substitute_type(generic) for generic in ty.generics])
        return ty

    # Ensure that all existentials are fully inferred, and there are no recursive types
    def _check_consistency(self, ty: Type, stack: List[int]) -> None:
        if isinstance(ty, ExistentialType):
            if ty.idx == stack[-1]:
                data = self.existentials[ty.idx]
                raise self.type_propagator.new_error(
                    data.function_name_span,
                    f"unable to infer generics in function '{data.function_name}'",
                )
            if ty.idx in stack:
                data = self.existentials[ty.idx]
                raise self.type_propagator.new_error(
                    data.function_name_span,
                    f"Infinitely recursive type found during type inference of function `{data.function_name}`",
                )
            self._check_consistency(self.substitutions[ty.idx], stack + [ty.idx])
        elif isinstance(ty, IdType):
            for generic in ty.generics:
                self._check_consistency(generic, stack)

class TypePropagator:
    def __init__(
        self,
        ast: Ast,
        mod: str,
        entity_type: str,
        mod_api: ModApi,
        mods_dir_path: Path,
        file_path: Path,
        source_text: str,
    ):
        self.ast = ast
        self.mod = mod
        self.file_entity_type = entity_type
        self.mod_api = mod_api
        self.mods_dir_path = mods_dir_path
        self.file_path = file_path
        self.source_text = source_text

        self.on_fns: Dict[str, OnFn] = {
            s.fn_name: s for s in ast if isinstance(s, OnFn)
        }

        self.helper_fns = {s.fn_name: s for s in ast if isinstance(s, HelperFn)}

        self.fn_return_type = None
        self.filled_fn_name: Optional[str] = None

        self.local_variables: Dict[str, Variable] = {}
        self.global_variables: Dict[str, Variable] = {}

        self.entity_on_functions = {
            name: export_fn
            for (name, export_fn) in mod_api.entities[entity_type].export_fns
        }

    def new_error(self, err_span: SourceSpan, error_message: str) -> GrugError:
        return GrugError.new_compile_error(
            self.file_path,
            self.filled_fn_name,
            self.source_text,
            err_span,
            error_message,
        )

    def add_global_variable(
        self, name: str, var_type: Type, span: SourceSpan
    ):
        if name in self.global_variables:
            raise self.new_error(
                span, f"The global variable '{name}' shadows an earlier global variable"
            )

        var = Variable(name, var_type)
        self.global_variables[name] = var

    def get_variable(self, name: str):
        if name in self.local_variables:
            return self.local_variables[name]
        if name in self.global_variables:
            return self.global_variables[name]
        return None

    def add_local_variable(
        self, name: str, var_type: Type, span: SourceSpan
    ):
        if name in self.local_variables:
            raise self.new_error(
                span, f"The local variable '{name}' shadows an earlier local variable"
            )

        if name in self.global_variables:
            raise self.new_error(
                span, f"The local variable '{name}' shadows an earlier global variable"
            )

        var = Variable(name, var_type)
        self.local_variables[name] = var

    def verify_generics(self, ty: Type, err_span: SourceSpan) -> None:
        if not isinstance(ty, IdType):
            return

        mod_api_class = self.mod_api.classes.get(ty.name)
        expected_generics = len(mod_api_class.generics) if mod_api_class else 0
        if len(ty.generics) != expected_generics:
            raise self.new_error(
                err_span,
                f"type {ty.name} has {expected_generics} generics, but was given {len(ty.generics)}",
            )

        for generic in ty.generics:
            self.verify_generics(generic, err_span)

    def validate_entity_string(self, string: str, span: SourceSpan):
        if not string:
            raise self.new_error(span, "Entities can't be empty strings")

        mod = self.mod
        entity_name = string

        colon_pos = string.find(":")
        if colon_pos != -1:
            if colon_pos == 0:
                raise self.new_error(span, f"Entity '{string}' is missing a mod name")

            temp_mod_name = string[:colon_pos]

            mod = temp_mod_name
            entity_name = string[colon_pos + 1 :]

            if not entity_name:
                raise self.new_error(span, f"Entity '{string}' missing entity name")

            if mod == self.mod:
                raise self.new_error(
                    span, f"Entity string ('{string}') cannot refer to its own mod"
                )

        for c in mod:
            if not (c.islower() or c.isdigit() or c in ("_", "-")):
                raise self.new_error(
                    span,
                    f"Entity '{string}' its mod name contains the invalid character '{c}'",
                )

        for c in entity_name:
            if not (c.islower() or c.isdigit() or c in ("_", "-")):
                raise self.new_error(
                    span,
                    f"Entity '{string}' its entity name contains the invalid character '{c}'",
                )

    def validate_resource_string(
        self, string: str, resource_extension: Optional[str], span: SourceSpan
    ):
        if not string:
            raise self.new_error(span, "Resources can't be empty strings")

        if string.startswith("/"):
            raise self.new_error(
                span, f'Remove the leading slash from the resource "{string}"'
            )

        if string.endswith("/"):
            raise self.new_error(
                span, f'Remove the trailing slash from the resource "{string}"'
            )

        if "\\" in string:
            raise self.new_error(
                span, f"Replace the '\\' with '/' in the resource \"{string}\""
            )

        if "//" in string:
            raise self.new_error(
                span, f"Replace the '//' with '/' in the resource \"{string}\""
            )

        # '.' check
        dot_index = string.find(".")
        if dot_index != -1:
            # String starts with "."
            if dot_index == 0:
                if len(string) == 1 or string[1] == "/":
                    raise self.new_error(
                        span, f"Remove the '.' from the resource \"{string}\""
                    )

            # String starts with "./"
            elif string[dot_index - 1] == "/":
                # Next must not be "/" or end-of-string
                if dot_index + 1 == len(string) or string[dot_index + 1] == "/":
                    raise self.new_error(
                        span, f"Remove the '.' from the resource \"{string}\""
                    )

        # '..' check
        dotdot_index = string.find("..")
        if dotdot_index != -1:
            # String starts with ".."
            if dotdot_index == 0:
                if len(string) == 2 or string[2] == "/":
                    raise self.new_error(
                        span, f"Remove the '..' from the resource \"{string}\""
                    )

            # String starts with "../"
            elif string[dotdot_index - 1] == "/":
                # Next must not be "/" or end-of-string
                if dotdot_index + 2 == len(string) or string[dotdot_index + 2] == "/":
                    raise self.new_error(
                        span, f"Remove the '..' from the resource \"{string}\""
                    )

        if string.endswith("."):
            raise self.new_error(span, f'resource name "{string}" cannot end with .')

        if resource_extension and not string.endswith(resource_extension):
            raise self.new_error(
                span,
                f"The resource '{string}' was supposed to have the extension '{resource_extension}'",
            )

        full_path = self.mods_dir_path / Path(self.mod) / Path(string)
        if not os.path.exists(full_path):
            raise self.new_error(span, f"resource '{string}' does not exist")

    @staticmethod
    def convert_mod_api_type(mod_api_type: Type, replacements: List[Type]) -> Type:
        return substitute_type(mod_api_type, replacements)

    @staticmethod
    def format_type_list(types: List[Type]) -> str:
        return "[" + ", ".join(str(ty) for ty in types) + "]"

    def fill_host_fn_ptr(
        self,
        host_fn: ModApiHostFn,
        generics: List[Type],
        name_span: SourceSpan,
        function_name: str,
        method_receiver_name: Optional[str] = None,
    ) -> Optional[HostFn]:
        if len(generics) == 0:
            return host_fn.fn_ptr

        if host_fn.generic_reg_fn is None:
            if method_receiver_name is None:
                raise RuntimeError(
                    f"generic function {function_name} was not registered"
                )
            raise RuntimeError(
                f"generic method {method_receiver_name}.{function_name} was not registered"
            )

        fn_ptr = host_fn.generic_reg_fn(generics)
        if fn_ptr is None:
            type_list = self.format_type_list(generics)
            if method_receiver_name is None:
                raise self.new_error(
                    name_span,
                    f"generic function '{function_name}' instantiation failed for types {type_list}",
                )
            raise self.new_error(
                name_span,
                f"generic method {method_receiver_name}.{function_name} instantiation failed for types {type_list}",
            )
        return fn_ptr

    def fill_complete_expr(self, expr: Expr, expected_type: Optional[Type]) -> Type:
        ty_ctx = TyCtx(self.filled_fn_name or "member scope", self)
        expr_type = self.fill_expr(ty_ctx, None, expr)
        if expected_type is not None:
            ty_ctx.add_constraint(expr.expr_span, expected_type, expr_type)
        substitutions = ty_ctx.substitute()
        return self.fill_expr(TyCtx(self.filled_fn_name or "member scope", self), substitutions, expr)

    def fill_arguments(
        self,
        function_name: str,
        ty_ctx: TyCtx,
        substitutions: Optional[List[Type]],
        name_span: SourceSpan,
        signature: List[Parameter],
        arguments: List[Expr],
    ) -> None:
        if len(signature) > len(arguments):
            param = signature[len(arguments)]
            raise self.new_error(
                name_span,
                f"Function call '{function_name}' expected the argument '{param.name}' with type {param.type}",
            )
        if len(signature) < len(arguments):
            arg = arguments[len(signature)]
            got_type = self.fill_expr(ty_ctx, substitutions, arg)
            raise self.new_error(
                arg.expr_span,
                f"Function call '{function_name}' got an unexpected extra argument with type {got_type}",
            )

        for param, arg in zip(signature, arguments):
            arg_result_ty = self.fill_expr(ty_ctx, substitutions, arg)

            if isinstance(param.type, ResourceStrType) and isinstance(arg, ResourceExpr):
                if substitutions is not None:
                    self.validate_resource_string(arg.string, param.type.extension, arg.expr_span)
            elif isinstance(param.type, EntityStrType) and isinstance(arg, EntityExpr):
                if substitutions is not None:
                    self.validate_entity_string(arg.string, arg.expr_span)
            elif isinstance(param.type, ResourceStrType) and isinstance(arg, StringExpr):
                raise self.new_error(
                    arg.expr_span,
                    f"The host function '{function_name}' expects a resource string, so put an 'r' in front of string \"{arg.string}\"",
                )
            elif isinstance(param.type, EntityStrType) and isinstance(arg, StringExpr):
                raise self.new_error(
                    arg.expr_span,
                    f"The host function '{function_name}' expects an entity string, so put an 'e' in front of string \"{arg.string}\"",
                )
            elif arg_result_ty == PrimitiveType.VOID:
                raise self.new_error(
                    arg.expr_span,
                    f"Function call '{function_name}' expected the type {param.type} for argument '{param.name}', but got a function call that doesn't return anything",
                )
            elif type_matches(arg_result_ty, param.type):
                try:
                    ty_ctx.add_constraint(arg.expr_span, param.type, arg_result_ty)
                except TypeMismatch as mismatch:
                    raise self.new_error(
                        mismatch.span,
                        f"Function call '{function_name}' expected the type {type_diff(mismatch.expected, mismatch.actual)} for argument '{param.name}', but got {type_diff(mismatch.actual, mismatch.expected)}",
                    ) from mismatch
            else:
                raise self.new_error(
                    arg.expr_span,
                    f"Function call '{function_name}' expected the type {type_diff(param.type, arg_result_ty)} for argument '{param.name}', but got {type_diff(arg_result_ty, param.type)}",
                )

    # Creates existentials for the generics of a host function. 
    # substitues the existentials if available
    def _call_generics(
        self,
        ty_ctx: TyCtx,
        substitutions: Optional[List[Type]],
        function_name: str,
        function_name_span: SourceSpan,
        generic_names: List[str],
    ) -> List[Type]:
        result: List[Type] = []
        for _ in generic_names:
            existential = ty_ctx.create_existential(function_name, function_name_span)
            if substitutions is None:
                result.append(existential)
            else:
                result.append(substitutions[existential.idx])
        return result

    def fill_expr(
        self, ty_ctx: TyCtx, substitutions: Optional[List[Type]], expr: Expr
    ) -> Type:
        if isinstance(expr, TrueExpr):
            result_ty: Type = PrimitiveType.BOOL
        elif isinstance(expr, FalseExpr):
            result_ty = PrimitiveType.BOOL
        elif isinstance(expr, StringExpr):
            result_ty = PrimitiveType.STRING
        elif isinstance(expr, ResourceExpr):
            result_ty = ResourceStrType(extension="")
        elif isinstance(expr, EntityExpr):
            result_ty = EntityStrType(entity_type=None)
        elif isinstance(expr, IdentifierExpr):
            var = self.get_variable(expr.name)
            if not var:
                raise self.new_error(
                    expr.expr_span, f"The variable '{expr.name}' does not exist"
                )
            result_ty = var.type
        elif isinstance(expr, NumberExpr):
            result_ty = PrimitiveType.NUMBER
        elif isinstance(expr, UnaryExpr):
            result_ty = self._fill_unary_expr(ty_ctx, substitutions, expr)
        elif isinstance(expr, (BinaryExpr, LogicalExpr)):
            result_ty = self._fill_binary_expr(ty_ctx, substitutions, expr)
        elif isinstance(expr, CallExpr):
            result_ty = self._fill_call_expr(ty_ctx, substitutions, expr)
        else:
            assert isinstance(expr, ParenthesizedExpr)
            result_ty = self.fill_expr(ty_ctx, substitutions, expr.expr)

        expr.result = result_ty
        return result_ty

    def _fill_unary_expr(
        self, ty_ctx: TyCtx, substitutions: Optional[List[Type]], expr: UnaryExpr
    ) -> Type:
        if isinstance(expr.expr, UnaryExpr) and expr.expr.operator == expr.operator:
            raise self.new_error(
                expr.op_span,
                f"Found {expr.operator} directly next to another {expr.operator}, which can be simplified by just removing both of them",
            )

        result_ty = self.fill_expr(ty_ctx, substitutions, expr.expr)
        expected = PrimitiveType.BOOL if expr.operator == TokenType.NOT_TOKEN else PrimitiveType.NUMBER
        op_text = "not" if expr.operator == TokenType.NOT_TOKEN else "-"
        expected_name = "bool" if expr.operator == TokenType.NOT_TOKEN else "number"

        if isinstance(result_ty, ExistentialType):
            try:
                ty_ctx.add_constraint(expr.op_span, expected, result_ty)
            except TypeMismatch as mismatch:
                raise self.new_error(
                    mismatch.span,
                    f"Found '{op_text}' before {type_diff(mismatch.actual, mismatch.expected)}, but it can only be put before a {expected_name}",
                ) from mismatch
        elif result_ty != expected:
            raise self.new_error(
                expr.op_span,
                f"Found '{op_text}' before {result_ty}, but it can only be put before a {expected_name}",
            )
        return result_ty

    def _fill_binary_expr(
        self, ty_ctx: TyCtx, substitutions: Optional[List[Type]], expr: Union[BinaryExpr, LogicalExpr]
    ) -> Type:
        left = expr.left_expr
        right = expr.right_expr
        result_0 = self.fill_expr(ty_ctx, substitutions, left)
        result_1 = self.fill_expr(ty_ctx, substitutions, right)
        op = expr.operator

        try:
            ty_ctx.add_constraint(expr.op_span, result_0, result_1)
        except TypeMismatch as mismatch:
            raise self.new_error(
                mismatch.span,
                f"The left and right operand of a binary expression ({op}) must have the same type, but got {type_diff(mismatch.expected, mismatch.actual)} and {type_diff(mismatch.actual, mismatch.expected)}",
            ) from mismatch

        current_0 = ty_ctx.get_current_type(result_0) or result_0
        current_1 = ty_ctx.get_current_type(result_1) or result_1

        if current_0 == PrimitiveType.STRING and current_1 == PrimitiveType.STRING:
            if op not in (TokenType.EQUALS_TOKEN, TokenType.NOT_EQUALS_TOKEN):
                if op == TokenType.PLUS_TOKEN:
                    raise self.new_error(expr.op_span, "cannot add strings with '+'")
                raise self.new_error(expr.op_span, f"You can't use the {op} operator on strings")

        if op in (TokenType.AND_TOKEN, TokenType.OR_TOKEN):
            expected_type: Type = PrimitiveType.BOOL
            result_type: Type = PrimitiveType.BOOL
        elif op in (TokenType.EQUALS_TOKEN, TokenType.NOT_EQUALS_TOKEN):
            expected_type = current_0
            result_type = PrimitiveType.BOOL
        elif op in (
            TokenType.GREATER_OR_EQUAL_TOKEN,
            TokenType.GREATER_TOKEN,
            TokenType.LESS_OR_EQUAL_TOKEN,
            TokenType.LESS_TOKEN,
        ):
            expected_type = PrimitiveType.NUMBER
            result_type = PrimitiveType.BOOL
        else:
            expected_type = PrimitiveType.NUMBER
            result_type = PrimitiveType.NUMBER

        for expr_result, expr_span in ((current_0, left.expr_span), (current_1, right.expr_span)):
            if isinstance(expr_result, ExistentialType):
                try:
                    ty_ctx.add_constraint(expr_span, expected_type, expr_result)
                except TypeMismatch as mismatch:
                    raise self.new_error(
                        mismatch.span,
                        f"{op} operator expects {expected_type} but got {type_diff(mismatch.actual, mismatch.expected)}",
                    ) from mismatch
            elif expr_result != expected_type:
                raise self.new_error(
                    expr.op_span,
                    f"{op} operator expects {expected_type} but got {type_diff(expr_result, expected_type)}",
                )

        return result_type

    def _fill_call_expr(
        self, ty_ctx: TyCtx, substitutions: Optional[List[Type]], expr: CallExpr
    ) -> Type:
        fn_name = expr.fn_name

        if expr.receiver is None:
            if fn_name in self.helper_fns:
                helper_fn = self.helper_fns[fn_name]
                self.fill_arguments(fn_name, ty_ctx, substitutions, expr.name_span, helper_fn.parameters, expr.arguments)
                return helper_fn.return_type

            if fn_name in self.mod_api.host_fns:
                host_fn = self.mod_api.host_fns[fn_name]
                generics = self._call_generics(ty_ctx, substitutions, fn_name, expr.name_span, host_fn.generics)
                parameters = [
                    Parameter(param.name, self.convert_mod_api_type(param.type, generics), param.name_span, param.type_span)
                    for param in host_fn.parameters
                ]
                self.fill_arguments(fn_name, ty_ctx, substitutions, expr.name_span, parameters, expr.arguments)
                if substitutions is not None:
                    expr.fn_ptr = self.fill_host_fn_ptr(
                        host_fn, generics, expr.name_span, fn_name
                    )
                return self.convert_mod_api_type(host_fn.return_type, generics)

            if fn_name.startswith("_"):
                raise self.new_error(expr.name_span, f"The local function '{fn_name}' was not defined by this grug file")
            if fn_name in self.entity_on_functions:
                raise self.new_error(expr.name_span, "Mods aren't allowed to call their own export functions")
            raise self.new_error(expr.name_span, f"The game function '{fn_name}' was not declared by mod_api.json")

        return self._fill_method_expr(ty_ctx, substitutions, expr)

    def _fill_method_expr(
        self, ty_ctx: TyCtx, substitutions: Optional[List[Type]], expr: CallExpr
    ) -> Type:
        assert expr.receiver is not None
        if isinstance(expr.receiver, CallExpr):
            if expr.receiver.receiver is None:
                raise self.new_error(expr.receiver.expr_span, "Cannot call method on the result of a function call")
            raise self.new_error(expr.receiver.expr_span, "Method chaining is not allowed")

        receiver_type = self.fill_expr(ty_ctx, substitutions, expr.receiver)
        receiver_type = ty_ctx.get_current_type(receiver_type)
        if receiver_type is None:
            raise self.new_error(expr.receiver.expr_span, "Unable to infer type of method receiver")
        if not isinstance(receiver_type, IdType):
            raise self.new_error(expr.receiver.expr_span, f"Cannot call method on '{receiver_type}' type")

        receiver_name = receiver_type.name
        mod_api_class = self.mod_api.classes.get(receiver_name)
        if mod_api_class is None:
            raise self.new_error(expr.receiver.expr_span, f"Type '{receiver_name}' does not have any methods")

        host_fn = mod_api_class.methods.get(expr.fn_name)
        if host_fn is None:
            raise self.new_error(expr.receiver.expr_span, f"Cannot find method '{expr.fn_name}' on type '{receiver_name}'")

        generics = self._call_generics(ty_ctx, substitutions, expr.fn_name, expr.name_span, host_fn.generics)
        parameters = [
            Parameter(param.name, self.convert_mod_api_type(param.type, generics), param.name_span, param.type_span)
            for param in host_fn.parameters
        ]
        expected_receiver_type = self.convert_mod_api_type(mod_api_class.type, generics)
        try:
            ty_ctx.add_constraint(expr.receiver.expr_span, expected_receiver_type, receiver_type)
        except TypeMismatch as mismatch:
            raise self.new_error(
                mismatch.span,
                f"Expected {type_diff(mismatch.expected, mismatch.actual)} but got {type_diff(mismatch.actual, mismatch.expected)}",
            ) from mismatch

        self.fill_arguments(expr.fn_name, ty_ctx, substitutions, expr.name_span, parameters, expr.arguments)
        if substitutions is not None:
            expr.fn_ptr = self.fill_host_fn_ptr(
                host_fn, generics, expr.name_span, expr.fn_name, receiver_name
            )
        return self.convert_mod_api_type(host_fn.return_type, generics)

    def fill_variable_statement(self, stmt: VariableStatement):
        var = self.get_variable(stmt.name)

        if stmt.type:
            self.verify_generics(stmt.type, stmt.type_span)
            try:
                self.fill_complete_expr(stmt.expr, stmt.type)
            except TypeMismatch as mismatch:
                raise self.new_error(
                    mismatch.span,
                    f"Can't assign {type_diff(mismatch.actual, mismatch.expected)} to '{stmt.name}', which has type {type_diff(mismatch.expected, mismatch.actual)}",
                ) from mismatch

            self.add_local_variable(
                stmt.name, stmt.type, stmt.name_span
            )
        else:
            if not var:
                raise self.new_error(
                    stmt.name_span,
                    f"Can't assign to the variable '{stmt.name}', since it does not exist",
                )

            if stmt.name in self.global_variables and isinstance(var.type, IdType):
                raise self.new_error(
                    stmt.expr.expr_span, "Global id variables can't be reassigned"
                )

            try:
                self.fill_complete_expr(stmt.expr, var.type)
            except TypeMismatch as mismatch:
                raise self.new_error(
                    mismatch.span,
                    f"Can't assign {type_diff(mismatch.actual, mismatch.expected)} to '{var.name}', which has type {type_diff(mismatch.expected, mismatch.actual)}",
                ) from mismatch

    def remove_local_variables_in_statements(self, statements: List[Statement]):
        """
        Removes the local variables in the `statements` scope from `self.local_variables`,
        as those variables are unreachable after the scope has exited.
        """
        for stmt in statements:
            if isinstance(stmt, VariableStatement) and stmt.type:
                del self.local_variables[stmt.name]

    def fill_statements(self, statements: List[Statement]):
        for stmt in statements:
            if isinstance(stmt, VariableStatement):
                self.fill_variable_statement(stmt)
            elif isinstance(stmt, CallStatement):
                self.fill_complete_expr(stmt.expr, None)
            elif isinstance(stmt, IfStatement):
                while True:
                    try:
                        self.fill_complete_expr(stmt.condition, PrimitiveType.BOOL)
                    except TypeMismatch as mismatch:
                        raise self.new_error(
                            mismatch.span,
                            f"If condition must be bool but got '{type_diff(mismatch.actual, mismatch.expected)}'",
                        ) from mismatch
                    self.fill_statements(stmt.if_body)
                    if len(stmt.else_body) == 1 and isinstance(
                        stmt.else_body[0], IfStatement
                    ):
                        stmt = stmt.else_body[0]
                    else:
                        self.fill_statements(stmt.else_body)
                        break
            elif isinstance(stmt, ReturnStatement):
                if stmt.value:
                    if self.fn_return_type == PrimitiveType.VOID:
                        result_ty = self.fill_complete_expr(stmt.value, None)
                        raise self.new_error(
                            stmt.value.expr_span,
                            f"Function '{self.filled_fn_name}' wasn't supposed to return any value but it returned {result_ty}",
                        )
                    try:
                        self.fill_complete_expr(stmt.value, self.fn_return_type)
                    except TypeMismatch as mismatch:
                        raise self.new_error(
                            mismatch.span,
                            f"Function '{self.filled_fn_name}' is supposed to return {type_diff(mismatch.expected, mismatch.actual)}, not {type_diff(mismatch.actual, mismatch.expected)}",
                        ) from mismatch
                elif self.fn_return_type != PrimitiveType.VOID:
                    raise self.new_error(
                        stmt.return_span,
                        f"Function '{self.filled_fn_name}' is supposed to return a value of type {self.fn_return_type}",
                    )
            elif isinstance(stmt, WhileStatement):
                try:
                    self.fill_complete_expr(stmt.condition, PrimitiveType.BOOL)
                except TypeMismatch as mismatch:
                    raise self.new_error(
                        mismatch.span,
                        f"While condition must be bool but got '{type_diff(mismatch.actual, mismatch.expected)}'",
                    ) from mismatch
                self.fill_statements(stmt.body_statements)

        self.remove_local_variables_in_statements(statements)

    def add_parameter_variables(self, parameters: List[Parameter]):
        self.local_variables = {}

        for param in parameters:
            self.add_local_variable(param.name, param.type, param.name_span)

    def fill_helper_fns(self):
        for fn_name, fn in self.helper_fns.items():
            self.fn_return_type = fn.return_type
            self.filled_fn_name = fn_name

            for param in fn.parameters:
                self.verify_generics(param.type, param.type_span)
            self.verify_generics(fn.return_type, fn.span)
            self.add_parameter_variables(fn.parameters)

            self.fill_statements(fn.body_statements)

            if fn.return_type != PrimitiveType.VOID:
                # grug doesn't allow empty functions
                assert fn.body_statements

                if not isinstance(fn.body_statements[-1], ReturnStatement):
                    raise self.new_error(
                        fn.span,
                        f"Function '{self.filled_fn_name}' is supposed to return {self.fn_return_type} as its last line",
                    )

    def fill_on_fns(self):
        # Check for on_fns that aren't declared in the entity
        for fn_name in self.on_fns.keys():
            if fn_name not in self.entity_on_functions:
                self.filled_fn_name = fn_name
                raise self.new_error(
                    self.on_fns[fn_name].span,
                    f"The function '{fn_name}' was not declared by entity '{self.file_entity_type}' in mod_api.json",
                )

        # Create a list of parser on_fn names for index lookup
        parser_on_fn_names = list(self.on_fns.keys())

        # Check ordering and validate signatures by iterating through expected order
        previous_on_fn_index = 0
        for expected_fn_name in self.entity_on_functions.keys():
            if expected_fn_name not in self.on_fns:
                continue

            fn = self.on_fns[expected_fn_name]

            # Check ordering
            current_parser_index = parser_on_fn_names.index(expected_fn_name)
            if previous_on_fn_index > current_parser_index:
                self.filled_fn_name = expected_fn_name
                raise self.new_error(
                    fn.span,
                    f"The function '{expected_fn_name}' needs to be moved before or after a different export function, according to the entity '{self.file_entity_type}' in mod_api.json",
                )
            previous_on_fn_index = current_parser_index

            self.fn_return_type = PrimitiveType.VOID
            self.filled_fn_name = expected_fn_name

            params = self.entity_on_functions[expected_fn_name].parameters

            if len(fn.parameters) != len(params):
                if len(fn.parameters) < len(params):
                    raise self.new_error(
                        fn.span,
                        f"Function '{expected_fn_name}' expected the parameter '{params[len(fn.parameters)].name}' with type {params[len(fn.parameters)].type}",
                    )
                else:
                    raise self.new_error(
                        fn.parameters[len(params)].name_span,
                        f"Function '{expected_fn_name}' got an unexpected extra parameter '{fn.parameters[len(params)].name}' with type {fn.parameters[len(params)].type}",
                    )

            for arg, param in zip(fn.parameters, params):
                self.verify_generics(arg.type, arg.type_span)
                if arg.name != param.name:
                    raise self.new_error(
                        arg.name_span,
                        f"Function '{expected_fn_name}' its '{arg.name}' parameter was supposed to be named '{param.name}'",
                    )

                if arg.type != param.type:
                    raise self.new_error(
                        arg.type_span,
                        f"Function '{expected_fn_name}' its '{param.name}' parameter was supposed to have the type {param.type}, but got {arg.type}",
                    )

            self.add_parameter_variables(fn.parameters)
            self.fill_statements(fn.body_statements)

    def check_global_expr(self, expr: Expr, name: str):
        """Check that global variables don't call helper fns"""
        if isinstance(expr, UnaryExpr):
            self.check_global_expr(expr.expr, name)
        elif isinstance(expr, (BinaryExpr, LogicalExpr)):
            self.check_global_expr(expr.left_expr, name)
            self.check_global_expr(expr.right_expr, name)
        elif isinstance(expr, CallExpr):
            if expr.fn_name.startswith("_"):
                raise self.new_error(
                    expr.name_span,
                    f"The global variable '{name}' isn't allowed to call local functions",
                )
            for arg in expr.arguments:
                self.check_global_expr(arg, name)
        elif isinstance(expr, ParenthesizedExpr):
            self.check_global_expr(expr.expr, name)

    def fill_global_variables(self):
        # Add the implicit 'me' variable
        self.global_variables["me"] = Variable("me", IdType(self.file_entity_type))

        # Process global variable statements
        for stmt in self.ast:
            if isinstance(stmt, VariableStatement):
                # Global variables are guaranteed to be initialized
                assert stmt.type
                assert stmt.expr

                self.verify_generics(stmt.type, stmt.type_span)
                self.check_global_expr(stmt.expr, stmt.name)
                try:
                    self.fill_complete_expr(stmt.expr, stmt.type)
                except TypeMismatch as mismatch:
                    raise self.new_error(
                        mismatch.span,
                        f"Can't assign {type_diff(mismatch.actual, mismatch.expected)} to '{stmt.name}', which has type {type_diff(mismatch.expected, mismatch.actual)}",
                    ) from mismatch

                # Check for assignment to 'me'
                if isinstance(stmt.expr, IdentifierExpr):
                    if stmt.expr.name == "me":
                        raise self.new_error(
                            stmt.expr.expr_span,
                            "Global variables can't be assigned 'me'",
                        )

                self.add_global_variable(
                    stmt.name, stmt.type, stmt.name_span
                )

    def fill(self):
        """Main entry point for type propagation"""
        self.fill_global_variables()
        self.fill_on_fns()
        self.fill_helper_fns()
