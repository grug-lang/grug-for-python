from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union
import os

from .error import GrugError, SourceSpan
from .parser import (
    Ast,
    BinaryExpr,
    CallExpr,
    CallStatement,
    EntityExpr,
    Expr,
    HelperFn,
    IdentifierExpr,
    IfStatement,
    LogicalExpr,
    OnFn,
    ParenthesizedExpr,
    Parameter,
    ResourceExpr,
    ReturnStatement,
    Statement,
    StringExpr,
    Type,
    PrimitiveType,
	IdType,
	EntityStrType,
	ResourceStrType,
    UnaryExpr,
    VariableStatement,
    WhileStatement,
)
from .tokenizer import TokenType
from .mod_api import ModApi


@dataclass
class Variable:
    name: str
    type: Type

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

    def check_arguments(self, params: List[Parameter], call_expr: CallExpr):
        fn_name = call_expr.fn_name
        args = call_expr.arguments

        if len(args) < len(params):
            raise self.new_error(
                call_expr.name_span,
                f"Function call '{fn_name}' expected the argument '{params[len(args)].name}' with type {params[len(args)].type}",
            )

        if len(args) > len(params):
            raise self.new_error(
                call_expr.arguments[len(params)].expr_span, f"Function call '{fn_name}' got an unexpected extra argument with type {call_expr.arguments[len(params)].result}",
            )

        for arg, param in zip(args, params):
            if isinstance(arg, StringExpr) and isinstance(param.type, EntityStrType):
                raise self.new_error(
                    arg.expr_span,
                    f"The host function '{fn_name}' expects an entity string, so put an 'e' in front of string \"{arg.string}\"",
                )
            if isinstance(arg, StringExpr) and isinstance(param.type, ResourceStrType):
                raise self.new_error(
                    arg.expr_span,
                    f"The host function '{fn_name}' expects a resource string, so put an 'r' in front of string \"{arg.string}\"",
                )

            if isinstance(arg, EntityExpr):
                self.validate_entity_string(arg.string, arg.expr_span)
            elif isinstance(arg, ResourceExpr):
                param_type = param.type
                assert(isinstance(param_type, ResourceStrType))
                self.validate_resource_string(
                    arg.string, param_type.extension, arg.expr_span
                )

            if arg.result == PrimitiveType.VOID:
                raise self.new_error(
                    arg.expr_span,
                    f"Function call '{fn_name}' expected the type {param.type} for argument '{param.name}', but got a function call that doesn't return anything",
                )

            if param.type != arg.result:
                raise self.new_error(
                    arg.expr_span,
                    f"Function call '{fn_name}' expected the type {param.type} for argument '{param.name}', but got {arg.result}",
                )

    def fill_call_expr(self, expr: CallExpr):
        # Fill argument expressions first
        for arg in expr.arguments:
            self.fill_expr(arg)

        fn_name = expr.fn_name

        # Check if it's a helper function
        if fn_name in self.helper_fns:
            helper_fn = self.helper_fns[fn_name]
            expr.result = helper_fn.return_type
            self.check_arguments(helper_fn.parameters, expr)
            return

        # Check if it's a game function
        if fn_name in self.mod_api.host_fns:
            host_fn = self.mod_api.host_fns[fn_name]
            expr.result = host_fn.return_type
            self.check_arguments(host_fn.parameters, expr)
            return

        if fn_name.startswith("_"):
            raise self.new_error(
                expr.name_span,
                f"The local function '{fn_name}' was not defined by this grug file",
            )

        if fn_name in self.entity_on_functions:
            raise self.new_error(
                expr.name_span, "Mods aren't allowed to call their own export functions"
            )

        raise self.new_error(
            expr.name_span,
            f"The game function '{fn_name}' was not declared by mod_api.json",
        )

    def fill_method_expr(self, expr: CallExpr):
        # Fill argument expressions first
        assert expr.receiver
        # method chaining is not allowed
        if isinstance(expr.receiver, CallExpr):
            if expr.receiver.receiver == None:
                raise self.new_error(
                    expr.expr_span,
                    f"Cannot call method on the result of a function call",
                )
            else:
                raise self.new_error(
                    expr.expr_span,
                    f"Method chaining is not allowed",
                )

        self.fill_expr(expr.receiver)
        if isinstance(expr.receiver.result, IdType):
            receiver_type = expr.receiver.result
        else:
            raise self.new_error(
                expr.expr_span,
                f"Cannot call method on '{expr.receiver.result}' type",
            )

        for arg in expr.arguments:
            self.fill_expr(arg)

        if receiver_type.name in self.mod_api.classes:
            available_methods = self.mod_api.classes[receiver_type.name].methods
            if expr.fn_name not in available_methods:
                raise self.new_error(
                    expr.expr_span,
                    f"Cannot find method '{expr.fn_name}' on type '{receiver_type}'",
                )
            method = available_methods[expr.fn_name]
            self.check_arguments(method.parameters, expr)
            expr.result = method.return_type
            return
        else:
            raise self.new_error(
                expr.expr_span,
                f"Type '{receiver_type}' does not have any methods",
            )

    def fill_binary_expr(self, expr: Union[BinaryExpr, LogicalExpr]):
        left = expr.left_expr
        right = expr.right_expr

        self.fill_expr(left)
        self.fill_expr(right)

        op = expr.operator

        if left.result == PrimitiveType.STRING and right.result == PrimitiveType.STRING:
            if op not in (TokenType.EQUALS_TOKEN, TokenType.NOT_EQUALS_TOKEN):
                if op == TokenType.PLUS_TOKEN and right.result == PrimitiveType.STRING:
                    raise self.new_error(expr.op_span, "cannot add strings with '+'")
                raise self.new_error(
                    expr.op_span, f"You can't use the {op} operator on strings"
                )

        if left.result != right.result:
            raise self.new_error(
                expr.op_span,
                f"The left and right operand of a binary expression ({op}) must have the same type, but got {left.result} and {right.result}",
            )

        if op in (TokenType.EQUALS_TOKEN, TokenType.NOT_EQUALS_TOKEN):
            expr.result = PrimitiveType.BOOL
        elif op in (
            TokenType.GREATER_OR_EQUAL_TOKEN,
            TokenType.GREATER_TOKEN,
            TokenType.LESS_OR_EQUAL_TOKEN,
            TokenType.LESS_TOKEN,
        ):
            if left.result != PrimitiveType.NUMBER:
                raise self.new_error(expr.op_span, f"{op} operator expects number but got {left.result}")
            expr.result = PrimitiveType.BOOL
        elif op in (TokenType.AND_TOKEN, TokenType.OR_TOKEN):
            if left.result != PrimitiveType.BOOL:
                raise self.new_error(expr.op_span, f"{op} operator expects bool but got {left.result}")
            expr.result = PrimitiveType.BOOL
        else:
            assert op in (
                TokenType.PLUS_TOKEN,
                TokenType.MINUS_TOKEN,
                TokenType.MULTIPLICATION_TOKEN,
                TokenType.DIVISION_TOKEN,
            )

            if left.result != PrimitiveType.NUMBER:
                raise self.new_error(expr.op_span, f"{op} operator expects number but got {left.result}")
            expr.result = PrimitiveType.NUMBER

    def fill_expr(self, expr: Expr):
        if isinstance(expr, IdentifierExpr):
            var = self.get_variable(expr.name)
            if not var:
                raise self.new_error(
                    expr.expr_span, f"The variable '{expr.name}' does not exist"
                )
            expr.result = var.type
        elif isinstance(expr, UnaryExpr):
            op = expr.operator
            inner = expr.expr

            # Check for double unary
            if isinstance(inner, UnaryExpr) and inner.operator == op:
                raise self.new_error(
                    expr.op_span,
                    f"Found {op} directly next to another {op}, which can be simplified by just removing both of them",
                )

            self.fill_expr(inner)
            expr.result = inner.result

            if op == TokenType.NOT_TOKEN:
                if expr.result != PrimitiveType.BOOL:
                    raise self.new_error(
                        expr.op_span,
                        f"Found 'not' before {expr.result}, but it can only be put before a bool",
                    )
            else:
                assert op == TokenType.MINUS_TOKEN
                if expr.result != PrimitiveType.NUMBER:
                    raise self.new_error(
                        expr.op_span,
                        f"Found '-' before {expr.result}, but it can only be put before a number",
                    )
        elif isinstance(expr, (BinaryExpr, LogicalExpr)):
            self.fill_binary_expr(expr)
        elif isinstance(expr, CallExpr):
            if expr.receiver == None:
                self.fill_call_expr(expr)
            else:
                self.fill_method_expr(expr)
        elif isinstance(expr, ParenthesizedExpr):
            self.fill_expr(expr.expr)
            expr.result = expr.expr.result

    def fill_variable_statement(self, stmt: VariableStatement):
        # This call has to happen before the `add_local_variable()` we do below,
        # since `a: number = a` doesn't throw otherwise.
        self.fill_expr(stmt.expr)

        var = self.get_variable(stmt.name)

        if stmt.type:
            if stmt.type != stmt.expr.result:
                raise self.new_error(
                    stmt.expr.expr_span,
                    f"Can't assign {stmt.expr.result} to '{stmt.name}', which has type {stmt.type}",
                )

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

            if var.type != stmt.expr.result:
                raise self.new_error(
                    stmt.expr.expr_span,
                    f"Can't assign {stmt.expr.result} to '{var.name}', which has type {var.type}",
                )

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
                if stmt.expr.receiver == None:
                    self.fill_call_expr(stmt.expr)
                else:
                    self.fill_method_expr(stmt.expr)
            elif isinstance(stmt, IfStatement):
                while True:
                    self.fill_expr(stmt.condition)
                    if stmt.condition.result != PrimitiveType.BOOL:
                        raise self.new_error(
                            stmt.condition.expr_span,
                            f"If condition must be bool but got '{stmt.condition.result}'",
                        )
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
                    self.fill_expr(stmt.value)

                    if self.fn_return_type == PrimitiveType.VOID:
                        raise self.new_error(
                            stmt.value.expr_span,
                            f"Function '{self.filled_fn_name}' wasn't supposed to return any value but it returned {stmt.value.result}",
                        )

                    if self.fn_return_type != stmt.value.result:
                        raise self.new_error(
                            stmt.value.expr_span,
                            f"Function '{self.filled_fn_name}' is supposed to return {self.fn_return_type}, not {stmt.value.result}",
                        )
                elif self.fn_return_type:
                    raise self.new_error(
                        stmt.return_span,
                        f"Function '{self.filled_fn_name}' is supposed to return a value of type {self.fn_return_type}",
                    )
            elif isinstance(stmt, WhileStatement):
                self.fill_expr(stmt.condition)
                if stmt.condition.result != PrimitiveType.BOOL:
                    raise self.new_error(
                        stmt.condition.expr_span,
                        f"While condition must be bool but got '{stmt.condition.result}'",
                    )
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

            self.add_parameter_variables(fn.parameters)

            self.fill_statements(fn.body_statements)

            if fn.return_type:
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

                self.check_global_expr(stmt.expr, stmt.name)
                self.fill_expr(stmt.expr)

                # Check for assignment to 'me'
                if isinstance(stmt.expr, IdentifierExpr):
                    if stmt.expr.name == "me":
                        raise self.new_error(
                            stmt.expr.expr_span,
                            "Global variables can't be assigned 'me'",
                        )

                if stmt.type != stmt.expr.result:
                    raise self.new_error(
                        stmt.expr.expr_span,
                        f"Can't assign {stmt.expr.result} to '{stmt.name}', which has type {stmt.type}",
                    )

                self.add_global_variable(
                    stmt.name, stmt.type, stmt.name_span
                )

    def fill(self):
        """Main entry point for type propagation"""
        self.fill_global_variables()
        self.fill_on_fns()
        self.fill_helper_fns()
