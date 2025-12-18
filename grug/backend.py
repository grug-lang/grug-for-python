import ctypes
from typing import Any, Callable, Dict, List, Optional, Union

from .frontend import (
    Ast,
    BinaryExpr,
    BreakStatement,
    CallExpr,
    CallStatement,
    CommentStatement,
    ContinueStatement,
    EmptyLineStatement,
    EntityExpr,
    Expr,
    FalseExpr,
    HelperFn,
    IdentifierExpr,
    IfStatement,
    LogicalExpr,
    ModApi,
    NumberExpr,
    OnFn,
    ParenthesizedExpr,
    ResourceExpr,
    ReturnStatement,
    Statement,
    StringExpr,
    TokenType,
    TrueExpr,
    UnaryExpr,
    VariableStatement,
    WhileStatement,
)

GrugValueType = Union[float, bool, str, ctypes.c_uint64]


class GrugValue(ctypes.Union):
    _fields_ = [
        ("_number", ctypes.c_double),
        ("_bool", ctypes.c_bool),
        ("_string", ctypes.c_char_p),
        ("_id", ctypes.c_uint64),
    ]


class Break(Exception):
    pass


class Continue(Exception):
    pass


class Return(Exception):
    pass


GameFn = Callable[[ctypes.Array[GrugValue]], GrugValue]


