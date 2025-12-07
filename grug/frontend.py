import struct
import sys
import traceback
from enum import Enum, auto

SPACES_PER_INDENT = 4
MAX_VARIABLES_PER_FUNCTION = 1000
MAX_GLOBAL_VARIABLES = 1000
MAX_FILE_ENTITY_TYPE_LENGTH = 420
MAX_ENTITY_DEPENDENCY_NAME_LENGTH = 420
MAX_PARSING_DEPTH = 100

MAX_F32 = struct.unpack("!f", struct.pack("!I", 0x7F7FFFFF))[0]


class TokenType(Enum):
    OPEN_PARENTHESIS_TOKEN = auto()
    CLOSE_PARENTHESIS_TOKEN = auto()
    OPEN_BRACE_TOKEN = auto()
    CLOSE_BRACE_TOKEN = auto()
    PLUS_TOKEN = auto()
    MINUS_TOKEN = auto()
    MULTIPLICATION_TOKEN = auto()
    DIVISION_TOKEN = auto()
    REMAINDER_TOKEN = auto()
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
    I32_TOKEN = auto()
    F32_TOKEN = auto()
    COMMENT_TOKEN = auto()


TOKEN_TYPE_STRINGS = {t: t.name for t in TokenType}


class Token:
    def __init__(self, ttype: TokenType, value: str):
        self.type = ttype
        self.value = value

    def __repr__(self):
        return f"{self.type.name}({repr(self.value)})"


class TokenizerError(Exception):
    pass


class Tokenizer:
    def __init__(self, source: str):
        self.source = source
        self.tokens = []
        self.pos = 0

    def get_character_line_number(self, character_index: int) -> int:
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

        for i in range(character_index):
            if self.source[i] == "\n" or (
                self.source[i] == "\r"
                and i + 1 < len(self.source)
                and self.source[i + 1] == "\n"
            ):
                line_number += 1

        return line_number

    def tokenize(self):
        src = self.source
        i = 0
        while i < len(src):
            c = src[i]
            if c == "(":
                self.tokens.append(Token(TokenType.OPEN_PARENTHESIS_TOKEN, c))
                i += 1
            elif c == ")":
                self.tokens.append(Token(TokenType.CLOSE_PARENTHESIS_TOKEN, c))
                i += 1
            elif c == "{":
                self.tokens.append(Token(TokenType.OPEN_BRACE_TOKEN, c))
                i += 1
            elif c == "}":
                self.tokens.append(Token(TokenType.CLOSE_BRACE_TOKEN, c))
                i += 1
            elif c == "+":
                self.tokens.append(Token(TokenType.PLUS_TOKEN, c))
                i += 1
            elif c == "-":
                self.tokens.append(Token(TokenType.MINUS_TOKEN, c))
                i += 1
            elif c == "*":
                self.tokens.append(Token(TokenType.MULTIPLICATION_TOKEN, c))
                i += 1
            elif c == "/":
                self.tokens.append(Token(TokenType.DIVISION_TOKEN, c))
                i += 1
            elif c == "%":
                self.tokens.append(Token(TokenType.REMAINDER_TOKEN, c))
                i += 1
            elif c == ",":
                self.tokens.append(Token(TokenType.COMMA_TOKEN, c))
                i += 1
            elif c == ":":
                self.tokens.append(Token(TokenType.COLON_TOKEN, c))
                i += 1
            elif c == "\n":
                self.tokens.append(Token(TokenType.NEWLINE_TOKEN, c))
                i += 1
            elif c == "=" and i + 1 < len(src) and src[i + 1] == "=":
                self.tokens.append(Token(TokenType.EQUALS_TOKEN, "=="))
                i += 2
            elif c == "!" and i + 1 < len(src) and src[i + 1] == "=":
                self.tokens.append(Token(TokenType.NOT_EQUALS_TOKEN, "!="))
                i += 2
            elif c == "=":
                self.tokens.append(Token(TokenType.ASSIGNMENT_TOKEN, c))
                i += 1
            elif c == ">" and i + 1 < len(src) and src[i + 1] == "=":
                self.tokens.append(Token(TokenType.GREATER_OR_EQUAL_TOKEN, ">="))
                i += 2
            elif c == ">":
                self.tokens.append(Token(TokenType.GREATER_TOKEN, ">"))
                i += 1
            elif c == "<" and i + 1 < len(src) and src[i + 1] == "=":
                self.tokens.append(Token(TokenType.LESS_OR_EQUAL_TOKEN, "<="))
                i += 2
            elif c == "<":
                self.tokens.append(Token(TokenType.LESS_TOKEN, "<"))
                i += 1
            elif src.startswith("and", i) and self.is_end_of_word(i + 3):
                self.tokens.append(Token(TokenType.AND_TOKEN, "and"))
                i += 3
            elif src.startswith("or", i) and self.is_end_of_word(i + 2):
                self.tokens.append(Token(TokenType.OR_TOKEN, "or"))
                i += 2
            elif src.startswith("not", i) and self.is_end_of_word(i + 3):
                self.tokens.append(Token(TokenType.NOT_TOKEN, "not"))
                i += 3
            elif src.startswith("true", i) and self.is_end_of_word(i + 4):
                self.tokens.append(Token(TokenType.TRUE_TOKEN, "true"))
                i += 4
            elif src.startswith("false", i) and self.is_end_of_word(i + 5):
                self.tokens.append(Token(TokenType.FALSE_TOKEN, "false"))
                i += 5
            elif src.startswith("if", i) and self.is_end_of_word(i + 2):
                self.tokens.append(Token(TokenType.IF_TOKEN, "if"))
                i += 2
            elif src.startswith("else", i) and self.is_end_of_word(i + 4):
                self.tokens.append(Token(TokenType.ELSE_TOKEN, "else"))
                i += 4
            elif src.startswith("while", i) and self.is_end_of_word(i + 5):
                self.tokens.append(Token(TokenType.WHILE_TOKEN, "while"))
                i += 5
            elif src.startswith("break", i) and self.is_end_of_word(i + 5):
                self.tokens.append(Token(TokenType.BREAK_TOKEN, "break"))
                i += 5
            elif src.startswith("return", i) and self.is_end_of_word(i + 6):
                self.tokens.append(Token(TokenType.RETURN_TOKEN, "return"))
                i += 6
            elif src.startswith("continue", i) and self.is_end_of_word(i + 8):
                self.tokens.append(Token(TokenType.CONTINUE_TOKEN, "continue"))
                i += 8
            elif c == " ":
                if i + 1 >= len(src) or src[i + 1] != " ":
                    self.tokens.append(Token(TokenType.SPACE_TOKEN, " "))
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

                self.tokens.append(Token(TokenType.INDENTATION_TOKEN, " " * spaces))
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
                self.tokens.append(Token(TokenType.STRING_TOKEN, src[start:i]))
                i += 1
            elif c.isalpha() or c == "_":
                start = i
                while i < len(src) and (src[i].isalnum() or src[i] == "_"):
                    i += 1
                self.tokens.append(Token(TokenType.WORD_TOKEN, src[start:i]))
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

                if seen_period:
                    if src[i - 1] == ".":
                        raise TokenizerError(
                            f"Missing digit after decimal point in '{src[start:i]}'"
                        )
                    self.tokens.append(Token(TokenType.F32_TOKEN, src[start:i]))
                else:
                    self.tokens.append(Token(TokenType.I32_TOKEN, src[start:i]))
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

                self.tokens.append(Token(TokenType.COMMENT_TOKEN, src[start:i]))
            else:
                raise TokenizerError(
                    f"Unrecognized character '{c}' on line {self.get_character_line_number(i + 1)}"
                )
        return self.tokens

    def is_end_of_word(self, idx):
        """Check if position is at end of word (not alphanumeric or underscore)"""
        return idx >= len(self.source) or not (
            self.source[idx].isalnum() or self.source[idx] == "_"
        )


