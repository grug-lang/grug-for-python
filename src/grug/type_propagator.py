from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from .parser import (
    Argument,
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
    Parser,
    ResourceExpr,
    ReturnStatement,
    Statement,
    StringExpr,
    Type,
    UnaryExpr,
    VariableStatement,
    WhileStatement,
)
from .tokenizer import TokenType


@dataclass
class Variable:
    name: str
    type: Optional[Type]
    type_name: Optional[str]


@dataclass
class GameFn:
    fn_name: str
    arguments: List[Argument] = field(default_factory=lambda: [])
    return_type: Optional[Type] = None
    return_type_name: Optional[str] = None


class TypePropagationError(Exception):
    pass


ModApi = Dict[str, Dict[str, Any]]


class TypePropagator:
    def __init__(self, ast: Ast, mod: str, entity_type: str, mod_api: ModApi):
        self.ast = ast
        self.mod = mod
        self.file_entity_type = entity_type
        self.mod_api = mod_api

        self.on_fns: Dict[str, OnFn] = {
            s.fn_name: s for s in ast if isinstance(s, OnFn)
        }

        self.helper_fns = {s.fn_name: s for s in ast if isinstance(s, HelperFn)}

        self.fn_return_type = None
        self.fn_return_type_name = None
        self.filled_fn_name = None

        self.local_variables: Dict[str, Variable] = {}
        self.global_variables: Dict[str, Variable] = {}

        def parse_args(lst: List[Any]):
            return [
                Argument(
                    obj["name"],
                    Parser.parse_type(obj["type"]),
                    obj["type"],
                    obj.get("resource_extension"),
                    obj.get("entity_type"),
                )
                for obj in lst
            ]

        def parse_game_fn(fn_name: str, fn: Dict[str, Any]):
            return GameFn(
                fn_name,
                parse_args(fn.get("arguments", [])),
                Parser.parse_type(fn["return_type"]) if "return_type" in fn else None,
                fn.get("return_type", None),
            )

        self.game_functions = {
            fn_name: parse_game_fn(fn_name, fn)
            for fn_name, fn in mod_api["game_functions"].items()
        }

        self.entity_on_functions = mod_api["entities"][entity_type].get(
            "on_functions", {}
        )

    def add_global_variable(self, name: str, var_type: Type, type_name: str):
        if name in self.global_variables:
            raise TypePropagationError(
                f"The global variable '{name}' shadows an earlier global variable with the same name, so change the name of one of them"
            )

        var = Variable(name, var_type, type_name)
        self.global_variables[name] = var

    def get_variable(self, name: str):
        if name in self.local_variables:
            return self.local_variables[name]
        if name in self.global_variables:
            return self.global_variables[name]
        return None

    def add_local_variable(self, name: str, var_type: Type, type_name: str):
        if name in self.local_variables:
            raise TypePropagationError(
                f"The local variable '{name}' shadows an earlier local variable"
            )

        if name in self.global_variables:
            raise TypePropagationError(
                f"The local variable '{name}' shadows an earlier global variable"
            )

        var = Variable(name, var_type, type_name)
        self.local_variables[name] = var

    def is_wrong_type(
        self,
        a: Optional[Type],
        b: Optional[Type],
        a_name: Optional[str],
        b_name: Optional[str],
    ):
        if a != b:
            return True
        if a != Type.ID:
            return False
        return a_name != b_name

    def validate_entity_string(self, string: str):
        if not string:
            raise TypePropagationError("Entities can't be empty strings")

        mod = self.mod
        entity_name = string

        colon_pos = string.find(":")
        if colon_pos != -1:
            if colon_pos == 0:
                raise TypePropagationError(f"Entity '{string}' is missing a mod name")

            temp_mod_name = string[:colon_pos]

            mod = temp_mod_name
            entity_name = string[colon_pos + 1 :]

            if not entity_name:
                raise TypePropagationError(
                    f"Entity '{string}' specifies the mod name '{mod}', but it is missing an entity name after the ':'"
                )

            if mod == self.mod:
                raise TypePropagationError(
                    f"Entity '{string}' its mod name '{mod}' is invalid, since the file it is in refers to its own mod; just change it to '{entity_name}'"
                )

        for c in mod:
            if not (c.islower() or c.isdigit() or c in ("_", "-")):
                raise TypePropagationError(
                    f"Entity '{string}' its mod name contains the invalid character '{c}'"
                )

        for c in entity_name:
            if not (c.islower() or c.isdigit() or c in ("_", "-")):
                raise TypePropagationError(
                    f"Entity '{string}' its entity name contains the invalid character '{c}'"
                )

    def validate_resource_string(self, string: str, resource_extension: Optional[str]):
        if not string:
            raise TypePropagationError("Resources can't be empty strings")

        if string.startswith("/"):
            raise TypePropagationError(
                f'Remove the leading slash from the resource "{string}"'
            )

        if string.endswith("/"):
            raise TypePropagationError(
                f'Remove the trailing slash from the resource "{string}"'
            )

        if "\\" in string:
            raise TypePropagationError(
                f"Replace the '\\' with '/' in the resource \"{string}\""
            )

        if "//" in string:
            raise TypePropagationError(
                f"Replace the '//' with '/' in the resource \"{string}\""
            )

        # Dot '.' check
        dot_index = string.find(".")
        if dot_index != -1:
            # Case 1: String starts with "."
            if dot_index == 0:
                if len(string) == 1 or string[1] == "/":
                    raise TypePropagationError(
                        f"Remove the '.' from the resource \"{string}\""
                    )

            # Case 2: A path segment begins with "./"
            elif string[dot_index - 1] == "/":
                # Next must not be "/" or end-of-string
                if dot_index + 1 == len(string) or string[dot_index + 1] == "/":
                    raise TypePropagationError(
                        f"Remove the '.' from the resource \"{string}\""
                    )

        # Dot dot '..' check
        dotdot_index = string.find("..")
        if dotdot_index != -1:
            # Case 1: String starts with ".."
            if dotdot_index == 0:
                if len(string) == 2 or string[2] == "/":
                    raise TypePropagationError(
                        f"Remove the '..' from the resource \"{string}\""
                    )

            # Case 2: Path segment begins with "../"
            elif string[dotdot_index - 1] == "/":
                # Next must not be "/" or end-of-string
                if dotdot_index + 2 == len(string) or string[dotdot_index + 2] == "/":
                    raise TypePropagationError(
                        f"Remove the '..' from the resource \"{string}\""
                    )

        if string.endswith("."):
            raise TypePropagationError(f'resource name "{string}" cannot end with .')

        if resource_extension and not string.endswith(resource_extension):
            # TODO: Add an err/ test for this
            raise TypePropagationError(
                f"The resource '{string}' was supposed to have the extension '{resource_extension}'"
            )

    def check_arguments(self, params: List[Argument], call_expr: CallExpr):
        fn_name = call_expr.fn_name
        args = call_expr.arguments

        if len(args) < len(params):
            raise TypePropagationError(
                f"Function call '{fn_name}' expected the argument '{params[len(args)].name}' with type {params[len(args)].type_name}"
            )

        if len(args) > len(params):
            raise TypePropagationError(
                f"Function call '{fn_name}' got an unexpected extra argument with type {call_expr.arguments[len(params)].result.type_name}"
            )

        for i, (arg, param) in enumerate(zip(args, params)):
            # Handle resource/entity string conversions
            if isinstance(arg, StringExpr) and param.type == Type.RESOURCE:
                arg = ResourceExpr(arg.string)
                self.validate_resource_string(arg.string, param.resource_extension)
                args[i] = arg
            elif isinstance(arg, StringExpr) and param.type == Type.ENTITY:
                arg = EntityExpr(arg.string)
                self.validate_entity_string(arg.string)
                args[i] = arg

            if not arg.result.type:
                raise TypePropagationError(
                    f"Function call '{fn_name}' expected the type {param.type_name} for argument '{param.name}', but got a function call that doesn't return anything"
                )

            if not (param.type_name == "id" and arg.result.type ==
                Type.ID) and param.type_name != arg.result.type_name:
                raise TypePropagationError(
                    f"Function call '{fn_name}' expected the type {param.type_name} for argument '{param.name}', but got {arg.result.type_name}"
                )

    def fill_call_expr(self, expr: CallExpr):
        # Fill argument expressions first
        for arg in expr.arguments:
            self.fill_expr(arg)

        fn_name = expr.fn_name

        # Check if it's a helper function
        if fn_name in self.helper_fns:
            helper_fn = self.helper_fns[fn_name]
            expr.result.type = helper_fn.return_type
            expr.result.type_name = helper_fn.return_type_name
            self.check_arguments(helper_fn.arguments, expr)
            return

        # Check if it's a game function
        if fn_name in self.game_functions:
            game_fn = self.game_functions[fn_name]
            expr.result.type = game_fn.return_type
            expr.result.type_name = game_fn.return_type_name
            self.check_arguments(game_fn.arguments, expr)
            return

        if fn_name.startswith("on_"):
            raise TypePropagationError(
                f"Mods aren't allowed to call their own on_ functions, but '{fn_name}' was called"
            )

        if fn_name.startswith("helper_"):
            raise TypePropagationError(
                f"The helper function '{fn_name}' was not defined by this grug file"
            )

        raise TypePropagationError(
            f"The game function '{fn_name}' was not declared by mod_api.json"
        )

    def fill_binary_expr(self, expr: Union[BinaryExpr, LogicalExpr]):
        left = expr.left_expr
        right = expr.right_expr

        self.fill_expr(left)
        self.fill_expr(right)

        op = expr.operator
        op_name = op.name

        if left.result.type == Type.STRING:
            if op not in (TokenType.EQUALS_TOKEN, TokenType.NOT_EQUALS_TOKEN):
                raise TypePropagationError(
                    f"You can't use the {op_name} operator on a string"
                )

        is_id = left.result.type_name == "id" or right.result.type_name == "id"
        if not is_id and left.result.type_name != right.result.type_name:
            raise TypePropagationError(
                f"The left and right operand of a binary expression ('{op_name}') must have the same type, but got {left.result.type_name} and {right.result.type_name}"
            )

        if op in (TokenType.EQUALS_TOKEN, TokenType.NOT_EQUALS_TOKEN):
            expr.result.type = Type.BOOL
            expr.result.type_name = "bool"
        elif op in (
            TokenType.GREATER_OR_EQUAL_TOKEN,
            TokenType.GREATER_TOKEN,
            TokenType.LESS_OR_EQUAL_TOKEN,
            TokenType.LESS_TOKEN,
        ):
            if left.result.type != Type.NUMBER:
                raise TypePropagationError(f"'{op_name}' operator expects number")
            expr.result.type = Type.BOOL
            expr.result.type_name = "bool"
        elif op in (TokenType.AND_TOKEN, TokenType.OR_TOKEN):
            if left.result.type != Type.BOOL:
                raise TypePropagationError(f"'{op_name}' operator expects bool")
            expr.result.type = Type.BOOL
            expr.result.type_name = "bool"
        elif op in (
            TokenType.PLUS_TOKEN,
            TokenType.MINUS_TOKEN,
            TokenType.MULTIPLICATION_TOKEN,
            TokenType.DIVISION_TOKEN,
        ):
            if left.result.type != Type.NUMBER:
                raise TypePropagationError(f"'{op_name}' operator expects number")
            expr.result.type = left.result.type
            expr.result.type_name = left.result.type_name

    def fill_expr(self, expr: Expr):
        if isinstance(expr, IdentifierExpr):
            var = self.get_variable(expr.name)
            if not var:
                raise TypePropagationError(f"The variable '{expr.name}' does not exist")
            expr.result.type = var.type
            expr.result.type_name = var.type_name
        elif isinstance(expr, UnaryExpr):
            op = expr.operator
            inner = expr.expr

            # Check for double unary
            if isinstance(inner, UnaryExpr) and inner.operator == op:
                raise TypePropagationError(
                    f"Found '{op.name}' directly next to another '{op.name}', which can be simplified by just removing both of them"
                )

            self.fill_expr(inner)
            expr.result.type = inner.result.type
            expr.result.type_name = inner.result.type_name

            if op == TokenType.NOT_TOKEN:
                if expr.result.type != Type.BOOL:
                    raise TypePropagationError(
                        f"Found 'not' before {expr.result.type_name}, but it can only be put before a bool"
                    )
            elif op == TokenType.MINUS_TOKEN:
                if expr.result.type != Type.NUMBER:
                    raise TypePropagationError(
                        f"Found '-' before {expr.result.type_name}, but it can only be put before a number"
                    )
        elif isinstance(expr, (BinaryExpr, LogicalExpr)):
            self.fill_binary_expr(expr)
        elif isinstance(expr, CallExpr):
            self.fill_call_expr(expr)
        elif isinstance(expr, ParenthesizedExpr):
            self.fill_expr(expr.expr)
            expr.result.type = expr.expr.result.type
            expr.result.type_name = expr.expr.result.type_name

    def fill_variable_statement(self, stmt: VariableStatement):
        # This call has to happen before the `add_local_variable()` we do below,
        # since `a: number = a` doesn't throw otherwise.
        self.fill_expr(stmt.expr)

        var = self.get_variable(stmt.name)

        if stmt.type:
            assert stmt.type_name

            if var:
                raise TypePropagationError(f"The variable '{stmt.name}' already exists")

            if not (stmt.type_name == "id" and stmt.expr.result.type ==
                    Type.ID) and stmt.type_name != stmt.expr.result.type_name:
                raise TypePropagationError(
                    f"Can't assign {stmt.expr.result.type_name} to '{stmt.name}', which has type {stmt.type_name}"
                )

            self.add_local_variable(stmt.name, stmt.type, stmt.type_name)
        else:
            if not var:
                raise TypePropagationError(
                    f"Can't assign to the variable '{stmt.name}', since it does not exist"
                )

            if stmt.name in self.global_variables and var.type == Type.ID:
                raise TypePropagationError("Global id variables can't be reassigned")

            if not (var.type_name == "id" and stmt.expr.result.type ==
                    Type.ID) and var.type_name != stmt.expr.result.type_name:
                raise TypePropagationError(
                    f"Can't assign {stmt.expr.result.type_name} to '{var.name}', which has type {var.type_name}"
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
                self.fill_call_expr(stmt.expr)
            elif isinstance(stmt, IfStatement):
                self.fill_expr(stmt.condition)
                self.fill_statements(stmt.if_body)
                if stmt.else_body:
                    self.fill_statements(stmt.else_body)
            elif isinstance(stmt, ReturnStatement):
                if stmt.value:
                    self.fill_expr(stmt.value)

                    if not self.fn_return_type:
                        raise TypePropagationError(
                            f"Function '{self.filled_fn_name}' wasn't supposed to return any value"
                        )

                    if not (self.fn_return_type_name == "id" and stmt.value.result.type ==
                        Type.ID) and self.fn_return_type_name != stmt.value.result.type_name:
                        raise TypePropagationError(
                            f"Function '{self.filled_fn_name}' is supposed to return {self.fn_return_type_name}, not {stmt.value.result.type_name}"
                        )
                else:
                    if self.fn_return_type:
                        raise TypePropagationError(
                            f"Function '{self.filled_fn_name}' is supposed to return a value of type {self.fn_return_type_name}"
                        )
            elif isinstance(stmt, WhileStatement):
                self.fill_expr(stmt.condition)
                self.fill_statements(stmt.body_statements)

        self.remove_local_variables_in_statements(statements)

    def add_argument_variables(self, arguments: List[Argument]):
        self.local_variables = {}

        for arg in arguments:
            self.add_local_variable(arg.name, arg.type, arg.type_name)

    def fill_helper_fns(self):
        for fn_name, fn in self.helper_fns.items():
            self.fn_return_type = fn.return_type
            self.fn_return_type_name = fn.return_type_name
            self.filled_fn_name = fn_name

            self.add_argument_variables(fn.arguments)

            self.fill_statements(fn.body_statements)

            if fn.return_type:
                if not fn.body_statements:
                    raise TypePropagationError(
                        f"Function '{self.filled_fn_name}' is supposed to return {self.fn_return_type_name} as its last line"
                    )

                if not isinstance(fn.body_statements[-1], ReturnStatement):
                    raise TypePropagationError(
                        f"Function '{self.filled_fn_name}' is supposed to return {self.fn_return_type_name} as its last line"
                    )

    def fill_on_fns(self):
        # Check for on_fns that aren't declared in the entity
        for fn_name in self.on_fns.keys():
            if fn_name not in self.entity_on_functions:
                raise TypePropagationError(
                    f"The function '{fn_name}' was not declared by entity '{self.file_entity_type}' in mod_api.json"
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
                raise TypePropagationError(
                    f"The function '{expected_fn_name}' needs to be moved before/after a different on_ function, according to the entity '{self.file_entity_type}' in mod_api.json"
                )
            previous_on_fn_index = current_parser_index

            self.fn_return_type = None
            self.fn_return_type_name = None
            self.filled_fn_name = expected_fn_name

            params = self.entity_on_functions[expected_fn_name].get("arguments", [])

            if len(fn.arguments) != len(params):
                if len(fn.arguments) < len(params):
                    raise TypePropagationError(
                        f"Function '{expected_fn_name}' expected the parameter '{params[len(fn.arguments)]['name']}' with type {params[len(fn.arguments)]['type']}"
                    )
                else:
                    raise TypePropagationError(
                        f"Function '{expected_fn_name}' got an unexpected extra parameter '{fn.arguments[len(params)].name}' with type {fn.arguments[len(params)].type_name}"
                    )

            for arg, param in zip(fn.arguments, params):
                if arg.name != param["name"]:
                    raise TypePropagationError(
                        f"Function '{expected_fn_name}' its '{arg.name}' parameter was supposed to be named '{param['name']}'"
                    )

                if self.is_wrong_type(
                    arg.type,
                    Parser.parse_type(param["type"]),
                    arg.type_name,
                    param["type"],
                ):
                    raise TypePropagationError(
                        f"Function '{expected_fn_name}' its '{param['name']}' parameter was supposed to have the type {param['type']}, but got {arg.type_name}"
                    )

            self.add_argument_variables(fn.arguments)
            self.fill_statements(fn.body_statements)

    def check_global_expr(self, expr: Expr, name: str):
        """Check that global variables don't call helper fns"""
        if isinstance(expr, UnaryExpr):
            self.check_global_expr(expr.expr, name)
        elif isinstance(expr, (BinaryExpr, LogicalExpr)):
            self.check_global_expr(expr.left_expr, name)
            self.check_global_expr(expr.right_expr, name)
        elif isinstance(expr, CallExpr):
            if expr.fn_name.startswith("helper_"):
                raise TypePropagationError(
                    f"The global variable '{name}' isn't allowed to call helper functions"
                )
            for arg in expr.arguments:
                self.check_global_expr(arg, name)
        elif isinstance(expr, ParenthesizedExpr):
            self.check_global_expr(expr.expr, name)

    def fill_global_variables(self):
        # Add the implicit 'me' variable
        self.add_global_variable("me", Type.ID, self.file_entity_type)

        # Process global variable statements
        for stmt in self.ast:
            if isinstance(stmt, VariableStatement):
                # Global variables are guaranteed to be initialized
                assert stmt.type
                assert stmt.type_name
                assert stmt.expr

                self.check_global_expr(stmt.expr, stmt.name)
                self.fill_expr(stmt.expr)

                # Check for assignment to 'me'
                if isinstance(stmt.expr, IdentifierExpr):
                    if stmt.expr.name == "me":
                        raise TypePropagationError(
                            "Global variables can't be assigned 'me'"
                        )

                if not (stmt.type_name == "id" and stmt.expr.result.type ==
                    Type.ID) and stmt.type_name != stmt.expr.result.type_name:
                    raise TypePropagationError(
                        f"Can't assign {stmt.expr.result.type_name} to '{stmt.name}', which has type {stmt.type_name}"
                    )

                self.add_global_variable(stmt.name, stmt.type, stmt.type_name)

    def fill(self):
        """Main entry point for type propagation"""
        self.fill_global_variables()
        self.fill_on_fns()
        self.fill_helper_fns()