class Backend:
    def __init__(self, mod_api: ModApi):
        self.mod_api = mod_api

        self.game_fns: Dict[str, Dict[str, Any]] = {}

        # Every on_ and helper_ function gets its own local variables.
        self.local_variables: Dict[str, GrugValueType] = {}

        # Stack of scopes, necessary when an on_ fn calls a helper_ fn.
        self.local_variable_scopes: List[Dict[str, GrugValueType]] = []

    def register_game_fn(self, name: str, fn: GameFn):
        self.game_fns[name] = {
            "fn": fn,
            "return_type": self.mod_api["game_functions"][name].get("return_type"),
            "arg_types": [
                arg["type"]
                for arg in self.mod_api["game_functions"][name].get("arguments", [])
            ],
        }

    def init_globals_fn_dispatcher(self, path: str):
        pass

    def run_on_fn(
        self,
        on_fn_name: str,  # TODO: Use in runtime error messages
        grug_file_path: str,  # TODO: Use in runtime error messages
        args: List[GrugValueType],  # TODO: Turn these into local variables
        ast: Ast,
    ):
        self.local_variables = {}
        self.local_variable_scopes.append(self.local_variables)

        on_fns: Dict[str, OnFn] = {s.fn_name: s for s in ast if isinstance(s, OnFn)}

        on_fn = on_fns.get(on_fn_name)
        if not on_fn:
            raise RuntimeError(
                f"The function '{on_fn_name}' is not defined by the file {grug_file_path}"
            )

        self.helper_fns = {s.fn_name: s for s in ast if isinstance(s, HelperFn)}

        for arg, argument in zip(args, on_fn.arguments):
            self.local_variables[argument.name] = arg

        self._run_statements(on_fn.body_statements)

        self.local_variable_scopes.pop()
        assert len(self.local_variable_scopes) == 0

    def _run_statements(self, statements: List[Statement]):
        for statement in statements:
            self._run_statement(statement)

    def _run_statement(self, statement: Statement):
        if isinstance(statement, VariableStatement):
            self._run_variable_statement(statement)
        elif isinstance(statement, CallStatement):
            self._run_call_statement(statement)
        elif isinstance(statement, IfStatement):
            self._run_if_statement(statement)
        elif isinstance(statement, ReturnStatement):
            self._run_return_statement(statement)
        elif isinstance(statement, WhileStatement):
            self._run_while_statement(statement)
        elif isinstance(statement, BreakStatement):
            self._run_break_statement()
        elif isinstance(statement, ContinueStatement):
            self._run_continue_statement()
        else:
            assert isinstance(statement, (EmptyLineStatement, CommentStatement))

    def _run_variable_statement(self, statement: VariableStatement):
        self.local_variables[statement.name] = self._run_expr(statement.assignment_expr)

    def _run_call_statement(self, statement: CallStatement):
        return self._run_call_expr(statement.expr)

    def _run_expr(self, expr: Expr) -> GrugValueType:
        if isinstance(expr, TrueExpr):
            return True
        elif isinstance(expr, FalseExpr):
            return False
        elif isinstance(expr, StringExpr):
            return expr.string
        elif isinstance(expr, ResourceExpr):
            return expr.string
        elif isinstance(expr, EntityExpr):
            return expr.string
        elif isinstance(expr, IdentifierExpr):
            return self.local_variables[expr.name]
        elif isinstance(expr, NumberExpr):
            return expr.value
        elif isinstance(expr, UnaryExpr):
            return self._run_unary_expr(expr)
        elif isinstance(expr, BinaryExpr):
            return self._run_binary_expr(expr)
        elif isinstance(expr, LogicalExpr):
            return self._run_logical_expr(expr)
        elif isinstance(expr, CallExpr):
            value = self._run_call_expr(expr)

            # Functions that return nothing are not callable in exprs
            assert value is not None

            return value
        else:
            assert isinstance(expr, ParenthesizedExpr)
            return self._run_expr(expr.expr)

    def _run_unary_expr(self, unary_expr: UnaryExpr):
        op = unary_expr.operator

        if op == TokenType.MINUS_TOKEN:
            number = self._run_expr(unary_expr.expr)
            assert isinstance(number, float)
            return -number
        else:
            assert op == TokenType.NOT_TOKEN
            return not self._run_expr(unary_expr.expr)

    def _run_binary_expr(self, binary_expr: BinaryExpr):
        left = self._run_expr(binary_expr.left_expr)
        right = self._run_expr(binary_expr.right_expr)

        op = binary_expr.operator

        if op == TokenType.PLUS_TOKEN:
            assert isinstance(left, float) and isinstance(right, float)
            return left + right
        elif op == TokenType.MINUS_TOKEN:
            assert isinstance(left, float) and isinstance(right, float)
            return left - right
        elif op == TokenType.MULTIPLICATION_TOKEN:
            assert isinstance(left, float) and isinstance(right, float)
            return left * right
        elif op == TokenType.DIVISION_TOKEN:
            assert isinstance(left, float) and isinstance(right, float)
            return left / right
        elif op == TokenType.EQUALS_TOKEN:
            assert isinstance(left, (float, str)) and isinstance(right, (float, str))
            return left == right
        elif op == TokenType.NOT_EQUALS_TOKEN:
            assert isinstance(left, (float, str)) and isinstance(right, (float, str))
            return left != right
        elif op == TokenType.GREATER_OR_EQUAL_TOKEN:
            assert isinstance(left, float) and isinstance(right, float)
            return left >= right
        elif op == TokenType.GREATER_TOKEN:
            assert isinstance(left, float) and isinstance(right, float)
            return left > right
        elif op == TokenType.LESS_OR_EQUAL_TOKEN:
            assert isinstance(left, float) and isinstance(right, float)
            return left <= right
        elif op == TokenType.LESS_TOKEN:
            assert isinstance(left, float) and isinstance(right, float)
            return left < right
        else:
            assert False  # Unreachable

    def _run_logical_expr(self, logical_expr: LogicalExpr):
        op = logical_expr.operator

        if op == TokenType.AND_TOKEN:
            return self._run_expr(logical_expr.left_expr) and self._run_expr(
                logical_expr.right_expr
            )
        else:
            assert op == TokenType.OR_TOKEN

            return self._run_expr(logical_expr.left_expr) or self._run_expr(
                logical_expr.right_expr
            )

    def _run_call_expr(self, call_expr: CallExpr):
        args = [self._run_expr(arg) for arg in call_expr.arguments]

        if call_expr.fn_name.startswith("helper_"):
            return self._call_helper_fn(call_expr.fn_name, args)
        else:
            return self._call_game_fn(call_expr.fn_name, args)

    def _run_if_statement(self, statement: IfStatement):
        if self._run_expr(statement.condition):
            self._run_statements(statement.if_body)
        else:
            self._run_statements(statement.else_body)

    def _run_return_statement(self, statement: ReturnStatement):
        if statement.value:
            raise Return(self._run_expr(statement.value))
        raise Return()

    def _run_while_statement(self, statement: WhileStatement):
        try:
            while self._run_expr(statement.condition):
                try:
                    self._run_statements(statement.body_statements)
                except Continue:
                    pass
        except Break:
            pass

    def _run_break_statement(self):
        raise Break()

    def _run_continue_statement(self):
        raise Continue()

    def _call_helper_fn(
        self, name: str, args: List[GrugValueType]
    ) -> Optional[GrugValueType]:
        helper_fn = self.helper_fns.get(name)
        if not helper_fn:
            raise KeyError(f"Unknown helper function '{name}'")

        for arg, argument in zip(args, helper_fn.arguments):
            self.local_variables[argument.name] = arg

        return self._run_statements(helper_fn.body_statements)

    def _call_game_fn(
        self, name: str, args: List[GrugValueType]
    ) -> Optional[GrugValueType]:
        game_fn = self.game_fns.get(name)
        if not game_fn:
            raise KeyError(f"Unknown game function '{name}'")

        fn_ptr: GameFn = game_fn["fn"]

        # The fn args will be turned from a Python list into a ctypes array
        c_args = (GrugValue * len(args))()

        # TODO: Can this be removed?
        # Keeps strings alive
        string_refs: List[Any] = []

        for i, v in enumerate(args):
            if isinstance(v, float):
                c_args[i]._number = v
            elif isinstance(v, bool):
                c_args[i]._bool = v
            elif isinstance(v, str):
                s = ctypes.c_char_p(v.encode())
                string_refs.append(s)
                c_args[i]._string = s
            else:
                assert isinstance(v, ctypes.c_uint64)
                c_args[i]._id = v

        # Python receives a GrugValueWorkaround struct (correctly handled via register OR memory).
        result = fn_ptr(c_args)

        return_type = game_fn["return_type"]

        if return_type == None:
            return

        # Create a GrugValue and copy the bits from GrugValueWorkaround into it.
        value = GrugValue()
        ctypes.memmove(ctypes.byref(value), ctypes.byref(result), ctypes.sizeof(value))

        if return_type == "number":
            return value._number
        if return_type == "bool":
            return value._bool
        if return_type == "string":
            return value._string

        assert return_type == "id"
        return value._id
