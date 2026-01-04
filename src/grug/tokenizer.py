from dataclasses import dataclass
from enum import Enum, auto
from typing import List

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
