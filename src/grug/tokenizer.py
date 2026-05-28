from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import List, Tuple

from .error import GrugError, SourceSpan

SPACES_PER_INDENT = 4


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
    EXPORT_TOKEN = auto()
    LOCAL_TOKEN = auto()
    SPACE_TOKEN = auto()
    INDENTATION_TOKEN = auto()
    STRING_TOKEN = auto()
    ENTITY_TOKEN = auto()
    RESOURCE_TOKEN = auto()
    WORD_TOKEN = auto()
    NUMBER_TOKEN = auto()
    COMMENT_TOKEN = auto()

    def __str__(self) -> str:
        return {
            TokenType.OPEN_PARENTHESIS_TOKEN: "'('",
            TokenType.CLOSE_PARENTHESIS_TOKEN: "')'",
            TokenType.OPEN_BRACE_TOKEN: "'{'",
            TokenType.CLOSE_BRACE_TOKEN: "'}'",
            TokenType.PLUS_TOKEN: "'+'",
            TokenType.MINUS_TOKEN: "'-'",
            TokenType.MULTIPLICATION_TOKEN: "'*'",
            TokenType.DIVISION_TOKEN: "'/'",
            TokenType.COMMA_TOKEN: "','",
            TokenType.COLON_TOKEN: "':'",
            TokenType.NEWLINE_TOKEN: "line break ('\\n')",
            TokenType.EQUALS_TOKEN: "'=='",
            TokenType.NOT_EQUALS_TOKEN: "'!='",
            TokenType.ASSIGNMENT_TOKEN: "'='",
            TokenType.GREATER_OR_EQUAL_TOKEN: "'>='",
            TokenType.GREATER_TOKEN: "'>'",
            TokenType.LESS_OR_EQUAL_TOKEN: "'<='",
            TokenType.LESS_TOKEN: "'<'",
            TokenType.AND_TOKEN: "'and'",
            TokenType.OR_TOKEN: "'or'",
            TokenType.NOT_TOKEN: "'not'",
            TokenType.TRUE_TOKEN: "'true'",
            TokenType.FALSE_TOKEN: "'false'",
            TokenType.IF_TOKEN: "'if'",
            TokenType.ELSE_TOKEN: "'else'",
            TokenType.WHILE_TOKEN: "'while'",
            TokenType.BREAK_TOKEN: "'break'",
            TokenType.RETURN_TOKEN: "'return'",
            TokenType.CONTINUE_TOKEN: "'continue'",
            TokenType.EXPORT_TOKEN: "'export'",
            TokenType.LOCAL_TOKEN: "'local'",
            TokenType.SPACE_TOKEN: "space (' ')",
            TokenType.INDENTATION_TOKEN: "indentation",
            TokenType.STRING_TOKEN: "string",
            TokenType.ENTITY_TOKEN: "entity string",
            TokenType.RESOURCE_TOKEN: "resource string",
            TokenType.WORD_TOKEN: "word",
            TokenType.NUMBER_TOKEN: "number",
            TokenType.COMMENT_TOKEN: "comment",
        }.get(self, self.name)


@dataclass
class Token:
    type: TokenType
    value: str
    span: SourceSpan


