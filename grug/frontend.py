from __future__ import annotations

import math
import struct
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Union

SPACES_PER_INDENT = 4
MAX_VARIABLES_PER_FUNCTION = 1000
MAX_GLOBAL_VARIABLES = 1000
MAX_FILE_ENTITY_TYPE_LENGTH = 420
MAX_ENTITY_DEPENDENCY_NAME_LENGTH = 420
MAX_PARSING_DEPTH = 100

MIN_F64 = struct.unpack("!d", struct.pack("!Q", 0x0010000000000000))[0]
MAX_F64 = struct.unpack("!d", struct.pack("!Q", 0x7FEFFFFFFFFFFFFF))[0]


class TokenType(Enum):
    OPEN_PARENTHESIS_TOKEN = auto()
    CLOSE_PARENTHESIS_TOKEN = auto()
    OPEN_BRACE_TOKEN = auto()
    CLOSE_BRACE_TOKEN = auto()
    PLUS_TOKEN = auto()
    MINUS_TOKEN = auto()
    MULTIPLICATION_TOKEN = auto()
    DIVISION_TOKEN = auto()
    COMMA_TOKEN = auto()
    COLON_TOKEN = auto()
    NEWLINE_TOKEN = auto()
    EQUALS_TOKEN = auto()
    NOT_EQUALS_TOKEN = auto()
    ASSIGNMENT_TOKEN = auto()
    GREATER_OR_EQUAL_TOKEN = auto()
    GREATER_TOKEN = auto()
    LESS_OR_EQUAL_TOKEN = auto()
    LESS_TOKEN = auto()
    AND_TOKEN = auto()
    OR_TOKEN = auto()
    NOT_TOKEN = auto()
    TRUE_TOKEN = auto()
    FALSE_TOKEN = auto()
    IF_TOKEN = auto()
    ELSE_TOKEN = auto()
    WHILE_TOKEN = auto()
    BREAK_TOKEN = auto()
    RETURN_TOKEN = auto()
    CONTINUE_TOKEN = auto()
    SPACE_TOKEN = auto()
    INDENTATION_TOKEN = auto()
    STRING_TOKEN = auto()
    WORD_TOKEN = auto()
    NUMBER_TOKEN = auto()
    COMMENT_TOKEN = auto()


@dataclass
class Token:
    type: TokenType
    value: str


class TokenizerError(Exception):
    pass


