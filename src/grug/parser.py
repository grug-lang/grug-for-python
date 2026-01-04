from __future__ import annotations

import math
import struct
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Union

from .tokenizer import SPACES_PER_INDENT, Token, TokenType

MAX_PARSING_DEPTH = 100

MIN_F64 = struct.unpack("!d", struct.pack("!Q", 0x0010000000000000))[0]
MAX_F64 = struct.unpack("!d", struct.pack("!Q", 0x7FEFFFFFFFFFFFFF))[0]


class ParserError(Exception):
    pass


class Type(Enum):
    BOOL = auto()
    NUMBER = auto()
    STRING = auto()
    ID = auto()
    RESOURCE = auto()
    ENTITY = auto()


@dataclass
class Result:
    type: Optional[Type] = None
    type_name: Optional[str] = None


@dataclass
class TrueExpr:
    result: Result = field(default_factory=lambda: Result(Type.BOOL, "bool"))


@dataclass
class FalseExpr:
    result: Result = field(default_factory=lambda: Result(Type.BOOL, "bool"))


@dataclass
class StringExpr:
    string: str
    result: Result = field(default_factory=lambda: Result(Type.STRING, "string"))


@dataclass
class ResourceExpr:
    string: str
    result: Result = field(default_factory=lambda: Result(Type.RESOURCE, "resource"))


@dataclass
class EntityExpr:
    string: str
    result: Result = field(default_factory=lambda: Result(Type.ENTITY, "entity"))


@dataclass
class IdentifierExpr:
    name: str
    result: Result = field(default_factory=Result)


@dataclass
class NumberExpr:
    value: float
    string: str
    result: Result = field(default_factory=lambda: Result(Type.NUMBER, "number"))


@dataclass
class UnaryExpr:
    operator: TokenType
    expr: Expr
    result: Result = field(default_factory=Result)


@dataclass
class BinaryExpr:
    left_expr: Expr
    operator: TokenType
    right_expr: Expr
    result: Result = field(default_factory=Result)


@dataclass
class LogicalExpr:
    left_expr: Expr
    operator: TokenType
    right_expr: Expr
    result: Result = field(default_factory=Result)


@dataclass
class CallExpr:
    fn_name: str
    arguments: List[Expr] = field(default_factory=lambda: [])
    result: Result = field(default_factory=Result)


@dataclass
class ParenthesizedExpr:
    expr: Expr
    result: Result = field(default_factory=Result)


Expr = Union[
    TrueExpr,
    FalseExpr,
    StringExpr,
    ResourceExpr,
    EntityExpr,
    IdentifierExpr,
    NumberExpr,
    UnaryExpr,
    BinaryExpr,
    LogicalExpr,
    CallExpr,
    ParenthesizedExpr,
]


@dataclass
class VariableStatement:
    name: str
    type: Optional[Type]
    type_name: Optional[str]
    expr: Expr


@dataclass
class CallStatement:
    expr: CallExpr


@dataclass
class IfStatement:
    condition: Expr
    if_body: List[Statement]
    else_body: List[Statement]


@dataclass
class ReturnStatement:
    value: Optional[Expr] = None


@dataclass
class WhileStatement:
    condition: Expr
    body_statements: List[Statement]


@dataclass
class BreakStatement:
    pass


@dataclass
class ContinueStatement:
    pass


@dataclass
class EmptyLineStatement:
    pass


@dataclass
class CommentStatement:
    string: str


Statement = Union[
    VariableStatement,
    CallStatement,
    IfStatement,
    ReturnStatement,
    WhileStatement,
    BreakStatement,
    ContinueStatement,
    EmptyLineStatement,
    CommentStatement,
]


@dataclass
class Argument:
    name: str
    type: Type
    type_name: str
    resource_extension: Optional[str] = None
    entity_type: Optional[str] = None


@dataclass
class OnFn:
    fn_name: str
    arguments: List[Argument] = field(default_factory=lambda: [])
    body_statements: List[Statement] = field(default_factory=lambda: [])