class Tokenizer:
    def __init__(self, src: str, file_path: Path):
        self.src = src
        self.file_path = file_path

    def new_error(self, err_span: SourceSpan, error_message: str) -> GrugError:
        return GrugError.new_tokenizer_error(
            self.file_path, self.src, err_span, error_message
        )

    def tokenize(self):
        tokens: List[Token] = []
        src = self.src
        i = 0
        current_line = 1

        def current_span(start: int) -> SourceSpan:
            return SourceSpan(current_line, start)

        def add_token(token_type: TokenType, value: str, start: int) -> None:
            tokens.append(Token(token_type, value, current_span(start)))

        while i < len(src):
            c = src[i]
            if c == "(":
                add_token(TokenType.OPEN_PARENTHESIS_TOKEN, c, i)
                i += 1
            elif c == ")":
                add_token(TokenType.CLOSE_PARENTHESIS_TOKEN, c, i)
                i += 1
            elif c == "{":
                add_token(TokenType.OPEN_BRACE_TOKEN, c, i)
                i += 1
            elif c == "}":
                add_token(TokenType.CLOSE_BRACE_TOKEN, c, i)
                i += 1
            elif c == "+":
                add_token(TokenType.PLUS_TOKEN, c, i)
                i += 1
            elif c == "-":
                add_token(TokenType.MINUS_TOKEN, c, i)
                i += 1
            elif c == "*":
                add_token(TokenType.MULTIPLICATION_TOKEN, c, i)
                i += 1
            elif c == "/":
                add_token(TokenType.DIVISION_TOKEN, c, i)
                i += 1
            elif c == ",":
                add_token(TokenType.COMMA_TOKEN, c, i)
                i += 1
            elif c == ":":
                add_token(TokenType.COLON_TOKEN, c, i)
                i += 1
            # Hard to hit this branch when running on windows because "\r\n"
            # is replaced with "\n" when reading the file
            elif src.startswith("\r\n", i): # pragma: no cover
                add_token(TokenType.NEWLINE_TOKEN, "\r\n", i)
                current_line += 1
                i += 2
            elif c == "\n":
                add_token(TokenType.NEWLINE_TOKEN, c, i)
                current_line += 1
                i += 1
            elif c == "=" and i + 1 < len(src) and src[i + 1] == "=":
                add_token(TokenType.EQUALS_TOKEN, "==", i)
                i += 2
            elif c == "!" and i + 1 < len(src) and src[i + 1] == "=":
                add_token(TokenType.NOT_EQUALS_TOKEN, "!=", i)
                i += 2
            elif c == "=":
                add_token(TokenType.ASSIGNMENT_TOKEN, c, i)
                i += 1
            elif c == ">" and i + 1 < len(src) and src[i + 1] == "=":
                add_token(TokenType.GREATER_OR_EQUAL_TOKEN, ">=", i)
                i += 2
            elif c == ">":
                add_token(TokenType.GREATER_TOKEN, ">", i)
                i += 1
            elif c == "<" and i + 1 < len(src) and src[i + 1] == "=":
                add_token(TokenType.LESS_OR_EQUAL_TOKEN, "<=", i)
                i += 2
            elif c == "<":
                add_token(TokenType.LESS_TOKEN, "<", i)
                i += 1
            elif src.startswith("and", i) and self.is_end_of_word(i + 3):
                add_token(TokenType.AND_TOKEN, "and", i)
                i += 3
            elif src.startswith("or", i) and self.is_end_of_word(i + 2):
                add_token(TokenType.OR_TOKEN, "or", i)
                i += 2
            elif src.startswith("not", i) and self.is_end_of_word(i + 3):
                add_token(TokenType.NOT_TOKEN, "not", i)
                i += 3
            elif src.startswith("true", i) and self.is_end_of_word(i + 4):
                add_token(TokenType.TRUE_TOKEN, "true", i)
                i += 4
            elif src.startswith("false", i) and self.is_end_of_word(i + 5):
                add_token(TokenType.FALSE_TOKEN, "false", i)
                i += 5
            elif src.startswith("if", i) and self.is_end_of_word(i + 2):
                add_token(TokenType.IF_TOKEN, "if", i)
                i += 2
            elif src.startswith("else", i) and self.is_end_of_word(i + 4):
                add_token(TokenType.ELSE_TOKEN, "else", i)
                i += 4
            elif src.startswith("while", i) and self.is_end_of_word(i + 5):
                add_token(TokenType.WHILE_TOKEN, "while", i)
                i += 5
            elif src.startswith("break", i) and self.is_end_of_word(i + 5):
                add_token(TokenType.BREAK_TOKEN, "break", i)
                i += 5
            elif src.startswith("return", i) and self.is_end_of_word(i + 6):
                add_token(TokenType.RETURN_TOKEN, "return", i)
                i += 6
            elif src.startswith("continue", i) and self.is_end_of_word(i + 8):
                add_token(TokenType.CONTINUE_TOKEN, "continue", i)
                i += 8
            elif src.startswith("export", i) and self.is_end_of_word(i + 6):
                add_token(TokenType.EXPORT_TOKEN, "export", i)
                i += 6
            elif src.startswith("local", i) and self.is_end_of_word(i + 5):
                add_token(TokenType.LOCAL_TOKEN, "local", i)
                i += 5
            # spaces and indentation
            elif c == " ":
                if i + 1 >= len(src) or src[i + 1] != " ":
                    add_token(TokenType.SPACE_TOKEN, " ", i)
                    i += 1
                    continue

                old_i = i
                while i < len(src) and src[i] == " ":
                    i += 1

                spaces = i - old_i

                if spaces % SPACES_PER_INDENT != 0:
                    raise self.new_error(
                        current_span(old_i),
                        f"Expected multiple of {SPACES_PER_INDENT} spaces but found {spaces} spaces",
                    )

                add_token(TokenType.INDENTATION_TOKEN, " " * spaces, old_i)
            # Strings
            elif c == '"':
                token_span = current_span(i)
                string, i, current_line = self.tokenize_string(i, current_line)
                tokens.append(Token(TokenType.STRING_TOKEN, string, token_span))
                i += 1
            # Entity strings
            elif c == "e" and i + 1 < len(src) and src[i + 1] == '"':
                token_span = current_span(i)
                i += 1
                string, i, current_line = self.tokenize_string(i, current_line)
                tokens.append(Token(TokenType.ENTITY_TOKEN, string, token_span))
                i += 1
            # Resource strings
            elif c == "r" and i + 1 < len(src) and src[i + 1] == '"':
                token_span = current_span(i)
                i += 1
                string, i, current_line = self.tokenize_string(i, current_line)
                tokens.append(Token(TokenType.RESOURCE_TOKEN, string, token_span))
                i += 1
            # words
            elif c.isalpha() or c == "_":
                start = i
                while i < len(src) and (src[i].isalnum() or src[i] == "_"):
                    i += 1
                add_token(TokenType.WORD_TOKEN, src[start:i], start)
            # numbers
            elif c.isdigit():
                start = i
                seen_period = False
                i += 1
                while i < len(src) and (src[i].isdigit() or src[i] == "."):
                    if src[i] == ".":
                        if seen_period:
                            raise self.new_error(
                                current_span(i),
                                f"Encountered two '.' periods in a number on line {self.get_character_line_number(i)}",
                            )
                        seen_period = True
                    i += 1

                if src[i - 1] == ".":
                    raise self.new_error(
                        current_span(i),
                        f"Missing digit after decimal point in '{src[start:i]}'",
                    )

                add_token(TokenType.NUMBER_TOKEN, src[start:i], start)
            # comments
            elif c == "#":
                token_start = i
                i += 1
                if i >= len(src) or src[i] != " ":
                    raise self.new_error(
                        current_span(i),
                        "Expected space (' ') after '#'",
                    )
                i += 1
                start = i
                while i < len(src) and src[i] != "\n":
                    if src[i] == "\0":
                        raise self.new_error(
                            current_span(i),
                            f"Unexpected null byte on line {self.get_character_line_number(i)}",
                        )
                    i += 1

                comment_len = i - start
                if comment_len == 0:
                    raise self.new_error(
                        current_span(i - 1),
                        f"Expected comment to contain some text",
                    )

                if src[i - 1].isspace():
                    raise self.new_error(
                        current_span(i),
                        f"A comment has trailing whitespace on line {self.get_character_line_number(i)}",
                    )

                add_token(TokenType.COMMENT_TOKEN, src[start:i], token_start)
            else:
                raise self.new_error(
                    current_span(i),
                    f"Unrecognized character '{c}'",
                )

        return tokens

    def get_character_line_number(self, idx: int) -> int:
        """
        Calculate the line number for a given character index.
        Line numbers are 1-based.
        """
        return self.src[:idx].count("\n") + 1

    def is_end_of_word(self, idx: int):
        """Check if position is at end of word (not alphanumeric or underscore)"""
        return idx >= len(self.src) or not (
            self.src[idx].isalnum() or self.src[idx] == "_"
        )

    def tokenize_string(self, i: int, current_line: int) -> Tuple[str, int, int]:
        src = self.src
        open_quote_index = i
        open_quote_line = current_line
        i += 1
        start = i
        while i < len(src) and src[i] != '"':
            if src[i] == "\n": 
                current_line += 1;
            elif src[i] == "\0":
                raise self.new_error(
                    SourceSpan(current_line, i),
                    f"Unexpected null byte on line {self.get_character_line_number(i)}",
                )
            elif src[i] == "\\" and i + 1 < len(src) and src[i + 1] == "\n":
                raise self.new_error(
                    SourceSpan(current_line, i),
                    f"Unexpected line break in string on line {self.get_character_line_number(i)}",
                )
            i += 1
        if i >= len(src):
            raise self.new_error(
                SourceSpan(open_quote_line, open_quote_index),
                f'Unclosed " on line {self.get_character_line_number(open_quote_index)}',
            )
        return src[start:i], i, current_line