class ParserError(Exception):
    pass


class Expr:
    def __init__(self, expr_type, value=None, operands=None):
        self.type = expr_type
        self.value = value
        self.operands = operands or []
        # Type propagation fields
        self.result_type = None
        self.result_type_name = None


class Statement:
    def __init__(self, stmt_type, **kwargs):
        self.type = stmt_type
        self.__dict__.update(kwargs)


class Argument:
    def __init__(self, name, arg_type, type_name):
        self.name = name
        self.type = arg_type
        self.type_name = type_name


class HelperFn:
    def __init__(self, fn_name):
        self.fn_name = fn_name
        self.arguments = []
        self.argument_count = 0
        self.return_type = "void"
        self.return_type_name = None
        self.body_statements = []
        self.calls_helper_fn = False
        self.contains_while_loop = False


class OnFn:
    def __init__(self, fn_name):
        self.fn_name = fn_name
        self.arguments = []
        self.argument_count = 0
        self.body_statements = []
        self.calls_helper_fn = False
        self.contains_while_loop = False


class Variable:
    def __init__(self, name, var_type, type_name):
        self.name = name
        self.type = var_type
        self.type_name = type_name


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.global_statements = []
        self.helper_fns = {}
        self.on_fns = {}
        self.statements = []
        self.arguments = []
        self.parsing_depth = 0
        self.loop_depth = 0
        self.parsing_depth = 0
        self.indentation = 0
        self.called_helper_fn_names = set()
        self.global_statements = []

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

                self.global_statements.append(
                    {
                        "type": "global_variable",
                        "variable": self.parse_global_variable(i),
                    }
                )

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

                self.global_statements.append({"type": "empty_line"})
                i[0] += 1
                continue

            elif tname == "COMMENT_TOKEN":
                newline_allowed = True
                self.global_statements.append(
                    {"type": "comment", "comment": token.value}
                )
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

    def peek_token(self, token_index):
        if token_index >= len(self.tokens):
            raise ParserError(
                f"token_index {token_index} was out of bounds in peek_token()"
            )
        return self.tokens[token_index]

    def consume_token(self, i):
        token_index = i[0]
        token = self.peek_token(token_index)
        i[0] += 1
        return token

    def assert_token_type(self, token_index, expected_type):
        token = self.peek_token(token_index)
        if token.type != expected_type:
            raise ParserError(
                f"Expected token type {expected_type.name}, "
                f"but got {token.type.name} on line {self.get_token_line_number(token_index)}"
            )

    def consume_token_type(self, i, expected_type):
        self.assert_token_type(i[0], expected_type)
        i[0] += 1

    def get_token_line_number(self, token_index):
        if token_index >= len(self.tokens):
            raise ParserError(
                f"token_index {token_index} out of bounds in get_token_line_number()"
            )
        line_number = 1
        for idx in range(token_index):
            if self.tokens[idx].type == TokenType.NEWLINE_TOKEN:
                line_number += 1
        return line_number

    def parse_statement(self, i):
        self.increase_parsing_depth()
        switch_token = self.peek_token(i[0])

        statement = None
        if switch_token.type == TokenType.WORD_TOKEN:
            token = self.peek_token(i[0] + 1)
            if token.type == TokenType.OPEN_PARENTHESIS_TOKEN:
                expr = self.parse_call(i)
                statement = Statement("call", expr=expr)
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
                statement = Statement("return", has_value=False)
            else:
                self.consume_space(i)
                expr = self.parse_expression(i)
                statement = Statement("return", has_value=True, value=expr)
        elif switch_token.type == TokenType.WHILE_TOKEN:
            i[0] += 1
            statement = self.parse_while_statement(i)
        elif switch_token.type == TokenType.BREAK_TOKEN:
            if self.loop_depth == 0:
                raise ParserError(
                    f"There is a break statement that isn't inside of a while loop"
                )
            i[0] += 1
            statement = Statement("break")
        elif switch_token.type == TokenType.CONTINUE_TOKEN:
            if self.loop_depth == 0:
                raise ParserError(
                    f"There is a continue statement that isn't inside of a while loop"
                )
            i[0] += 1
            statement = Statement("continue")
        elif switch_token.type == TokenType.NEWLINE_TOKEN:
            i[0] += 1
            statement = Statement("empty_line")
        elif switch_token.type == TokenType.COMMENT_TOKEN:
            i[0] += 1
            statement = Statement("comment", comment=switch_token.value)
        else:
            raise ParserError(
                f"Expected a statement token, but got token type {switch_token.type.name} on line {self.get_token_line_number(i[0])}"
            )

        self.decrease_parsing_depth()
        return statement

    def push_argument(self, argument):
        self.arguments.append(argument)
        return argument

    def parse_type(self, type_str):
        if type_str == "bool":
            return "bool"
        if type_str == "i32":
            return "i32"
        if type_str == "f32":
            return "f32"
        if type_str == "string":
            return "string"
        if type_str == "resource":
            return "resource"
        if type_str == "entity":
            return "entity"
        return "id"

    def parse_arguments(self, i):
        arguments = []

        # First argument
        name_token = self.consume_token(i)
        arg_name = name_token.value

        self.consume_token_type(i, TokenType.COLON_TOKEN)

        self.consume_space(i)
        self.assert_token_type(i[0], TokenType.WORD_TOKEN)

        type_token = self.consume_token(i)
        type_name = type_token.value
        arg_type = type_name

        if arg_type == "resource":
            raise ParserError(
                f"The argument '{arg_name}' can't have 'resource' as its type"
            )
        if arg_type == "entity":
            raise ParserError(
                f"The argument '{arg_name}' can't have 'entity' as its type"
            )

        arguments.append({"name": arg_name, "type": arg_type, "type_name": type_name})

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
            arg_type = self.parse_type(type_name)

            if arg_type == "resource":
                raise ParserError(
                    f"The argument '{arg_name}' can't have 'resource' as its type"
                )
            if arg_type == "entity":
                raise ParserError(
                    f"The argument '{arg_name}' can't have 'entity' as its type"
                )

            arguments.append(
                {"name": arg_name, "type": arg_type, "type_name": type_name}
            )

        return arguments

    def parse_helper_fn(self, i):
        fn_token = self.consume_token(i)
        fn = HelperFn(fn_token.value)

        if fn.fn_name not in self.called_helper_fn_names:
            raise ParserError(
                f"{fn.fn_name}() is defined before the first time it gets called"
            )

        self.consume_token_type(i, TokenType.OPEN_PARENTHESIS_TOKEN)

        token = self.peek_token(i[0])
        if token.type == TokenType.WORD_TOKEN:
            fn.arguments = self.parse_arguments(i)
            fn.argument_count = len(fn.arguments)

        self.consume_token_type(i, TokenType.CLOSE_PARENTHESIS_TOKEN)

        self.assert_token_type(i[0], TokenType.SPACE_TOKEN)
        token = self.peek_token(i[0] + 1)
        fn.return_type = "void"
        if token.type == TokenType.WORD_TOKEN:
            i[0] += 2
            fn.return_type = self.parse_type(token.value)
            fn.return_type_name = token.value

            if fn.return_type == "resource":
                raise ParserError(
                    f"The function '{fn.fn_name}' can't have 'resource' as its return type"
                )
            if fn.return_type == "entity":
                raise ParserError(
                    f"The function '{fn.fn_name}' can't have 'entity' as its return type"
                )

        self.indentation = 0
        fn.body_statements = self.parse_statements(i)

        if all(s.type in ("empty_line", "comment") for s in fn.body_statements):
            raise ParserError(f"{fn.fn_name}() can't be empty")

        self.global_statements.append({"type": "helper_fn", "helper_fn": fn})
        return fn

    def parse_on_fn(self, i):
        fn_token = self.consume_token(i)
        fn = OnFn(fn_token.value)

        self.consume_token_type(i, TokenType.OPEN_PARENTHESIS_TOKEN)
        next_tok = self.peek_token(i[0])
        if next_tok.type == TokenType.WORD_TOKEN:
            fn.arguments = self.parse_arguments(i)
            fn.argument_count = len(fn.arguments)
        self.consume_token_type(i, TokenType.CLOSE_PARENTHESIS_TOKEN)

        fn.body_statements = self.parse_statements(i)
        if all(s.type in ("empty_line", "comment") for s in fn.body_statements):
            raise ParserError(f"{fn.fn_name}() can't be empty")

        self.global_statements.append({"type": "on_fn", "on_fn": fn})
        return fn

    def parse_statements(self, i):
        stmts = []

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
                stmts.append(Statement("empty_line"))
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

    def consume_space(self, i):
        tok = self.peek_token(i[0])
        if tok.type != TokenType.SPACE_TOKEN:
            raise ParserError(
                f"Expected token type SPACE_TOKEN, but got {tok.type.name} on line {self.get_token_line_number(i[0])}"
            )
        i[0] += 1

    def consume_indentation(self, i):
        self.assert_token_type(i[0], TokenType.INDENTATION_TOKEN)
        spaces = len(self.peek_token(i[0]).value)
        expected = self.indentation * SPACES_PER_INDENT
        if spaces != expected:
            raise ParserError(
                f"Expected {expected} spaces, but got {spaces} spaces on line {self.get_token_line_number(i[0])}"
            )
        i[0] += 1

    def is_end_of_block(self, i):
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

    def parse_local_variable(self, i):
        name_token_index = i[0]
        var_token = self.consume_token(i)
        var_name = var_token.value

        has_type = False
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

            has_type = True
            var_type = self.parse_type(type_token.value)
            var_type_name = type_token.value

            if var_type in ("resource", "entity"):
                raise ParserError(
                    f"The variable '{var_name}' can't have '{var_type}' as its type"
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

        return Statement(
            "variable",
            name=var_name,
            has_type=has_type,
            var_type=var_type,
            var_type_name=var_type_name,
            assignment_expr=assignment_expr,
        )

    def parse_global_variable(self, i):
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

        global_type = self.parse_type(type_token.value)
        global_type_name = type_token.value

        if global_type == "resource":
            raise ParserError(
                f"The global variable '{global_name}' can't have 'resource' as its type"
            )
        if global_type == "entity":
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

        return Statement(
            "global_variable",
            name=global_name,
            var_type=global_type,
            var_type_name=global_type_name,
            assignment_expr=assignment_expr,
        )

    def parse_unary(self, i):
        self.increase_parsing_depth()
        token = self.peek_token(i[0])
        if token.type in (TokenType.MINUS_TOKEN, TokenType.NOT_TOKEN):
            i[0] += 1
            if token.type == TokenType.NOT_TOKEN:
                self.consume_space(i)
            expr = Expr("unary", token.type.name, [self.parse_unary(i)])
            self.decrease_parsing_depth()
            return expr
        self.decrease_parsing_depth()
        return self.parse_call(i)

    def parse_call(self, i):
        self.increase_parsing_depth()

        expr = self.parse_primary(i)

        token = self.peek_token(i[0])
        if token is None or token.type != TokenType.OPEN_PARENTHESIS_TOKEN:
            self.decrease_parsing_depth()
            return expr

        if expr.type != "identifier":
            raise ParserError(
                f"Unexpected '(' after non-identifier at line {self.get_token_line_number(i[0])}"
            )

        fn_name = expr.value
        if fn_name.startswith("helper_"):
            self.called_helper_fn_names.add(fn_name)

        i[0] += 1

        token = self.peek_token(i[0])
        if token.type == TokenType.CLOSE_PARENTHESIS_TOKEN:
            i[0] += 1
            expr.type = "call"
            expr.value = fn_name
            expr.operands = []
            self.decrease_parsing_depth()
            return expr

        args = []

        while True:
            arg = self.parse_expression(i)
            args.append(arg)

            token = self.peek_token(i[0])
            if token.type != TokenType.COMMA_TOKEN:
                self.consume_token_type(i, TokenType.CLOSE_PARENTHESIS_TOKEN)
                break
            i[0] += 1
            self.consume_space(i)

        expr.type = "call"
        expr.value = fn_name
        expr.operands = args

        self.decrease_parsing_depth()
        return expr

    def str_to_f32(self, s):
        f = float(s)

        # Check if the value exceeds the maximum 32-bit float
        if f > MAX_F32:
            raise ParserError(f"The f32 {s} is too big")

        # Check for underflow: non-zero value that's too small for 32-bit float
        # Minimum positive normal f32 is approximately 1.175494e-38
        MIN_F32 = 1.175494e-38
        if f != 0.0 and f < MIN_F32:
            raise ParserError(f"The f32 {s} is too close to zero")

        # Check if conversion resulted in zero due to underflow
        if f == 0.0:
            # Check if the string actually represents zero or if it underflowed
            if any(c in s for c in "123456789"):
                raise ParserError(f"The f32 {s} is too close to zero")

        return f

    def str_to_i32(self, s):
        try:
            n = int(s)
            if n > 2147483647:  # INT32_MAX
                raise ParserError(
                    f"The i32 {s} is too big, which has a maximum value of 2147483647"
                )
            assert n >= 0, "i32 should be non-negative at this point"
            return n
        except ValueError:
            raise ParserError(f"Invalid i32 value: {s}")

    def parse_primary(self, i):
        self.increase_parsing_depth()

        token = self.peek_token(i[0])
        expr = Expr(None)

        tname = token.type.name
        if tname == "OPEN_PARENTHESIS_TOKEN":
            i[0] += 1
            expr.type = "paren"
            expr.operands = [self.parse_expression(i)]
            self.consume_token_type(i, TokenType.CLOSE_PARENTHESIS_TOKEN)
        elif tname == "TRUE_TOKEN":
            i[0] += 1
            expr.type = "true"
        elif tname == "FALSE_TOKEN":
            i[0] += 1
            expr.type = "false"
        elif tname == "STRING_TOKEN":
            i[0] += 1
            expr.type = "string"
            expr.value = token.value
        elif tname == "WORD_TOKEN":
            i[0] += 1
            expr.type = "identifier"
            expr.value = token.value
        elif tname == "I32_TOKEN":
            i[0] += 1
            expr.type = "i32"
            expr.value = self.str_to_i32(token.value)
        elif tname == "F32_TOKEN":
            i[0] += 1
            expr.type = "f32"
            expr.value = self.str_to_f32(token.value)
            expr.string = token.value  # Store the original string representation
        else:
            raise ParserError(
                f"Expected a primary expression token, but got token type {tname} on line {self.get_token_line_number(i[0])}"
            )

        self.decrease_parsing_depth()
        return expr

    def parse_factor(self, i):
        expr = self.parse_unary(i)
        while True:
            tok1 = self.peek_token(i[0])
            if (
                tok1
                and tok1.type == TokenType.SPACE_TOKEN
                and self.peek_token(i[0] + 1).type
                in (
                    TokenType.MULTIPLICATION_TOKEN,
                    TokenType.DIVISION_TOKEN,
                    TokenType.REMAINDER_TOKEN,
                )
            ):
                i[0] += 1
                op_token = self.consume_token(i)
                self.consume_space(i)
                right = self.parse_unary(i)
                expr = Expr("binary", op_token.type.name, [expr, right])
            else:
                break
        return expr

    def parse_term(self, i):
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
                op_token = self.consume_token(i)
                self.consume_space(i)
                right = self.parse_factor(i)
                expr = Expr("binary", op_token.type.name, [expr, right])
            else:
                break
        return expr

    def parse_comparison(self, i):
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
                op_token = self.consume_token(i)
                self.consume_space(i)
                right = self.parse_term(i)
                expr = Expr("binary", op_token.type.name, [expr, right])
            else:
                break
        return expr

    def parse_equality(self, i):
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
                op_token = self.consume_token(i)
                self.consume_space(i)
                right = self.parse_comparison(i)
                expr = Expr("binary", op_token.type.name, [expr, right])
            else:
                break
        return expr

    def parse_and(self, i):
        expr = self.parse_equality(i)
        while True:
            tok1 = self.peek_token(i[0])
            if (
                tok1
                and tok1.type == TokenType.SPACE_TOKEN
                and self.peek_token(i[0] + 1).type == TokenType.AND_TOKEN
            ):
                i[0] += 1
                op_token = self.consume_token(i)
                self.consume_space(i)
                right = self.parse_equality(i)
                expr = Expr("logical", "AND", [expr, right])
            else:
                break
        return expr

    def parse_or(self, i):
        expr = self.parse_and(i)
        while True:
            tok1 = self.peek_token(i[0])
            if (
                tok1
                and tok1.type == TokenType.SPACE_TOKEN
                and self.peek_token(i[0] + 1).type == TokenType.OR_TOKEN
            ):
                i[0] += 1
                op_token = self.consume_token(i)
                self.consume_space(i)
                right = self.parse_and(i)
                expr = Expr("logical", "OR", [expr, right])
            else:
                break
        return expr

    def parse_expression(self, i):
        self.increase_parsing_depth()
        expr = self.parse_or(i)
        self.decrease_parsing_depth()
        return expr

    def parse_if_statement(self, i):
        self.increase_parsing_depth()
        self.consume_space(i)
        condition = self.parse_expression(i)
        if_body = self.parse_statements(i)

        else_body = []
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
        return Statement(
            "if", condition=condition, if_body=if_body, else_body=else_body
        )

    def parse_while_statement(self, i):
        self.increase_parsing_depth()
        self.consume_space(i)
        condition = self.parse_expression(i)

        self.loop_depth += 1
        body = self.parse_statements(i)
        self.loop_depth -= 1

        self.decrease_parsing_depth()
        return Statement("while", condition=condition, body=body)


class TypePropagationError(Exception):
    pass


class TypePropagator:
    def __init__(self, parser, mod_name, entity_type, mod_api):
        self.parser = parser
        self.mod = mod_name
        self.file_entity_type = entity_type
        self.mod_api = mod_api

        # Variable storage
        self.local_variables = {}
        self.global_variables = {}

        # Function context
        self.fn_return_type = None
        self.fn_return_type_name = None
        self.filled_fn_name = None

        # Flags for current function being analyzed
        self.parsed_fn_calls_helper_fn = False
        self.parsed_fn_contains_while_loop = False

        self.game_functions = mod_api["game_functions"]
        self.entity_on_functions = mod_api["entities"][entity_type].get(
            "on_functions", {}
        )

    def add_global_variable(self, name, var_type, type_name):
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

    def get_variable(self, name):
        if name in self.local_variables:
            return self.local_variables[name]
        if name in self.global_variables:
            return self.global_variables[name]
        return None

    def add_local_variable(self, name, var_type, type_name):
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

    def is_wrong_type(self, a, b, a_name, b_name):
        if a != b:
            return True
        if a != "id":
            return False
        return a_name != b_name

    def validate_entity_string(self, string):
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

    def validate_resource_string(self, string, resource_extension):
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

        if not string.endswith(resource_extension):
            raise TypePropagationError(
                f"The resource '{string}' was supposed to have extension '{resource_extension}'"
            )

    def check_arguments(self, params, call_expr):
        fn_name = call_expr.value
        args = call_expr.operands

        if len(args) < len(params):
            raise TypePropagationError(
                f"Function call '{fn_name}' expected the argument '{params[len(args)]["name"]}' with type {params[len(args)]["type"]}"
            )

        if len(args) > len(params):
            raise TypePropagationError(
                f"Function call '{fn_name}' got an unexpected extra argument with type {call_expr.operands[len(params)].result_type_name}"
            )

        for arg, param in zip(args, params):
            # Handle resource/entity string conversions
            if arg.type == "string" and param["type"] == "resource":
                arg.result_type = "resource"
                arg.result_type_name = "resource"
                arg.type = "resource"
                self.validate_resource_string(
                    arg.value,
                    (
                        param.resource_extension
                        if hasattr(param, "resource_extension")
                        else ".png"
                    ),
                )
            elif arg.type == "string" and param["type"] == "entity":
                arg.result_type = "entity"
                arg.result_type_name = "entity"
                arg.type = "entity"
                self.validate_entity_string(arg.value)

            if arg.result_type == "void":
                raise TypePropagationError(
                    f"Function call '{fn_name}' expected the type {param["type"]} for argument '{param["name"]}', but got a function call that doesn't return anything"
                )

            if param["type"] != "id" and self.is_wrong_type(
                arg.result_type,
                self.parser.parse_type(param["type"]),
                arg.result_type_name,
                param["type"],
            ):
                raise TypePropagationError(
                    f"Function call '{fn_name}' expected the type {param["type"]} for argument '{param["name"]}', but got {arg.result_type_name}"
                )

    def fill_call_expr(self, expr):
        # Fill argument expressions first
        for arg in expr.operands:
            self.fill_expr(arg)

        fn_name = expr.value

        if fn_name.startswith("helper_"):
            self.parsed_fn_calls_helper_fn = True

        # Check if it's a helper function
        if fn_name in self.parser.helper_fns:
            helper_fn = self.parser.helper_fns[fn_name]
            expr.result_type = helper_fn.return_type
            expr.result_type_name = helper_fn.return_type_name
            self.check_arguments(helper_fn.arguments, expr)
            return

        # Check if it's a game function
        if fn_name in self.game_functions:
            game_fn = self.game_functions[fn_name]
            expr.result_type = self.parser.parse_type(
                game_fn.get("return_type", "void")
            )
            expr.result_type_name = game_fn.get("return_type", "void")
            self.check_arguments(game_fn.get("arguments", []), expr)
            return

        if fn_name.startswith("on_"):
            raise TypePropagationError(
                f"Mods aren't allowed to call their own on_ functions, but '{fn_name}' was called"
            )
        else:
            raise TypePropagationError(f"The function '{fn_name}' does not exist")

    def fill_binary_expr(self, expr):
        left = expr.operands[0]
        right = expr.operands[1]

        self.fill_expr(left)
        self.fill_expr(right)

        op_name = expr.value

        if left.result_type == "string":
            if op_name not in ("EQUALS_TOKEN", "NOT_EQUALS_TOKEN"):
                raise TypePropagationError(
                    f"You can't use the {op_name} operator on a string"
                )

        is_id = left.result_type_name == "id" or right.result_type_name == "id"
        if not is_id and self.is_wrong_type(
            left.result_type,
            right.result_type,
            left.result_type_name,
            right.result_type_name,
        ):
            raise TypePropagationError(
                f"The left and right operand of a binary expression ('{op_name}') must have the same type, but got {left.result_type_name} and {right.result_type_name}"
            )

        if op_name in ("EQUALS_TOKEN", "NOT_EQUALS_TOKEN"):
            expr.result_type = "bool"
            expr.result_type_name = "bool"
        elif op_name in (
            "GREATER_OR_EQUAL_TOKEN",
            "GREATER_TOKEN",
            "LESS_OR_EQUAL_TOKEN",
            "LESS_TOKEN",
        ):
            if left.result_type not in ("i32", "f32"):
                raise TypePropagationError(f"'{op_name}' operator expects i32 or f32")
            expr.result_type = "bool"
            expr.result_type_name = "bool"
        elif op_name in ("AND_TOKEN", "OR_TOKEN"):
            if left.result_type != "bool":
                raise TypePropagationError(f"'{op_name}' operator expects bool")
            expr.result_type = "bool"
            expr.result_type_name = "bool"
        elif op_name in (
            "PLUS_TOKEN",
            "MINUS_TOKEN",
            "MULTIPLICATION_TOKEN",
            "DIVISION_TOKEN",
        ):
            if left.result_type not in ("i32", "f32"):
                raise TypePropagationError(f"'{op_name}' operator expects i32 or f32")
            expr.result_type = left.result_type
            expr.result_type_name = left.result_type_name
        elif op_name == "REMAINDER_TOKEN":
            if left.result_type != "i32":
                raise TypePropagationError("'%' operator expects i32")
            expr.result_type = "i32"
            expr.result_type_name = "i32"

    def fill_expr(self, expr):
        if expr.type in ("true", "false"):
            expr.result_type = "bool"
            expr.result_type_name = "bool"
        elif expr.type == "string":
            expr.result_type = "string"
            expr.result_type_name = "string"
        elif expr.type in ("resource", "entity"):
            raise TypePropagationError(f"Unexpected {expr.type} expression")
        elif expr.type == "identifier":
            var = self.get_variable(expr.value)
            if not var:
                raise TypePropagationError(
                    f"The variable '{expr.value}' does not exist"
                )
            expr.result_type = var.type
            expr.result_type_name = var.type_name
        elif expr.type == "i32":
            expr.result_type = "i32"
            expr.result_type_name = "i32"
        elif expr.type == "f32":
            expr.result_type = "f32"
            expr.result_type_name = "f32"
        elif expr.type == "unary":
            op = expr.value
            inner = expr.operands[0]

            # Check for double unary
            if inner.type == "unary" and inner.value == op:
                raise TypePropagationError(
                    f"Found '{op}' directly next to another '{op}', which can be simplified by just removing both of them"
                )

            self.fill_expr(inner)
            expr.result_type = inner.result_type
            expr.result_type_name = inner.result_type_name

            if op == "NOT_TOKEN":
                if expr.result_type != "bool":
                    raise TypePropagationError(
                        f"Found 'not' before {expr.result_type_name}, but it can only be put before a bool"
                    )
            elif op == "MINUS_TOKEN":
                if expr.result_type not in ("i32", "f32"):
                    raise TypePropagationError(
                        f"Found '-' before {expr.result_type_name}, but it can only be put before an i32 or f32"
                    )
        elif expr.type in ("binary", "logical"):
            self.fill_binary_expr(expr)
        elif expr.type == "call":
            self.fill_call_expr(expr)
        elif expr.type == "paren":
            self.fill_expr(expr.operands[0])
            expr.result_type = expr.operands[0].result_type
            expr.result_type_name = expr.operands[0].result_type_name

    def fill_variable_statement(self, stmt):
        # Fill the assignment expression first
        self.fill_expr(stmt.assignment_expr)

        var = self.get_variable(stmt.name)

        if stmt.has_type:
            if var:
                raise TypePropagationError(f"The variable '{stmt.name}' already exists")

            if stmt.var_type_name != "id" and self.is_wrong_type(
                stmt.var_type,
                stmt.assignment_expr.result_type,
                stmt.var_type_name,
                stmt.assignment_expr.result_type_name,
            ):
                raise TypePropagationError(
                    f"Can't assign {stmt.assignment_expr.result_type_name} to '{stmt.name}', which has type {stmt.var_type_name}"
                )

            self.add_local_variable(stmt.name, stmt.var_type, stmt.var_type_name)
        else:
            if not var:
                raise TypePropagationError(
                    f"Can't assign to the variable '{stmt.name}', since it does not exist"
                )

            if stmt.name in self.global_variables and var.type == "id":
                raise TypePropagationError("Global id variables can't be reassigned")

            if var.type_name != "id" and self.is_wrong_type(
                var.type,
                stmt.assignment_expr.result_type,
                var.type_name,
                stmt.assignment_expr.result_type_name,
            ):
                raise TypePropagationError(
                    f"Can't assign {stmt.assignment_expr.result_type_name} to '{var.name}', which has type {var.type_name}"
                )

    def mark_local_variables_unreachable(self, statements):
        for stmt in statements:
            if stmt.type == "variable" and stmt.has_type:
                if stmt.name in self.local_variables:
                    del self.local_variables[stmt.name]

    def fill_statements(self, statements):
        for stmt in statements:
            if stmt.type == "variable":
                self.fill_variable_statement(stmt)
            elif stmt.type == "call":
                self.fill_call_expr(stmt.expr)
            elif stmt.type == "if":
                self.fill_expr(stmt.condition)
                self.fill_statements(stmt.if_body)
                if stmt.else_body:
                    self.fill_statements(stmt.else_body)
            elif stmt.type == "return":
                if stmt.has_value:
                    self.fill_expr(stmt.value)

                    if self.fn_return_type == "void":
                        raise TypePropagationError(
                            f"Function '{self.filled_fn_name}' wasn't supposed to return any value"
                        )

                    if self.fn_return_type_name != "id" and self.is_wrong_type(
                        stmt.value.result_type,
                        self.fn_return_type,
                        stmt.value.result_type_name,
                        self.fn_return_type_name,
                    ):
                        raise TypePropagationError(
                            f"Function '{self.filled_fn_name}' is supposed to return {self.fn_return_type_name}, not {stmt.value.result_type_name}"
                        )
                else:
                    if self.fn_return_type != "void":
                        raise TypePropagationError(
                            f"Function '{self.filled_fn_name}' is supposed to return a value of type {self.fn_return_type_name}"
                        )
            elif stmt.type == "while":
                self.fill_expr(stmt.condition)
                self.fill_statements(stmt.body)
                self.parsed_fn_contains_while_loop = True

        self.mark_local_variables_unreachable(statements)

    def add_argument_variables(self, arguments):
        self.local_variables = {}

        for arg in arguments:
            self.add_local_variable(arg["name"], arg["type"], arg["type_name"])

    def fill_helper_fns(self):
        for fn_name, fn in self.parser.helper_fns.items():
            self.fn_return_type = fn.return_type
            self.fn_return_type_name = fn.return_type_name
            self.filled_fn_name = fn_name

            self.add_argument_variables(fn.arguments)

            self.parsed_fn_calls_helper_fn = False
            self.parsed_fn_contains_while_loop = False

            self.fill_statements(fn.body_statements)

            fn.calls_helper_fn = self.parsed_fn_calls_helper_fn
            fn.contains_while_loop = self.parsed_fn_contains_while_loop

            if fn.return_type != "void":
                if not fn.body_statements:
                    raise TypePropagationError(
                        f"Function '{self.filled_fn_name}' is supposed to return {self.fn_return_type_name} as its last line"
                    )

                last_stmt = fn.body_statements[-1]
                if last_stmt.type != "return":
                    raise TypePropagationError(
                        f"Function '{self.filled_fn_name}' is supposed to return {self.fn_return_type_name} as its last line"
                    )

    def fill_on_fns(self):
        # Check for on_fns that aren't declared in the entity
        for fn_name in self.parser.on_fns.keys():
            if fn_name not in self.entity_on_functions:
                raise TypePropagationError(
                    f"The function '{fn_name}' was not declared by entity '{self.file_entity_type}' in mod_api.json"
                )

        # Create a list of parser on_fn names for index lookup
        parser_on_fn_names = list(self.parser.on_fns.keys())

        # Check ordering and validate signatures by iterating through expected order
        previous_on_fn_index = 0
        for expected_fn_name in self.entity_on_functions.keys():
            if expected_fn_name not in self.parser.on_fns:
                continue

            fn = self.parser.on_fns[expected_fn_name]

            # Check ordering
            current_parser_index = parser_on_fn_names.index(expected_fn_name)
            if previous_on_fn_index > current_parser_index:
                raise TypePropagationError(
                    f"The function '{expected_fn_name}' needs to be moved before/after a different on_ function, according to the entity '{self.file_entity_type}' in mod_api.json"
                )
            previous_on_fn_index = current_parser_index

            # Validate signature
            self.fn_return_type = "void"
            self.filled_fn_name = expected_fn_name
            params = self.entity_on_functions[expected_fn_name].get("arguments", [])

            if len(fn.arguments) != len(params):
                if len(fn.arguments) < len(params):
                    raise TypePropagationError(
                        f"Function '{expected_fn_name}' expected the parameter '{params[len(fn.arguments)]["name"]}' with type {params[len(fn.arguments)]["type"]}"
                    )
                else:
                    raise TypePropagationError(
                        f"Function '{expected_fn_name}' got an unexpected extra parameter '{fn.arguments[len(params)]["name"]}' with type {fn.arguments[len(params)]["type_name"]}"
                    )

            for arg, param in zip(fn.arguments, params):
                if arg["name"] != param["name"]:
                    raise TypePropagationError(
                        f"Function '{expected_fn_name}' its '{arg["name"]}' parameter was supposed to be named '{param["name"]}'"
                    )

                if self.is_wrong_type(
                    arg["type"],
                    self.parser.parse_type(param["type"]),
                    arg["type_name"],
                    param["type"],
                ):
                    raise TypePropagationError(
                        f"Function '{expected_fn_name}' its '{param["name"]}' parameter was supposed to have the type {param["type"]}, but got {arg["type_name"]}"
                    )

            self.add_argument_variables(fn.arguments)
            self.parsed_fn_calls_helper_fn = False
            self.parsed_fn_contains_while_loop = False
            self.fill_statements(fn.body_statements)

            fn.calls_helper_fn = self.parsed_fn_calls_helper_fn
            fn.contains_while_loop = self.parsed_fn_contains_while_loop

    def check_global_expr(self, expr, name):
        """Check that global variable expressions don't contain certain calls"""
        if expr.type in ("true", "false", "string", "i32", "f32", "identifier"):
            pass
        elif expr.type in ("resource", "entity"):
            raise TypePropagationError(f"Unexpected {expr.type} in global expression")
        elif expr.type == "unary":
            self.check_global_expr(expr.operands[0], name)
        elif expr.type in ("binary", "logical"):
            self.check_global_expr(expr.operands[0], name)
            self.check_global_expr(expr.operands[1], name)
        elif expr.type == "call":
            if expr.value.startswith("helper_"):
                raise TypePropagationError(
                    f"The global variable '{name}' isn't allowed to call helper functions"
                )
            for arg in expr.operands:
                self.check_global_expr(arg, name)
        elif expr.type == "paren":
            self.check_global_expr(expr.operands[0], name)

    def fill_global_variables(self):
        # Add the implicit 'me' variable
        self.add_global_variable("me", "id", self.file_entity_type)

        # Process global variable statements
        for item in self.parser.global_statements:
            if item["type"] == "global_variable":
                stmt = item["variable"]

                self.check_global_expr(stmt.assignment_expr, stmt.name)
                self.fill_expr(stmt.assignment_expr)

                # Check for assignment to 'me'
                if stmt.assignment_expr.type == "identifier":
                    if stmt.assignment_expr.value == "me":
                        raise TypePropagationError(
                            "Global variables can't be assigned 'me'"
                        )

                if stmt.var_type_name != "id" and self.is_wrong_type(
                    stmt.var_type,
                    stmt.assignment_expr.result_type,
                    stmt.var_type_name,
                    stmt.assignment_expr.result_type_name,
                ):
                    raise TypePropagationError(
                        f"Can't assign {stmt.assignment_expr.result_type_name} to '{stmt.name}', which has type {stmt.var_type_name}"
                    )

                self.add_global_variable(stmt.name, stmt.var_type, stmt.var_type_name)

    def fill_result_types(self):
        """Main entry point for type propagation"""
        self.fill_global_variables()
        self.fill_on_fns()
        self.fill_helper_fns()


class Frontend:
    def __init__(self, mod_api):
        self.mod_api = mod_api

    def compile_grug_fn(self, source: str, mod_name: str, entity_type: str):
        """
        Compile source text and return an error message string,
        or None if compilation succeeded.
        """
        try:
            tokenizer = Tokenizer(source)
            tokens = tokenizer.tokenize()

            parser = Parser(tokens)
            parser.parse()

            type_propagator = TypePropagator(
                parser, mod_name, entity_type, self.mod_api
            )
            type_propagator.fill_result_types()

        except (TokenizerError, ParserError, TypePropagationError) as e:
            return str(e)
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
            return "Unhandled error"

        return None