@dataclass
class HelperFn:
    fn_name: str
    arguments: List[Argument] = field(default_factory=lambda: [])
    return_type: Optional[Type] = None
    return_type_name: Optional[str] = None
    body_statements: List[Statement] = field(default_factory=lambda: [])


Ast = List[
    Union[VariableStatement, EmptyLineStatement, CommentStatement, OnFn, HelperFn]
]


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.ast: Ast = []
        self.helper_fns: Dict[str, HelperFn] = {}
        self.on_fns: Dict[str, OnFn] = {}
        self.statements = []
        self.arguments = []
        self.parsing_depth = 0
        self.loop_depth = 0
        self.indentation = 0
        self.called_helper_fn_names: Set[str] = set()

    def parse(self):
        seen_on_fn = False
        seen_newline = False
        newline_allowed = False
        newline_required = False
        just_seen_global = False

        i = [0]  # Use a list to allow modification by called functions
        while i[0] < len(self.tokens):
            token = self.tokens[i[0]]
            tname = token.type.name

            if (
                tname == "WORD_TOKEN"
                and i[0] + 1 < len(self.tokens)
                and self.tokens[i[0] + 1].type.name == "COLON_TOKEN"
            ):
                if seen_on_fn:
                    raise ParserError(
                        f"Move the global variable '{token.value}' so it is above the on_ functions"
                    )
                if newline_required and not just_seen_global:
                    raise ParserError(
                        f"Expected an empty line, on line {self.get_token_line_number(i[0])}"
                    )

                self.ast.append(self.parse_global_variable(i))

                self.consume_token_type(i, TokenType.NEWLINE_TOKEN)

                newline_allowed = True
                newline_required = True

                just_seen_global = True

                continue

            elif (
                tname == "WORD_TOKEN"
                and token.value.startswith("on_")
                and i[0] + 1 < len(self.tokens)
                and self.tokens[i[0] + 1].type.name == "OPEN_PARENTHESIS_TOKEN"
            ):
                if self.helper_fns:
                    raise ParserError(
                        f"{token.value}() must be defined before all helper_ functions"
                    )
                if newline_required:
                    raise ParserError(
                        f"Expected an empty line, on line {self.get_token_line_number(i[0])}"
                    )

                fn = self.parse_on_fn(i)
                if fn.fn_name in self.on_fns:
                    raise ParserError(
                        f"The function '{fn.fn_name}' was defined several times in the same file"
                    )
                self.on_fns[fn.fn_name] = fn

                self.consume_token_type(i, TokenType.NEWLINE_TOKEN)

                seen_on_fn = True

                newline_allowed = True
                newline_required = True

                just_seen_global = False

                continue

            elif (
                tname == "WORD_TOKEN"
                and token.value.startswith("helper_")
                and i[0] + 1 < len(self.tokens)
                and self.tokens[i[0] + 1].type.name == "OPEN_PARENTHESIS_TOKEN"
            ):
                if newline_required:
                    raise ParserError(
                        f"Expected an empty line, on line {self.get_token_line_number(i[0])}"
                    )

                fn = self.parse_helper_fn(i)
                if fn.fn_name in self.helper_fns:
                    raise ParserError(
                        f"The function '{fn.fn_name}' was defined several times in the same file"
                    )
                self.helper_fns[fn.fn_name] = fn

                self.consume_token_type(i, TokenType.NEWLINE_TOKEN)

                newline_allowed = True
                newline_required = True

                just_seen_global = False

                continue

            elif tname == "NEWLINE_TOKEN":
                if not newline_allowed:
                    raise ParserError(
                        f"Unexpected empty line, on line {self.get_token_line_number(i[0])}"
                    )

                seen_newline = True

                newline_allowed = False
                newline_required = False

                just_seen_global = False

                self.ast.append(EmptyLineStatement())
                i[0] += 1
                continue

            elif tname == "COMMENT_TOKEN":
                newline_allowed = True
                self.ast.append(CommentStatement(token.value))
                i[0] += 1
                self.consume_token_type(i, TokenType.NEWLINE_TOKEN)
                continue

            else:
                raise ParserError(
                    f"Unexpected token '{token.value}' on line {self.get_token_line_number(i[0])}"
                )

        if seen_newline and not newline_allowed:
            raise ParserError(
                f"Unexpected empty line, on line {self.get_token_line_number(len(self.tokens)-1)}"
            )

        return self.ast

    def peek_token(self, token_index: int):
        if token_index >= len(self.tokens):
            raise ParserError(
                f"token_index {token_index} was out of bounds in peek_token()"
            )
        return self.tokens[token_index]

    def consume_token(self, i: List[int]):
        token_index = i[0]
        token = self.peek_token(token_index)
        i[0] += 1
        return token

    def assert_token_type(self, token_index: int, expected_type: TokenType):
        token = self.peek_token(token_index)
        if token.type != expected_type:
            raise ParserError(
                f"Expected token type {expected_type.name}, "
                f"but got {token.type.name} on line {self.get_token_line_number(token_index)}"
            )

    def consume_token_type(self, i: List[int], expected_type: TokenType):
        self.assert_token_type(i[0], expected_type)
        i[0] += 1

    def get_token_line_number(self, token_index: int):
        if token_index >= len(self.tokens):
            raise ParserError(
                f"token_index {token_index} out of bounds in get_token_line_number()"
            )
        line_number = 1
        for idx in range(token_index):
            if self.tokens[idx].type == TokenType.NEWLINE_TOKEN:
                line_number += 1
        return line_number

    def parse_statement(self, i: List[int]):
        self.increase_parsing_depth()
        switch_token = self.peek_token(i[0])

        if switch_token.type == TokenType.WORD_TOKEN:
            token = self.peek_token(i[0] + 1)
            if token.type == TokenType.OPEN_PARENTHESIS_TOKEN:
                expr = self.parse_call(i)

                # The above `token.type == TokenType.OPEN_PARENTHESIS_TOKEN` guarantees that in `parse_call()`
                # the early Expr return in `if token.type != TokenType.OPEN_PARENTHESIS_TOKEN` is not reached.
                assert isinstance(expr, CallExpr)

                statement = CallStatement(expr)
            elif (
                token.type == TokenType.COLON_TOKEN
                or token.type == TokenType.SPACE_TOKEN
            ):
                statement = self.parse_local_variable(i)
            else:
                raise ParserError(
                    f"Expected '(', or ':', or ' =' after the word '{switch_token.value}' on line {self.get_token_line_number(i[0])}"
                )
        elif switch_token.type == TokenType.IF_TOKEN:
            i[0] += 1
            statement = self.parse_if_statement(i)
        elif switch_token.type == TokenType.RETURN_TOKEN:
            i[0] += 1
            token = self.peek_token(i[0])
            if token.type == TokenType.NEWLINE_TOKEN:
                statement = ReturnStatement()
            else:
                self.consume_space(i)
                expr = self.parse_expression(i)
                statement = ReturnStatement(expr)
        elif switch_token.type == TokenType.WHILE_TOKEN:
            i[0] += 1
            statement = self.parse_while_statement(i)
        elif switch_token.type == TokenType.BREAK_TOKEN:
            if self.loop_depth == 0:
                raise ParserError(
                    f"There is a break statement that isn't inside of a while loop"
                )
            i[0] += 1
            statement = BreakStatement()
        elif switch_token.type == TokenType.CONTINUE_TOKEN:
            if self.loop_depth == 0:
                raise ParserError(
                    f"There is a continue statement that isn't inside of a while loop"
                )
            i[0] += 1
            statement = ContinueStatement()
        elif switch_token.type == TokenType.NEWLINE_TOKEN:
            i[0] += 1
            statement = EmptyLineStatement()
        elif switch_token.type == TokenType.COMMENT_TOKEN:
            i[0] += 1
            statement = CommentStatement(switch_token.value)
        else:
            raise ParserError(
                f"Expected a statement token, but got token type {switch_token.type.name} on line {self.get_token_line_number(i[0])}"
            )

        self.decrease_parsing_depth()
        return statement

    @staticmethod
    def parse_type(type_str: str):
        if type_str == "bool":
            return Type.BOOL
        if type_str == "number":
            return Type.NUMBER
        if type_str == "string":
            return Type.STRING
        if type_str == "resource":
            return Type.RESOURCE
        if type_str == "entity":
            return Type.ENTITY
        return Type.ID

    def parse_arguments(self, i: List[int]):
        arguments: List[Argument] = []

        # First argument
        name_token = self.consume_token(i)
        arg_name = name_token.value

        self.consume_token_type(i, TokenType.COLON_TOKEN)

        self.consume_space(i)
        self.assert_token_type(i[0], TokenType.WORD_TOKEN)

        type_token = self.consume_token(i)
        type_name = type_token.value
        arg_type = Parser.parse_type(type_name)

        if arg_type == Type.RESOURCE:
            raise ParserError(
                f"The argument '{arg_name}' can't have 'resource' as its type"
            )
        if arg_type == Type.ENTITY:
            raise ParserError(
                f"The argument '{arg_name}' can't have 'entity' as its type"
            )

        arguments.append(Argument(arg_name, arg_type, type_name))

        # Every argument after the first one starts with a comma
        while True:
            token = self.peek_token(i[0])
            if token.type != TokenType.COMMA_TOKEN:
                break
            i[0] += 1

            self.consume_space(i)
            self.assert_token_type(i[0], TokenType.WORD_TOKEN)
            name_token = self.consume_token(i)
            arg_name = name_token.value

            self.consume_token_type(i, TokenType.COLON_TOKEN)

            self.consume_space(i)
            self.assert_token_type(i[0], TokenType.WORD_TOKEN)
            type_token = self.consume_token(i)
            type_name = type_token.value
            arg_type = Parser.parse_type(type_name)

            if arg_type == Type.RESOURCE:
                raise ParserError(
                    f"The argument '{arg_name}' can't have 'resource' as its type"
                )
            if arg_type == Type.ENTITY:
                raise ParserError(
                    f"The argument '{arg_name}' can't have 'entity' as its type"
                )

            arguments.append(Argument(arg_name, arg_type, type_name))

        return arguments

    def parse_helper_fn(self, i: List[int]):
        fn_name = self.consume_token(i)
        fn = HelperFn(fn_name.value)

        if fn.fn_name not in self.called_helper_fn_names:
            raise ParserError(
                f"{fn.fn_name}() is defined before the first time it gets called"
            )

        self.consume_token_type(i, TokenType.OPEN_PARENTHESIS_TOKEN)

        token = self.peek_token(i[0])
        if token.type == TokenType.WORD_TOKEN:
            fn.arguments = self.parse_arguments(i)

        self.consume_token_type(i, TokenType.CLOSE_PARENTHESIS_TOKEN)

        self.assert_token_type(i[0], TokenType.SPACE_TOKEN)
        token = self.peek_token(i[0] + 1)
        if token.type == TokenType.WORD_TOKEN:
            i[0] += 2
            fn.return_type = Parser.parse_type(token.value)
            fn.return_type_name = token.value

            if fn.return_type == Type.RESOURCE:
                raise ParserError(
                    f"The function '{fn.fn_name}' can't have 'resource' as its return type"
                )
            if fn.return_type == Type.ENTITY:
                raise ParserError(
                    f"The function '{fn.fn_name}' can't have 'entity' as its return type"
                )

        self.indentation = 0
        fn.body_statements = self.parse_statements(i)

        if all(
            isinstance(s, (EmptyLineStatement, CommentStatement))
            for s in fn.body_statements
        ):
            raise ParserError(f"{fn.fn_name}() can't be empty")

        self.ast.append(fn)
        return fn

    def parse_on_fn(self, i: List[int]):
        fn_token = self.consume_token(i)
        fn = OnFn(fn_token.value)

        self.consume_token_type(i, TokenType.OPEN_PARENTHESIS_TOKEN)
        next_tok = self.peek_token(i[0])
        if next_tok.type == TokenType.WORD_TOKEN:
            fn.arguments = self.parse_arguments(i)
        self.consume_token_type(i, TokenType.CLOSE_PARENTHESIS_TOKEN)

        fn.body_statements = self.parse_statements(i)
        if all(
            isinstance(s, (EmptyLineStatement, CommentStatement))
            for s in fn.body_statements
        ):
            raise ParserError(f"{fn.fn_name}() can't be empty")

        self.ast.append(fn)
        return fn

    def parse_statements(self, i: List[int]):
        stmts: List[Statement] = []

        self.increase_parsing_depth()
        self.consume_space(i)
        self.consume_token_type(i, TokenType.OPEN_BRACE_TOKEN)

        if self.peek_token(i[0]).type == TokenType.NEWLINE_TOKEN:
            i[0] += 1

        self.indentation += 1

        seen_newline = False
        newline_allowed = False

        while True:
            if self.is_end_of_block(i):
                break

            tok = self.peek_token(i[0])
            if tok.type == TokenType.NEWLINE_TOKEN:
                if not newline_allowed:
                    raise ParserError(
                        f"Unexpected empty line, on line {self.get_token_line_number(i[0])}"
                    )
                i[0] += 1
                seen_newline = True
                newline_allowed = False
                stmts.append(EmptyLineStatement())
            else:
                newline_allowed = True

                self.consume_indentation(i)

                stmt = self.parse_statement(i)
                stmts.append(stmt)

                self.consume_token_type(i, TokenType.NEWLINE_TOKEN)

        if seen_newline and not newline_allowed:
            raise ParserError(
                f"Unexpected empty line, on line {self.get_token_line_number(i[0]-1)}"
            )

        self.indentation -= 1

        if self.indentation > 0:
            self.consume_indentation(i)

        self.consume_token_type(i, TokenType.CLOSE_BRACE_TOKEN)

        self.decrease_parsing_depth()

        return stmts

    def consume_space(self, i: List[int]):
        tok = self.peek_token(i[0])
        if tok.type != TokenType.SPACE_TOKEN:
            raise ParserError(
                f"Expected token type SPACE_TOKEN, but got {tok.type.name} on line {self.get_token_line_number(i[0])}"
            )
        i[0] += 1

    def consume_indentation(self, i: List[int]):
        self.assert_token_type(i[0], TokenType.INDENTATION_TOKEN)
        spaces = len(self.peek_token(i[0]).value)
        expected = self.indentation * SPACES_PER_INDENT
        if spaces != expected:
            raise ParserError(
                f"Expected {expected} spaces, but got {spaces} spaces on line {self.get_token_line_number(i[0])}"
            )
        i[0] += 1

    def is_end_of_block(self, i: List[int]):
        tok = self.peek_token(i[0])
        if tok.type == TokenType.CLOSE_BRACE_TOKEN:
            return True
        elif tok.type == TokenType.NEWLINE_TOKEN:
            return False
        elif tok.type == TokenType.INDENTATION_TOKEN:
            spaces = len(tok.value)
            return spaces == (self.indentation - 1) * SPACES_PER_INDENT
        else:
            raise ParserError(
                f"Expected indentation, newline, or '}}', but got '{tok.value}' on line {self.get_token_line_number(i[0])}"
            )

    def increase_parsing_depth(self):
        self.parsing_depth += 1
        if self.parsing_depth >= MAX_PARSING_DEPTH:
            raise ParserError(
                f"There is a function that contains more than {MAX_PARSING_DEPTH} levels of nested expressions"
            )

    def decrease_parsing_depth(self):
        if self.parsing_depth <= 0:
            raise ParserError("Parsing depth underflow")
        self.parsing_depth -= 1

    def parse_local_variable(self, i: List[int]):
        name_token_index = i[0]
        var_token = self.consume_token(i)
        var_name = var_token.value

        var_type = None
        var_type_name = None

        if self.peek_token(i[0]).type == TokenType.COLON_TOKEN:
            i[0] += 1

            if var_name == "me":
                raise ParserError(
                    "The local variable 'me' has to have its name changed to something else, since grug already declares that variable"
                )

            self.consume_space(i)
            type_token = self.consume_token(i)
            if type_token.type != TokenType.WORD_TOKEN:
                raise ParserError(
                    f"Expected a word token after the colon on line {self.get_token_line_number(name_token_index)}"
                )

            var_type = Parser.parse_type(type_token.value)
            var_type_name = type_token.value

            if var_type in (Type.RESOURCE, Type.ENTITY):
                raise ParserError(
                    f"The variable '{var_name}' can't have '{var_type_name}' as its type"
                )

        if self.peek_token(i[0]).type != TokenType.SPACE_TOKEN:
            raise ParserError(
                f"The variable '{var_name}' was not assigned a value on line {self.get_token_line_number(name_token_index)}"
            )

        self.consume_space(i)

        self.consume_token_type(i, TokenType.ASSIGNMENT_TOKEN)

        if var_name == "me":
            raise ParserError(
                "Assigning a new value to the entity's 'me' variable is not allowed"
            )

        self.consume_space(i)

        expr = self.parse_expression(i)

        return VariableStatement(var_name, var_type, var_type_name, expr)

    def parse_global_variable(self, i: List[int]):
        name_token_index = i[0]
        name_token = self.consume_token(i)
        global_name = name_token.value

        if global_name == "me":
            raise ParserError(
                "The global variable 'me' has to have its name changed to something else, since grug already declares that variable"
            )

        self.consume_token_type(i, TokenType.COLON_TOKEN)

        self.consume_space(i)
        type_token = self.consume_token(i)
        if type_token.type != TokenType.WORD_TOKEN:
            raise ParserError(
                f"Expected a word token after the colon on line {self.get_token_line_number(name_token_index)}"
            )

        global_type = Parser.parse_type(type_token.value)
        global_type_name = type_token.value

        if global_type == Type.RESOURCE:
            raise ParserError(
                f"The global variable '{global_name}' can't have 'resource' as its type"
            )
        if global_type == Type.ENTITY:
            raise ParserError(
                f"The global variable '{global_name}' can't have 'entity' as its type"
            )

        if self.peek_token(i[0]).type != TokenType.SPACE_TOKEN:
            raise ParserError(
                f"The global variable '{global_name}' was not assigned a value on line {self.get_token_line_number(name_token_index)}"
            )

        self.consume_space(i)
        self.consume_token_type(i, TokenType.ASSIGNMENT_TOKEN)

        self.consume_space(i)
        expr = self.parse_expression(i)

        return VariableStatement(global_name, global_type, global_type_name, expr)

    def parse_unary(self, i: List[int]):
        self.increase_parsing_depth()
        token = self.peek_token(i[0])
        if token.type in (TokenType.MINUS_TOKEN, TokenType.NOT_TOKEN):
            i[0] += 1
            if token.type == TokenType.NOT_TOKEN:
                self.consume_space(i)
            expr = UnaryExpr(token.type, self.parse_unary(i))
            self.decrease_parsing_depth()
            return expr
        self.decrease_parsing_depth()
        return self.parse_call(i)

    def parse_call(self, i: List[int]):
        self.increase_parsing_depth()

        expr = self.parse_primary(i)

        token = self.peek_token(i[0])
        if token.type != TokenType.OPEN_PARENTHESIS_TOKEN:
            self.decrease_parsing_depth()
            return expr

        if not isinstance(expr, IdentifierExpr):
            # TODO: I am pretty sure a grug-tests test needs to be added for this,
            #       but I should add all missing tests at once using a Python line coverage reporting tool.
            raise ParserError(
                f"Unexpected '(' after non-identifier at line {self.get_token_line_number(i[0])}"
            )

        fn_name = expr.name
        expr = CallExpr(fn_name)

        if fn_name.startswith("helper_"):
            self.called_helper_fn_names.add(fn_name)

        i[0] += 1

        token = self.peek_token(i[0])
        if token.type == TokenType.CLOSE_PARENTHESIS_TOKEN:
            i[0] += 1
            self.decrease_parsing_depth()
            return expr

        while True:
            arg = self.parse_expression(i)
            expr.arguments.append(arg)

            token = self.peek_token(i[0])
            if token.type != TokenType.COMMA_TOKEN:
                self.consume_token_type(i, TokenType.CLOSE_PARENTHESIS_TOKEN)
                break
            i[0] += 1
            self.consume_space(i)

        self.decrease_parsing_depth()
        return expr

    def str_to_number(self, s: str):
        f = float(s)

        # Overflow
        if not math.isfinite(f) or abs(f) > MAX_F64:
            raise ParserError(f"The number {s} is too big")

        # Underflow
        if f != 0.0 and abs(f) < MIN_F64:
            raise ParserError(f"The number {s} is too close to zero")

        # Check if conversion resulted in zero due to underflow
        if f == 0.0:
            # Check if the string actually represents zero or if it underflowed
            if any(c in s for c in "123456789"):
                raise ParserError(f"The number {s} is too close to zero")

        return f

    def parse_primary(self, i: List[int]):
        self.increase_parsing_depth()

        token = self.peek_token(i[0])

        expr: Expr

        tname = token.type.name
        if tname == "OPEN_PARENTHESIS_TOKEN":
            i[0] += 1
            expr = ParenthesizedExpr(self.parse_expression(i))
            self.consume_token_type(i, TokenType.CLOSE_PARENTHESIS_TOKEN)
        elif tname == "TRUE_TOKEN":
            i[0] += 1
            expr = TrueExpr()
        elif tname == "FALSE_TOKEN":
            i[0] += 1
            expr = FalseExpr()
        elif tname == "STRING_TOKEN":
            i[0] += 1
            expr = StringExpr(token.value)
        elif tname == "WORD_TOKEN":
            i[0] += 1
            expr = IdentifierExpr(token.value)
        elif tname == "NUMBER_TOKEN":
            i[0] += 1
            expr = NumberExpr(self.str_to_number(token.value), token.value)
        else:
            raise ParserError(
                f"Expected a primary expression token, but got token type {tname} on line {self.get_token_line_number(i[0])}"
            )

        self.decrease_parsing_depth()
        return expr

    def parse_factor(self, i: List[int]):
        expr = self.parse_unary(i)
        while True:
            tok1 = self.peek_token(i[0])
            if (
                tok1
                and tok1.type == TokenType.SPACE_TOKEN
                and self.peek_token(i[0] + 1).type
                in (TokenType.MULTIPLICATION_TOKEN, TokenType.DIVISION_TOKEN)
            ):
                i[0] += 1
                op = self.consume_token(i).type
                self.consume_space(i)
                right_expr = self.parse_unary(i)
                expr = BinaryExpr(expr, op, right_expr)
            else:
                break
        return expr

    def parse_term(self, i: List[int]):
        expr = self.parse_factor(i)
        while True:
            tok1 = self.peek_token(i[0])
            if (
                tok1
                and tok1.type == TokenType.SPACE_TOKEN
                and self.peek_token(i[0] + 1).type
                in (
                    TokenType.PLUS_TOKEN,
                    TokenType.MINUS_TOKEN,
                )
            ):
                i[0] += 1
                op = self.consume_token(i).type
                self.consume_space(i)
                right_expr = self.parse_factor(i)
                expr = BinaryExpr(expr, op, right_expr)
            else:
                break
        return expr

    def parse_comparison(self, i: List[int]):
        expr = self.parse_term(i)
        while True:
            tok1 = self.peek_token(i[0])
            if (
                tok1
                and tok1.type == TokenType.SPACE_TOKEN
                and self.peek_token(i[0] + 1).type
                in (
                    TokenType.GREATER_OR_EQUAL_TOKEN,
                    TokenType.GREATER_TOKEN,
                    TokenType.LESS_OR_EQUAL_TOKEN,
                    TokenType.LESS_TOKEN,
                )
            ):
                i[0] += 1
                op = self.consume_token(i).type
                self.consume_space(i)
                right_expr = self.parse_term(i)
                expr = BinaryExpr(expr, op, right_expr)
            else:
                break
        return expr

    def parse_equality(self, i: List[int]):
        expr = self.parse_comparison(i)
        while True:
            tok1 = self.peek_token(i[0])
            if (
                tok1
                and tok1.type == TokenType.SPACE_TOKEN
                and self.peek_token(i[0] + 1).type
                in (
                    TokenType.EQUALS_TOKEN,
                    TokenType.NOT_EQUALS_TOKEN,
                )
            ):
                i[0] += 1
                op = self.consume_token(i).type
                self.consume_space(i)
                right_expr = self.parse_comparison(i)
                expr = BinaryExpr(expr, op, right_expr)
            else:
                break
        return expr

    def parse_and(self, i: List[int]):
        expr = self.parse_equality(i)
        while True:
            tok1 = self.peek_token(i[0])
            if (
                tok1
                and tok1.type == TokenType.SPACE_TOKEN
                and self.peek_token(i[0] + 1).type == TokenType.AND_TOKEN
            ):
                i[0] += 1
                op = self.consume_token(i).type
                self.consume_space(i)
                right_expr = self.parse_equality(i)
                expr = LogicalExpr(expr, op, right_expr)
            else:
                break
        return expr

    def parse_or(self, i: List[int]):
        expr = self.parse_and(i)
        while True:
            tok1 = self.peek_token(i[0])
            if (
                tok1
                and tok1.type == TokenType.SPACE_TOKEN
                and self.peek_token(i[0] + 1).type == TokenType.OR_TOKEN
            ):
                i[0] += 1
                op = self.consume_token(i).type
                self.consume_space(i)
                right_expr = self.parse_and(i)
                expr = LogicalExpr(expr, op, right_expr)
            else:
                break
        return expr

    def parse_expression(self, i: List[int]) -> Expr:
        self.increase_parsing_depth()
        expr = self.parse_or(i)
        self.decrease_parsing_depth()
        return expr

    def parse_if_statement(self, i: List[int]):
        self.increase_parsing_depth()
        self.consume_space(i)
        condition = self.parse_expression(i)
        if_body = self.parse_statements(i)

        else_body: List[Statement] = []
        tok = self.peek_token(i[0])
        if tok and tok.type == TokenType.SPACE_TOKEN:
            i[0] += 1

            self.consume_token_type(i, TokenType.ELSE_TOKEN)

            if (
                self.peek_token(i[0]).type == TokenType.SPACE_TOKEN
                and self.peek_token(i[0] + 1).type == TokenType.IF_TOKEN
            ):
                i[0] += 2
                else_body = [self.parse_if_statement(i)]
            else:
                else_body = self.parse_statements(i)

        self.decrease_parsing_depth()
        return IfStatement(condition, if_body, else_body)

    def parse_while_statement(self, i: List[int]):
        self.increase_parsing_depth()
        self.consume_space(i)
        condition = self.parse_expression(i)

        self.loop_depth += 1
        body = self.parse_statements(i)
        self.loop_depth -= 1

        self.decrease_parsing_depth()
        return WhileStatement(condition, body)
