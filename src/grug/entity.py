from typing import Dict, List, Optional

from grug.grug_file import GrugFile
from grug.grug_value import GrugValue

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


class Break(Exception):
    pass


class Continue(Exception):
    pass


class Return(Exception):
    pass


class Entity:
    def __init__(self, file: GrugFile):
        self.me_id = file.state.next_id
        file.state.next_id += 1

        self.file = file

        self.game_fns = file.game_fns

        self.global_variables: Dict[str, GrugValue] = {}
        self.global_variables["me"] = self.me_id
        for g in file.global_variables:
            self.global_variables[g.name] = self._run_expr(g.expr)

        # Stack of scopes, necessary when an on_ fn calls a helper_ fn.
        self.local_variable_scopes: List[Dict[str, GrugValue]] = []

        # Points to the current on/helper fn's scope in self.local_variable_scopes.
        self.local_variables: Dict[str, GrugValue] = {}

    def __getattr__(self, name: str):
        """
        This function lets `dog.spawn(42)` call `dog.run_on_fn("spawn", 42)`.
        """

        def runner(*args: GrugValue) -> Optional[GrugValue]:
            return self.run_on_fn(name, *args)

        return runner

    def run_on_fn(self, on_fn_name: str, *args: GrugValue):
        on_fn = self.file.on_fns.get(on_fn_name)
        if not on_fn:
            raise RuntimeError(
                f"The function '{on_fn_name}' is not defined by the file {self.file.relative_path}"
            )

        self.local_variables = {}
        self.local_variable_scopes.append(self.local_variables)

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
            return expr.string
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
        except Break:
            pass

    def _run_break_statement(self):
        raise Break()

    def _run_continue_statement(self):
        raise Continue()

    def _run_helper_fn(self, name: str, *args: GrugValue) -> Optional[GrugValue]:
        helper_fn = self.file.helper_fns.get(name)
        if not helper_fn:
            raise KeyError(f"Unknown helper function '{name}'")

        self.local_variables = {}
        self.local_variable_scopes.append(self.local_variables)

        for arg, argument in zip(args, helper_fn.arguments):
            self.local_variables[argument.name] = arg

        result = self._run_statements(helper_fn.body_statements)

        self.local_variable_scopes.pop()

        return result

    def _run_game_fn(self, name: str, *args: GrugValue) -> Optional[GrugValue]:
        game_fn = self.game_fns.get(name)
        if not game_fn:
            raise KeyError(f"Unknown game function '{name}'")
        return game_fn(*args)