class Tokenizer:
    def __init__(self, src: str):
        self.src = src

    def tokenize(self):
        tokens: List[Token] = []
        src = self.src
        i = 0
        while i < len(src):
            c = src[i]
            if c == "(":
                tokens.append(Token(TokenType.OPEN_PARENTHESIS_TOKEN, c))
                i += 1
            elif c == ")":
                tokens.append(Token(TokenType.CLOSE_PARENTHESIS_TOKEN, c))
                i += 1
            elif c == "{":
                tokens.append(Token(TokenType.OPEN_BRACE_TOKEN, c))
                i += 1
            elif c == "}":
                tokens.append(Token(TokenType.CLOSE_BRACE_TOKEN, c))
                i += 1
            elif c == "+":
                tokens.append(Token(TokenType.PLUS_TOKEN, c))
                i += 1
            elif c == "-":
                tokens.append(Token(TokenType.MINUS_TOKEN, c))
                i += 1
            elif c == "*":
                tokens.append(Token(TokenType.MULTIPLICATION_TOKEN, c))
                i += 1
            elif c == "/":
                tokens.append(Token(TokenType.DIVISION_TOKEN, c))
                i += 1
            elif c == ",":
                tokens.append(Token(TokenType.COMMA_TOKEN, c))
                i += 1
            elif c == ":":
                tokens.append(Token(TokenType.COLON_TOKEN, c))
                i += 1
            elif c == "\n":
                tokens.append(Token(TokenType.NEWLINE_TOKEN, c))
                i += 1
            elif c == "=" and i + 1 < len(src) and src[i + 1] == "=":
                tokens.append(Token(TokenType.EQUALS_TOKEN, "=="))
                i += 2
            elif c == "!" and i + 1 < len(src) and src[i + 1] == "=":
                tokens.append(Token(TokenType.NOT_EQUALS_TOKEN, "!="))
                i += 2
            elif c == "=":
                tokens.append(Token(TokenType.ASSIGNMENT_TOKEN, c))
                i += 1
            elif c == ">" and i + 1 < len(src) and src[i + 1] == "=":
                tokens.append(Token(TokenType.GREATER_OR_EQUAL_TOKEN, ">="))
                i += 2
            elif c == ">":
                tokens.append(Token(TokenType.GREATER_TOKEN, ">"))
                i += 1
            elif c == "<" and i + 1 < len(src) and src[i + 1] == "=":
                tokens.append(Token(TokenType.LESS_OR_EQUAL_TOKEN, "<="))
                i += 2
            elif c == "<":
                tokens.append(Token(TokenType.LESS_TOKEN, "<"))
                i += 1
            elif src.startswith("and", i) and self.is_end_of_word(i + 3):
                tokens.append(Token(TokenType.AND_TOKEN, "and"))
                i += 3
            elif src.startswith("or", i) and self.is_end_of_word(i + 2):
                tokens.append(Token(TokenType.OR_TOKEN, "or"))
                i += 2
            elif src.startswith("not", i) and self.is_end_of_word(i + 3):
                tokens.append(Token(TokenType.NOT_TOKEN, "not"))
                i += 3
            elif src.startswith("true", i) and self.is_end_of_word(i + 4):
                tokens.append(Token(TokenType.TRUE_TOKEN, "true"))
                i += 4
            elif src.startswith("false", i) and self.is_end_of_word(i + 5):
                tokens.append(Token(TokenType.FALSE_TOKEN, "false"))
                i += 5
            elif src.startswith("if", i) and self.is_end_of_word(i + 2):
                tokens.append(Token(TokenType.IF_TOKEN, "if"))
                i += 2
            elif src.startswith("else", i) and self.is_end_of_word(i + 4):
                tokens.append(Token(TokenType.ELSE_TOKEN, "else"))
                i += 4
            elif src.startswith("while", i) and self.is_end_of_word(i + 5):
                tokens.append(Token(TokenType.WHILE_TOKEN, "while"))
                i += 5
            elif src.startswith("break", i) and self.is_end_of_word(i + 5):
                tokens.append(Token(TokenType.BREAK_TOKEN, "break"))
                i += 5
            elif src.startswith("return", i) and self.is_end_of_word(i + 6):
                tokens.append(Token(TokenType.RETURN_TOKEN, "return"))
                i += 6
            elif src.startswith("continue", i) and self.is_end_of_word(i + 8):
                tokens.append(Token(TokenType.CONTINUE_TOKEN, "continue"))
                i += 8
            elif c == " ":
                if i + 1 >= len(src) or src[i + 1] != " ":
                    tokens.append(Token(TokenType.SPACE_TOKEN, " "))
                    i += 1
                    continue

                old_i = i
                while i < len(src) and src[i] == " ":
                    i += 1

                spaces = i - old_i

                if spaces % SPACES_PER_INDENT != 0:
                    raise TokenizerError(
                        f"Encountered {spaces} spaces, while indentation expects multiples of {SPACES_PER_INDENT} spaces, on line {self.get_character_line_number(i)}"
                    )

                tokens.append(Token(TokenType.INDENTATION_TOKEN, " " * spaces))
            elif c == '"':
                open_quote_index = i
                i += 1
                start = i
                while i < len(src) and src[i] != '"':
                    i += 1
                if i >= len(src):
                    raise TokenizerError(
                        f'Unclosed " on line {self.get_character_line_number(open_quote_index + 1)}'
                    )
                tokens.append(Token(TokenType.STRING_TOKEN, src[start:i]))
                i += 1
            elif c.isalpha() or c == "_":
                start = i
                while i < len(src) and (src[i].isalnum() or src[i] == "_"):
                    i += 1
                tokens.append(Token(TokenType.WORD_TOKEN, src[start:i]))
            elif c.isdigit():
                start = i
                seen_period = False
                i += 1
                while i < len(src) and (src[i].isdigit() or src[i] == "."):
                    if src[i] == ".":
                        if seen_period:
                            raise TokenizerError(
                                f"Encountered two '.' periods in a number on line {self.get_character_line_number(i)}"
                            )
                        seen_period = True
                    i += 1

                if src[i - 1] == ".":
                    raise TokenizerError(
                        f"Missing digit after decimal point in '{src[start:i]}'"
                    )

                tokens.append(Token(TokenType.NUMBER_TOKEN, src[start:i]))
            elif c == "#":
                i += 1
                if i >= len(src) or src[i] != " ":
                    raise TokenizerError(
                        f"Expected a single space after the '#' on line {self.get_character_line_number(i)}"
                    )
                i += 1
                start = i
                while i < len(src) and src[i] not in "\r\n":
                    if not src[i].isprintable():
                        raise TokenizerError(
                            f"Unexpected unprintable character in comment on line {self.get_character_line_number(i + 1)}"
                        )
                    i += 1

                comment_len = i - start
                if comment_len == 0:
                    raise TokenizerError(
                        f"Expected the comment to contain some text on line {self.get_character_line_number(i)}"
                    )

                if src[i - 1].isspace():
                    raise TokenizerError(
                        f"A comment has trailing whitespace on line {self.get_character_line_number(i)}"
                    )

                tokens.append(Token(TokenType.COMMENT_TOKEN, src[start:i]))
            else:
                raise TokenizerError(
                    f"Unrecognized character '{c}' on line {self.get_character_line_number(i + 1)}"
                )

        return tokens

    def get_character_line_number(self, idx: int):
        """
        Calculate the line number for a given character index.
        Examples:
        "" => 1
        "<a>" => 1
        "a<b>" => 1
        "<\\n>" => 1
        "\\n<a>" => 2
        "\\n<\\n>" => 2
        """
        line_number = 1

        for i in range(idx):
            if self.src[i] == "\n" or (
                self.src[i] == "\r"
                and i + 1 < len(self.src)
                and self.src[i + 1] == "\n"
            ):
                line_number += 1

        return line_number

    def is_end_of_word(self, idx: int):
        """Check if position is at end of word (not alphanumeric or underscore)"""
        return idx >= len(self.src) or not (
            self.src[idx].isalnum() or self.src[idx] == "_"
        )


