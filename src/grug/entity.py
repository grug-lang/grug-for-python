import time
from typing import Dict, List, Optional

from grug.grug_file import GrugFile
from grug.grug_state import GrugRuntimeErrorType
from grug.grug_value import GrugValue

from .parser import (
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
    NumberExpr,
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

MAX_DEPTH = 100


class Break(Exception):
    pass


class Continue(Exception):
    pass


class Return(Exception):
    def __init__(self, value: Optional[GrugValue] = None):
        self.value = value


class StackOverflow(Exception):
    pass


class TimeLimitExceeded(Exception):
    pass


class GameFnError(Exception):
    def __init__(self, reason: str):
        self.reason = reason


class ReraisedGameFnError(Exception):
    pass


class Entity:
    def __init__(self, file: GrugFile):
        self.me_id = file.state.next_id
        file.state.next_id += 1

        self.file = file
        self.state = file.state

        self.game_fns = file.game_fns

        self.game_fn_return_types = file.game_fn_return_types

        self.on_fn_time_limit_sec = file.state.on_fn_time_limit_ms / 1000

        self.start_time: float

        self.local_variables: Dict[str, GrugValue] = {}

        self.on_fn_depth: int = 0

        self._init_globals(file.global_variables)

    def _init_globals(self, global_variables: List[VariableStatement]):
        self.fn_name = "init_globals"

        self.global_variables: Dict[str, GrugValue] = {}
        self.global_variables["me"] = self.me_id

        old_fn_depth = self.state.fn_depth
        self.state.fn_depth += 1

        self.start_time = time.time()

        # TODO: Add a test to grug-tests for this, containing two .grug files,
        #       where file 1 spawns file 2, and file 2 has a game fn error.
        #
        # TODO: Add examples/game_fn_error.py, to show off a Python game fn raising grug.GameFnError
        try:
            for g in global_variables:
                self.global_variables[g.name] = self._run_expr(g.expr)
        except (StackOverflow, TimeLimitExceeded, ReraisedGameFnError):
            if self.state.fn_depth > 1:
                raise  # Propagate exception
        finally:
            self.state.fn_depth = old_fn_depth

    def __getattr__(self, name: str):
        """
        This function lets `dog.spawn(42)` call `dog._run_on_fn("spawn", 42)`.
        """

        def runner(*args: GrugValue) -> Optional[GrugValue]:
            return self._run_on_fn(name, *args)

        return runner

    def _run_on_fn(self, on_fn_name: str, *args: GrugValue):
        on_fn = self.file.on_fns.get(on_fn_name)
        if not on_fn:
            raise RuntimeError(
                f"The function '{on_fn_name}' is not defined by the file {self.file.relative_path}"
            )

        # TODO: Add an ok/ test that verifies that the local vars of a single entity its on_a()
        #       isn't overwritten when it calls on_b().
        parent_local_variables = self.local_variables
        self.local_variables = {}

        self.fn_name = on_fn_name

        # Assign and verify argument types
        for arg, argument in zip(args, on_fn.arguments):
            assert isinstance(
                arg, self._get_expected_py_type(argument.type_name)
            ), f"Argument '{argument.name}' of {on_fn_name}() must be {argument.type_name}, got {type(arg).__name__}"

            self.local_variables[argument.name] = arg

        old_fn_depth = self.state.fn_depth
        self.state.fn_depth += 1

        # TODO: Add an ok/ test that asserts that start_time isn't shared by all on fns of a single entity, since on_a()->on_b()->etc. shouldn't keep resetting the start time.
        #
        # Prevents on_a() its start_time being reset when it indirectly calls its on_b().
        old_on_fn_depth = self.on_fn_depth
        self.on_fn_depth += 1
        if self.on_fn_depth == 1:
            self.start_time = time.time()

        try:
            self._run_statements(on_fn.body_statements)
        except Return:
            pass
        except (StackOverflow, TimeLimitExceeded, ReraisedGameFnError):
            if self.state.fn_depth > 1:
                raise  # Propagate exception
        finally:
            self.state.fn_depth = old_fn_depth
            self.on_fn_depth = old_on_fn_depth
            self.local_variables = parent_local_variables

    def _get_expected_py_type(self, expected_arg_type_name: str):
        if expected_arg_type_name == "number":
            return float
        elif expected_arg_type_name == "bool":
            return bool
        elif expected_arg_type_name in ("string", "resource", "entity"):
            return str
        return object

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
        value = self._run_expr(statement.expr)
        if statement.name in self.global_variables:
            self.global_variables[statement.name] = value
        else:
            self.local_variables[statement.name] = value

    def _run_call_statement(self, statement: CallStatement):
        self._run_call_expr(statement.expr)

    def _run_expr(self, expr: Expr) -> GrugValue:
        if isinstance(expr, TrueExpr):
            return True
        elif isinstance(expr, FalseExpr):
            return False
        elif isinstance(expr, StringExpr):
            return expr.string
        elif isinstance(expr, ResourceExpr):
            return f"{self.file.mod}/{expr.string}"
        elif isinstance(expr, EntityExpr):
            return (
                expr.string if ":" in expr.string else f"{self.file.mod}:{expr.string}"
            )
        elif isinstance(expr, IdentifierExpr):
            if expr.name in self.global_variables:
                return self.global_variables[expr.name]
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
            return left == right
        elif op == TokenType.NOT_EQUALS_TOKEN:
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
        else:
            assert op == TokenType.LESS_TOKEN
            assert isinstance(left, float) and isinstance(right, float)
            return left < right

    def _run_logical_expr(self, logical_expr: LogicalExpr):
        if logical_expr.operator == TokenType.AND_TOKEN:
            return self._run_expr(logical_expr.left_expr) and self._run_expr(
                logical_expr.right_expr
            )
        else:
            assert logical_expr.operator == TokenType.OR_TOKEN

            return self._run_expr(logical_expr.left_expr) or self._run_expr(
                logical_expr.right_expr
            )

    def _run_call_expr(self, call_expr: CallExpr):
        args = [self._run_expr(arg) for arg in call_expr.arguments]

        if call_expr.fn_name.startswith("helper_"):
            return self._run_helper_fn(call_expr.fn_name, *args)
        else:
            return self._run_game_fn(call_expr.fn_name, *args)

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
                self._check_time_limit_exceeded()
        except Break:
            pass

    def _check_time_limit_exceeded(self):
        if time.time() - self.start_time > self.on_fn_time_limit_sec:
            self.state.runtime_error_handler(
                f"Took longer than {self.on_fn_time_limit_sec * 1000:g} milliseconds to run",
                GrugRuntimeErrorType.TIME_LIMIT_EXCEEDED,
                self.fn_name,
                self.file.relative_path,
            )
            raise TimeLimitExceeded()

    def _run_break_statement(self):
        raise Break()

    def _run_continue_statement(self):
        raise Continue()

    def _run_helper_fn(self, name: str, *args: GrugValue) -> Optional[GrugValue]:
        helper_fn = self.file.helper_fns.get(name)
        if not helper_fn:
            raise KeyError(f"Unknown helper function '{name}'")

        parent_local_variables = self.local_variables
        self.local_variables = {}

        for arg, argument in zip(args, helper_fn.arguments):
            self.local_variables[argument.name] = arg

        old_fn_depth = self.state.fn_depth
        self.state.fn_depth += 1
        if self.state.fn_depth > MAX_DEPTH:
            self.state.runtime_error_handler(
                "Stack overflow, so check for accidental infinite recursion",
                GrugRuntimeErrorType.STACK_OVERFLOW,
                self.fn_name,
                self.file.relative_path,
            )
            raise StackOverflow()

        self._check_time_limit_exceeded()

        result: Optional[GrugValue] = None
        try:
            self._run_statements(helper_fn.body_statements)
        except Return as e:
            result = e.value

        self.state.fn_depth = old_fn_depth

        self.local_variables = parent_local_variables

        return result

    def _run_game_fn(self, name: str, *args: GrugValue) -> Optional[GrugValue]:
        game_fn = self.game_fns.get(name)
        if not game_fn:
            raise KeyError(f"Unknown game function '{name}'")

        try:
            result = game_fn(*args)
        except GameFnError as e:
            self.state.runtime_error_handler(
                e.reason,
                GrugRuntimeErrorType.GAME_FN_ERROR,
                self.fn_name,
                self.file.relative_path,
            )
            raise ReraisedGameFnError()

        t = self.game_fn_return_types[name]
        if t is None:
            return

        expected_type = self._get_expected_py_type(t)

        assert isinstance(
            result, expected_type
        ), f"Return value of game function {name}() must be {expected_type.__name__}, got {type(result).__name__}"

        return result
