import ctypes
from typing import Any, Callable, Dict, List, Optional, Union

from .frontend import (
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


GameFn = Callable[[ctypes.Array[GrugValue]], GrugValue]


class Backend:
    def __init__(self, mod_api: ModApi):
        self.mod_api = mod_api
        self.game_fns: Dict[str, Dict[str, Any]] = {}

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
        on_fn: OnFn,
    ):
        self._run_statements(on_fn.body_statements)

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
        assert False  # TODO: Implement

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
            # TODO: Use `expr.name` to look up local and global vars
            return ctypes.c_uint64(42)
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
            assert value  # Functions that return nothing are not callable in exprs
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
        if call_expr.fn_name.startswith("helper_"):
            assert False  # TODO: Implement!
        else:
            return self._call_game_fn(call_expr.fn_name, call_expr.arguments)

    def _run_if_statement(self, statement: IfStatement):
        assert False  # TODO: Implement

    def _run_return_statement(self, statement: ReturnStatement):
        assert False  # TODO: Implement

    def _run_while_statement(self, statement: WhileStatement):
        assert False  # TODO: Implement

    def _run_break_statement(self):
        assert False  # TODO: Implement

    def _run_continue_statement(self):
        assert False  # TODO: Implement

    def _call_game_fn(self, name: str, args: List[Expr]) -> Optional[GrugValueType]:
        if name not in self.game_fns:
            raise KeyError(f"Unknown game function '{name}'")

        info = self.game_fns[name]
        fn: GameFn = info["fn"]

        # The fn args will be turned from a Python list into a ctypes array
        c_args = (GrugValue * len(args))()

        # TODO: Can this be removed?
        # Keeps strings alive
        string_refs: List[Any] = []

        for i, v in enumerate([self._run_expr(expr) for expr in args]):
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

        result = fn(c_args)

        return_type = info["return_type"]
        if return_type == "number":
            return result._number
        if return_type == "bool":
            return result._bool
        if return_type == "string":
            return result._string
        if return_type == "id":
            return result._id

        assert return_type == None