class ParserError(Exception):
    pass


class Type(Enum):
    BOOL = auto()
    NUMBER = auto()
    STRING = auto()
    ID = auto()
    RESOURCE = auto()
    ENTITY = auto()


# TODO: Ensure this object never shows up in the serialized JSON
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
    assignment_expr: Expr


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
        self.parsing_depth = 0
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

        assignment_expr = self.parse_expression(i)

        return VariableStatement(var_name, var_type, var_type_name, assignment_expr)

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
        assignment_expr = self.parse_expression(i)

        return VariableStatement(
            global_name, global_type, global_type_name, assignment_expr
        )

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
            tok2 = self.peek_token(i[0])
            if tok2.type == TokenType.ELSE_TOKEN:
                i[0] += 1
                tok_next = self.peek_token(i[0])
                if (
                    tok_next.type == TokenType.SPACE_TOKEN
                    and self.peek_token(i[0] + 1).type == TokenType.IF_TOKEN
                ):
                    i[0] += 2
                    else_body = [self.parse_if_statement(i)]
                else:
                    self.consume_space(i)
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
    def __init__(self, ast: Ast, mod_name: str, entity_type: str, mod_api: ModApi):
        self.ast = ast
        self.mod = mod_name
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
        if len(self.global_variables) >= MAX_GLOBAL_VARIABLES:
            raise TypePropagationError(
                f"There are more than {MAX_GLOBAL_VARIABLES} global variables in a grug file"
            )

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
        if len(self.local_variables) >= MAX_VARIABLES_PER_FUNCTION:
            raise TypePropagationError(
                f"There are more than {MAX_VARIABLES_PER_FUNCTION} variables in a function"
            )

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

        mod_name = self.mod
        entity_name = string

        colon_pos = string.find(":")
        if colon_pos != -1:
            if colon_pos == 0:
                raise TypePropagationError(f"Entity '{string}' is missing a mod name")

            temp_mod_name = string[:colon_pos]

            if len(temp_mod_name) >= MAX_ENTITY_DEPENDENCY_NAME_LENGTH:
                raise TypePropagationError(
                    f"There are more than {MAX_ENTITY_DEPENDENCY_NAME_LENGTH} characters in the entity '{string}', exceeding MAX_ENTITY_DEPENDENCY_NAME_LENGTH"
                )

            mod_name = temp_mod_name
            entity_name = string[colon_pos + 1 :]

            if not entity_name:
                raise TypePropagationError(
                    f"Entity '{string}' specifies the mod name '{mod_name}', but it is missing an entity name after the ':'"
                )

            if mod_name == self.mod:
                raise TypePropagationError(
                    f"Entity '{string}' its mod name '{mod_name}' is invalid, since the file it is in refers to its own mod; just change it to '{entity_name}'"
                )

        for c in mod_name:
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

        if not resource_extension or not string.endswith(resource_extension):
            raise TypePropagationError(
                f"The resource '{string}' was supposed to have extension '{resource_extension}'"
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

            if param.type_name != "id" and self.is_wrong_type(
                arg.result.type,
                param.type,
                arg.result.type_name,
                param.type_name,
            ):
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
        else:
            raise TypePropagationError(f"The function '{fn_name}' does not exist")

    def fill_binary_expr(self, expr: BinaryExpr | LogicalExpr):
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
        if not is_id and self.is_wrong_type(
            left.result.type,
            right.result.type,
            left.result.type_name,
            right.result.type_name,
        ):
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
        self.fill_expr(stmt.assignment_expr)

        var = self.get_variable(stmt.name)

        if stmt.type:
            assert stmt.type_name

            if var:
                raise TypePropagationError(f"The variable '{stmt.name}' already exists")

            if stmt.type_name != "id" and self.is_wrong_type(
                stmt.type,
                stmt.assignment_expr.result.type,
                stmt.type_name,
                stmt.assignment_expr.result.type_name,
            ):
                raise TypePropagationError(
                    f"Can't assign {stmt.assignment_expr.result.type_name} to '{stmt.name}', which has type {stmt.type_name}"
                )

            self.add_local_variable(stmt.name, stmt.type, stmt.type_name)
        else:
            if not var:
                raise TypePropagationError(
                    f"Can't assign to the variable '{stmt.name}', since it does not exist"
                )

            if stmt.name in self.global_variables and var.type == Type.ID:
                raise TypePropagationError("Global id variables can't be reassigned")

            if var.type_name != "id" and self.is_wrong_type(
                var.type,
                stmt.assignment_expr.result.type,
                var.type_name,
                stmt.assignment_expr.result.type_name,
            ):
                raise TypePropagationError(
                    f"Can't assign {stmt.assignment_expr.result.type_name} to '{var.name}', which has type {var.type_name}"
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

                    if self.fn_return_type_name != "id" and self.is_wrong_type(
                        stmt.value.result.type,
                        self.fn_return_type,
                        stmt.value.result.type_name,
                        self.fn_return_type_name,
                    ):
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
                assert stmt.assignment_expr

                self.check_global_expr(stmt.assignment_expr, stmt.name)
                self.fill_expr(stmt.assignment_expr)

                # Check for assignment to 'me'
                if isinstance(stmt.assignment_expr, IdentifierExpr):
                    if stmt.assignment_expr.name == "me":
                        raise TypePropagationError(
                            "Global variables can't be assigned 'me'"
                        )

                if stmt.type_name != "id" and self.is_wrong_type(
                    stmt.type,
                    stmt.assignment_expr.result.type,
                    stmt.type_name,
                    stmt.assignment_expr.result.type_name,
                ):
                    raise TypePropagationError(
                        f"Can't assign {stmt.assignment_expr.result.type_name} to '{stmt.name}', which has type {stmt.type_name}"
                    )

                self.add_global_variable(stmt.name, stmt.type, stmt.type_name)

    def fill(self):
        """Main entry point for type propagation"""
        self.fill_global_variables()
        self.fill_on_fns()
        self.fill_helper_fns()


class FrontendError(Exception):
    pass


class Frontend:
    def __init__(self, mod_api: ModApi):
        self.mod_api = mod_api

    def compile_grug_file(self, source: str, mod_name: str, entity_type: str):
        """
        Compile source text and return an error message string,
        or None if compilation succeeded.
        """
        try:
            tokens = Tokenizer(source).tokenize()

            ast = Parser(tokens).parse()

            TypePropagator(ast, mod_name, entity_type, self.mod_api).fill()
        except (TokenizerError, ParserError, TypePropagationError) as e:
            raise FrontendError(str(e)) from e

        return ast
