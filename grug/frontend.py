from enum import Enum, auto

SPACES_PER_INDENT = 4

# -------------------- Tokenizer --------------------


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
        # Use repr() to escape special characters
        return f"{self.type.name}({repr(self.value)})"


class TokenizerError(Exception):
    pass


class Tokenizer:
    def __init__(self, source: str):
        self.source = source
        self.tokens = []
        self.pos = 0

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
            elif src.startswith("and", i) and not self.is_alnum_underscore(i + 3):
                self.tokens.append(Token(TokenType.AND_TOKEN, "and"))
                i += 3
            elif src.startswith("or", i) and not self.is_alnum_underscore(i + 2):
                self.tokens.append(Token(TokenType.OR_TOKEN, "or"))
                i += 2
            elif src.startswith("not", i) and not self.is_alnum_underscore(i + 3):
                self.tokens.append(Token(TokenType.NOT_TOKEN, "not"))
                i += 3
            elif src.startswith("true", i) and not self.is_alnum_underscore(i + 4):
                self.tokens.append(Token(TokenType.TRUE_TOKEN, "true"))
                i += 4
            elif src.startswith("false", i) and not self.is_alnum_underscore(i + 5):
                self.tokens.append(Token(TokenType.FALSE_TOKEN, "false"))
                i += 5
            elif src.startswith("if", i) and not self.is_alnum_underscore(i + 2):
                self.tokens.append(Token(TokenType.IF_TOKEN, "if"))
                i += 2
            elif src.startswith("else", i) and not self.is_alnum_underscore(i + 4):
                self.tokens.append(Token(TokenType.ELSE_TOKEN, "else"))
                i += 4
            elif src.startswith("while", i) and not self.is_alnum_underscore(i + 5):
                self.tokens.append(Token(TokenType.WHILE_TOKEN, "while"))
                i += 5
            elif src.startswith("break", i) and not self.is_alnum_underscore(i + 5):
                self.tokens.append(Token(TokenType.BREAK_TOKEN, "break"))
                i += 5
            elif src.startswith("return", i) and not self.is_alnum_underscore(i + 6):
                self.tokens.append(Token(TokenType.RETURN_TOKEN, "return"))
                i += 6
            elif src.startswith("continue", i) and not self.is_alnum_underscore(i + 8):
                self.tokens.append(Token(TokenType.CONTINUE_TOKEN, "continue"))
                i += 8
            elif c == " ":
                spaces = 1
                while i + spaces < len(src) and src[i + spaces] == " ":
                    spaces += 1
                if spaces % SPACES_PER_INDENT == 0 and spaces > 1:
                    self.tokens.append(Token(TokenType.INDENTATION_TOKEN, " " * spaces))
                else:
                    self.tokens.append(Token(TokenType.SPACE_TOKEN, " "))
                i += spaces
            elif c == '"':
                i += 1
                start = i
                while i < len(src) and src[i] != '"':
                    i += 1
                if i >= len(src):
                    raise TokenizerError(
                        f"Unclosed string starting at position {start}"
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
                seen_dot = False
                while i < len(src) and (src[i].isdigit() or src[i] == "."):
                    if src[i] == ".":
                        if seen_dot:
                            raise TokenizerError(
                                f"Invalid number with multiple '.' at {i}"
                            )
                        seen_dot = True
                    i += 1
                if seen_dot:
                    self.tokens.append(Token(TokenType.F32_TOKEN, src[start:i]))
                else:
                    self.tokens.append(Token(TokenType.I32_TOKEN, src[start:i]))
            elif c == "#":
                i += 1
                if i >= len(src) or src[i] != " ":
                    raise TokenizerError(f"Expected a space after # at {i}")
                i += 1
                start = i
                while i < len(src) and src[i] not in "\r\n":
                    i += 1
                self.tokens.append(Token(TokenType.COMMENT_TOKEN, src[start:i]))
            else:
                raise TokenizerError(f"Unrecognized character '{c}' at {i}")
        return self.tokens

    def is_alnum_underscore(self, idx):
        return idx < len(self.source) and (
            self.source[idx].isalnum() or self.source[idx] == "_"
        )


# -------------------- Parser --------------------


class ParserError(Exception):
    pass


class Expr:
    def __init__(self, expr_type, value=None, operands=None):
        self.type = expr_type  # e.g., 'call', 'variable', 'literal'
        self.value = value
        self.operands = operands or []


class Statement:
    def __init__(self, stmt_type, **kwargs):
        self.type = stmt_type  # e.g., 'call', 'variable', 'return', 'if', 'while'
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


class OnFn:
    def __init__(self, fn_name):
        self.fn_name = fn_name
        self.arguments = []
        self.argument_count = 0
        self.body_statements = []


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.global_statements = []
        self.helper_fns = []
        self.statements = []
        self.arguments = []
        self.parsing_depth = 0

    def reset_parsing(self):
        self.global_statements = []
        self.parsing_depth = 0
        self.indentation = 0

    def parse(self):
        self.reset_parsing()

        seen_on_fn = False
        seen_newline = False
        newline_allowed = False
        newline_required = False
        just_seen_global = False

        i = 0
        while i < len(self.tokens):
            token = self.tokens[i]
            tname = token.type.name

            # Global variable
            if (
                tname == "WORD_TOKEN"
                and i + 1 < len(self.tokens)
                and self.tokens[i + 1].type.name == "COLON_TOKEN"
            ):
                if seen_on_fn:
                    raise ParserError(
                        f"Move the global variable '{token.value}' so it is above the on_ functions"
                    )
                if newline_required and not just_seen_global:
                    raise ParserError(
                        f"Expected an empty line, on line {self.get_token_line_number(i)}"
                    )

                # Parse global variable
                var_stmt = self.parse_local_variable([i])
                self.global_statements.append(
                    {"type": "global_variable", "variable": var_stmt}
                )

                i += 1  # consume newline
                if i < len(self.tokens) and self.tokens[i].type.name == "NEWLINE_TOKEN":
                    i += 1

                newline_allowed = True
                newline_required = True
                just_seen_global = True
                continue

            # on_ function
            elif (
                tname == "WORD_TOKEN"
                and token.value.startswith("on_")
                and i + 1 < len(self.tokens)
                and self.tokens[i + 1].type.name == "OPEN_PARENTHESIS_TOKEN"
            ):
                if self.helper_fns:
                    raise ParserError(
                        f"{token.value}() must be defined before all helper_ functions"
                    )
                if newline_required:
                    raise ParserError(
                        f"Expected an empty line, on line {self.get_token_line_number(i)}"
                    )

                fn = self.parse_on_fn([i])
                seen_on_fn = True
                newline_allowed = True
                newline_required = True
                just_seen_global = False

                # Already added to global_statements inside parse_on_fn()
                continue

            # helper_ function
            elif (
                tname == "WORD_TOKEN"
                and token.value.startswith("helper_")
                and i + 1 < len(self.tokens)
                and self.tokens[i + 1].type.name == "OPEN_PARENTHESIS_TOKEN"
            ):
                if newline_required:
                    raise ParserError(
                        f"Expected an empty line, on line {self.get_token_line_number(i)}"
                    )

                fn = self.parse_helper_fn([i])
                newline_allowed = True
                newline_required = True
                just_seen_global = False

                # Already added to helper_fns and global_statements inside parse_helper_fn()
                continue

            # Empty line
            elif tname == "NEWLINE_TOKEN":
                if not newline_allowed:
                    raise ParserError(
                        f"Unexpected empty line, on line {self.get_token_line_number(i)}"
                    )
                seen_newline = True
                newline_allowed = False
                newline_required = False
                just_seen_global = False

                self.global_statements.append({"type": "empty_line"})
                i += 1
                continue

            # Comment
            elif tname == "COMMENT_TOKEN":
                newline_allowed = True
                self.global_statements.append(
                    {"type": "comment", "comment": token.value}
                )
                i += 1
                if i < len(self.tokens) and self.tokens[i].type.name == "NEWLINE_TOKEN":
                    i += 1
                continue

            else:
                raise ParserError(
                    f"Unexpected token '{token.value}' on line {self.get_token_line_number(i)}"
                )

        if seen_newline and not newline_allowed:
            raise ParserError(
                f"Unexpected empty line, on line {self.get_token_line_number(len(self.tokens)-1)}"
            )

    # Token helpers
    def peek_token(self, token_index):
        if token_index >= len(self.tokens):
            raise ParserError(
                f"token_index {token_index} was out of bounds in peek_token()"
            )
        return self.tokens[token_index]

    def consume_token(self, i):
        token_index = i[0]
        token = self.peek_token(
            token_index
        )  # uses the new peek_token with bounds check
        i[0] += 1
        return token

    def consume_token_type(self, i, expected_type):
        token_index = i[0]
        token = self.peek_token(token_index)
        if token.type != expected_type:
            raise ParserError(
                f"Expected token type {expected_type.name}, "
                f"but got {token.type.name} on line {self.get_token_line_number(token_index)}"
            )
        i[0] += 1
        return token

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

    def parse_expression(self, i):
        token = self.peek_token(i[0])
        if token.type == TokenType.I32_TOKEN:
            i[0] += 1
            return Expr("literal", int(token.value))
        elif token.type == TokenType.F32_TOKEN:
            i[0] += 1
            return Expr("literal", float(token.value))
        elif token.type == TokenType.WORD_TOKEN:
            # Variable or function call
            next_tok = self.peek_token(i[0] + 1)
            if next_tok and next_tok.type == TokenType.OPEN_PARENTHESIS_TOKEN:
                return self.parse_call(i)
            else:
                i[0] += 1
                return Expr("variable", token.value)
        else:
            raise ParserError(
                f"Unexpected token in expression '{token.value}' at line {self.get_token_line_number(i[0])}"
            )

    def parse_statement(self, i):
        token = self.peek_token(i[0])
        if token.type == TokenType.WORD_TOKEN:
            next_tok = self.peek_token(i[0] + 1)
            if next_tok.type == TokenType.OPEN_PARENTHESIS_TOKEN:
                expr = self.parse_call(i)
                return Statement("call", expr=expr)
            elif (
                next_tok.type == TokenType.COLON_TOKEN
                or next_tok.type == TokenType.SPACE_TOKEN
            ):
                # local variable
                return self.parse_local_variable(i)
            else:
                raise ParserError(
                    f"Expected '(', ':' or '=' after word '{token.value}' at line {self.get_token_line_number(i[0])}"
                )
        elif token.type == TokenType.IF_TOKEN:
            i[0] += 1
            return self.parse_if_statement(i)
        elif token.type == TokenType.RETURN_TOKEN:
            i[0] += 1
            tok_next = self.peek_token(i[0])
            if tok_next.type == TokenType.NEWLINE_TOKEN:
                i[0] += 1
                return Statement("return", has_value=False)
            else:
                expr = self.parse_expression(i)
                return Statement("return", has_value=True, value=expr)
        elif token.type == TokenType.WHILE_TOKEN:
            i[0] += 1
            return self.parse_while_statement(i)
        elif token.type == TokenType.BREAK_TOKEN:
            i[0] += 1
            return Statement("break")
        elif token.type == TokenType.CONTINUE_TOKEN:
            i[0] += 1
            return Statement("continue")
        elif token.type == TokenType.NEWLINE_TOKEN:
            i[0] += 1
            return Statement("empty_line")
        elif token.type == TokenType.COMMENT_TOKEN:
            i[0] += 1
            return Statement("comment", comment=token.value)
        else:
            raise ParserError(
                f"Unexpected token '{token.value}' at line {self.get_token_line_number(i[0])}"
            )

    def push_argument(self, argument):
        self.arguments.append(argument)
        return argument

    def parse_arguments(self, i):
        args = []
        arg_token = self.consume_token(i)
        self.consume_token_type(i, TokenType.COLON_TOKEN)
        type_token = self.consume_token(i)
        arg = Argument(arg_token.value, type_token.value, type_token.value)
        args.append(self.push_argument(arg))

        while True:
            tok = self.peek_token(i[0])
            if tok.type != TokenType.COMMA_TOKEN:
                break
            i[0] += 1
            arg_token = self.consume_token(i)
            self.consume_token_type(i, TokenType.COLON_TOKEN)
            type_token = self.consume_token(i)
            arg = Argument(arg_token.value, type_token.value, type_token.value)
            args.append(self.push_argument(arg))
        return args

    def parse_helper_fn(self, i):
        fn_token = self.consume_token(i)
        fn = HelperFn(fn_token.value)

        # Ensure the helper was called before defining it
        if not self.seen_called_helper_fn_name(fn.fn_name):
            raise ParserError(
                f"{fn.fn_name}() is defined before the first time it gets called"
            )

        # Arguments
        self.consume_token_type(i, TokenType.OPEN_PARENTHESIS_TOKEN)
        next_tok = self.peek_token(i[0])
        if next_tok.type == TokenType.WORD_TOKEN:
            fn.arguments = self.parse_arguments(i)
            fn.argument_count = len(fn.arguments)
        self.consume_token_type(i, TokenType.CLOSE_PARENTHESIS_TOKEN)

        # Optional return type
        tok_space = self.peek_token(i[0])
        fn.return_type = "void"
        if tok_space and tok_space.type == TokenType.SPACE_TOKEN:
            i[0] += 1
            tok_ret = self.peek_token(i[0])
            if tok_ret.type == TokenType.WORD_TOKEN:
                type_token = self.consume_token(i)
                fn.return_type = type_token.value
                fn.return_type_name = type_token.value

        # Body statements
        fn.body_statements = self.parse_statements(i)
        if all(s.type in ("empty_line", "comment") for s in fn.body_statements):
            raise ParserError(f"{fn.fn_name}() can't be empty")

        # Store function
        self.helper_fns.append(fn)
        self.global_statements.append({"type": "helper_fn", "helper_fn": fn})
        return fn

    def parse_on_fn(self, i):
        fn_token = self.consume_token(i)
        fn = OnFn(fn_token.value)

        # Arguments
        self.consume_token_type(i, TokenType.OPEN_PARENTHESIS_TOKEN)
        next_tok = self.peek_token(i[0])
        if next_tok.type == TokenType.WORD_TOKEN:
            fn.arguments = self.parse_arguments(i)
            fn.argument_count = len(fn.arguments)
        self.consume_token_type(i, TokenType.CLOSE_PARENTHESIS_TOKEN)

        # Body statements
        fn.body_statements = self.parse_statements(i)
        if all(s.type in ("empty_line", "comment") for s in fn.body_statements):
            raise ParserError(f"{fn.fn_name}() can't be empty")

        # Store function
        self.global_statements.append({"type": "on_fn", "on_fn": fn})
        return fn

    def parse_statements(self, i):
        stmts = []

        self.increase_parsing_depth()
        self.consume_space(i)
        self.consume_token_type(i, TokenType.OPEN_BRACE_TOKEN)

        # Consume first newline after opening brace
        if self.peek_token(i[0]).type == TokenType.NEWLINE_TOKEN:
            i[0] += 1

        body_statement_count = 0
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
                body_statement_count += 1
            else:
                newline_allowed = True

                # Consume indentation
                self.consume_indentation(i)

                # Parse statement
                stmt = self.parse_statement(i)
                stmts.append(stmt)
                body_statement_count += 1

                # Consume newline after statement
                if self.peek_token(i[0]).type == TokenType.NEWLINE_TOKEN:
                    i[0] += 1

        if seen_newline and not newline_allowed:
            raise ParserError(
                f"Unexpected empty line, on line {self.get_token_line_number(i[0]-1)}"
            )

        self.indentation -= 1

        # Consume closing brace
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
        tok = self.peek_token(i[0])
        if tok.type != TokenType.INDENTATION_TOKEN:
            raise ParserError(
                f"Expected indentation on line {self.get_token_line_number(i[0])}, got '{tok.value}'"
            )
        spaces = len(tok.value)
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
        MAX_PARSING_DEPTH = 100
        if self.parsing_depth >= MAX_PARSING_DEPTH:
            raise ParserError(f"Exceeded maximum parsing depth of {MAX_PARSING_DEPTH}")

    def decrease_parsing_depth(self):
        if self.parsing_depth <= 0:
            raise ParserError("Parsing depth underflow")
        self.parsing_depth -= 1

    def parse_local_variable(self, i):
        """
        Parse a local variable declaration with optional type and required assignment.
        Example: x: i32 = 42
        """
        name_token_index = i[0]
        var_token = self.consume_token(i)
        var_name = var_token.value

        has_type = False
        var_type = None
        var_type_name = None

        # Optional type after colon
        if self.peek_token(i[0]).type == TokenType.COLON_TOKEN:
            i[0] += 1

            if var_name == "me":
                raise ParserError(
                    "The local variable 'me' has to be renamed, since it is already declared"
                )

            self.consume_space(i)
            type_token = self.consume_token(i)
            if type_token.type != TokenType.WORD_TOKEN:
                raise ParserError(
                    f"Expected a word token after the colon on line {self.get_token_line_number(name_token_index)}"
                )

            has_type = True
            var_type = (
                type_token.value
            )  # You could convert this via parse_type if needed
            var_type_name = type_token.value

            if var_type in ("resource", "entity"):
                raise ParserError(
                    f"The variable '{var_name}' can't have '{var_type}' as its type"
                )

        # Ensure a space exists before assignment
        if self.peek_token(i[0]).type != TokenType.SPACE_TOKEN:
            raise ParserError(
                f"The variable '{var_name}' was not assigned a value on line {self.get_token_line_number(name_token_index)}"
            )

        self.consume_space(i)

        # Expect assignment token
        self.consume_token_type(i, TokenType.ASSIGNMENT_TOKEN)

        if var_name == "me":
            raise ParserError(
                "Assigning a new value to the entity's 'me' variable is not allowed"
            )

        self.consume_space(i)

        # Parse assignment expression
        assignment_expr = self.parse_expression(i)

        return Statement(
            "variable",
            name=var_name,
            has_type=has_type,
            var_type=var_type,
            var_type_name=var_type_name,
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
        if self.parsing_depth > 100:
            raise ParserError("Exceeded maximum parsing depth of 100")

        expr = self.parse_primary(i)

        token = self.peek_token(i[0])
        if token is None or token.type != TokenType.OPEN_PARENTHESIS_TOKEN:
            self.decrease_parsing_depth()
            return expr

        # Must be an identifier to call
        if expr.type != "identifier":
            raise ParserError(
                f"Unexpected '(' after non-identifier at line {self.get_token_line_number(i[0])}"
            )

        fn_name = expr.value
        if fn_name.startswith("helper_"):
            self.add_called_helper_fn_name(fn_name)

        i[0] += 1  # consume '('
        args = []

        while True:
            token = self.peek_token(i[0])
            if token.type == TokenType.CLOSE_PARENTHESIS_TOKEN:
                i[0] += 1
                break
            arg = self.parse_expression(i)
            args.append(arg)
            token = self.peek_token(i[0])
            if token.type == TokenType.COMMA_TOKEN:
                i[0] += 1  # consume comma
                self.consume_space(i)
            elif token.type != TokenType.CLOSE_PARENTHESIS_TOKEN:
                raise ParserError(
                    f"Expected ',' or ')' in argument list at line {self.get_token_line_number(i[0])}"
                )

        expr.type = "call"
        expr.value = fn_name
        expr.operands = args

        self.decrease_parsing_depth()
        return expr

    def parse_primary(self, i):
        self.increase_parsing_depth()
        if self.parsing_depth > 100:
            raise ParserError("Exceeded maximum parsing depth of 100")

        token = self.peek_token(i[0])
        expr = Expr(None)

        tname = token.type.name
        if tname == "OPEN_PARENTHESIS_TOKEN":
            i[0] += 1
            inner = self.parse_expression(i)
            self.consume_token_type(i, TokenType.CLOSE_PARENTHESIS_TOKEN)
            expr.type = "paren"
            expr.operands = [inner]
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
            expr.value = int(token.value)
        elif tname == "F32_TOKEN":
            i[0] += 1
            expr.type = "f32"
            expr.value = float(token.value)
        else:
            raise ParserError(
                f"Expected a primary expression token, but got {tname} at line {self.get_token_line_number(i[0])}"
            )

        self.decrease_parsing_depth()
        return expr

    def parse_factor(self, i):
        expr = self.parse_unary(i)
        while True:
            tok1 = self.peek_token(i[0])
            tok2 = self.peek_token(i[0] + 1)
            if (
                tok1
                and tok1.type == TokenType.SPACE_TOKEN
                and tok2
                and tok2.type
                in (
                    TokenType.MULTIPLICATION_TOKEN,
                    TokenType.DIVISION_TOKEN,
                    TokenType.REMAINDER_TOKEN,
                )
            ):
                i[0] += 1  # skip space
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
            tok2 = self.peek_token(i[0] + 1)
            if (
                tok1
                and tok1.type == TokenType.SPACE_TOKEN
                and tok2
                and tok2.type
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
            tok2 = self.peek_token(i[0] + 1)
            if (
                tok1
                and tok1.type == TokenType.SPACE_TOKEN
                and tok2
                and tok2.type
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
            tok2 = self.peek_token(i[0] + 1)
            if (
                tok1
                and tok1.type == TokenType.SPACE_TOKEN
                and tok2
                and tok2.type
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
            tok2 = self.peek_token(i[0] + 1)
            if (
                tok1
                and tok1.type == TokenType.SPACE_TOKEN
                and tok2
                and tok2.type == TokenType.AND_TOKEN
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
            tok2 = self.peek_token(i[0] + 1)
            if (
                tok1
                and tok1.type == TokenType.SPACE_TOKEN
                and tok2
                and tok2.type == TokenType.OR_TOKEN
            ):
                i[0] += 1
                op_token = self.consume_token(i)
                self.consume_space(i)
                right = self.parse_and(i)
                expr = Expr("logical", "OR", [expr, right])
            else:
                break
        return expr

    def parse_full_expression(self, i):
        """
        Entry point for parsing an expression, mirrors C parse_expression().
        """
        self.increase_parsing_depth()
        expr = self.parse_or(i)
        self.decrease_parsing_depth()
        return expr

    def parse_if_statement(self, i):
        """
        Parse an if statement, including optional else and else-if chains.
        """
        self.increase_parsing_depth()
        self.consume_space(i)
        condition = self.parse_full_expression(i)
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
                    i[0] += 2  # skip SPACE + IF
                    else_body = [self.parse_if_statement(i)]
                else:
                    self.consume_space(i)
                    else_body = self.parse_statements(i)

        self.decrease_parsing_depth()
        return Statement(
            "if", condition=condition, if_body=if_body, else_body=else_body
        )

    def parse_while_statement(self, i):
        """
        Parse a while statement, respecting spaces before the condition.
        """
        self.increase_parsing_depth()
        self.consume_space(i)
        condition = self.parse_full_expression(i)
        body = self.parse_statements(i)
        self.decrease_parsing_depth()
        return Statement("while", condition=condition, body=body)


class Frontend:
    def compile_grug_fn(self, source: str):
        """
        Compile source text and return an error message string,
        or None if compilation succeeded.
        """
        try:
            tokenizer = Tokenizer(source)
            tokens = tokenizer.tokenize()

            parser = Parser(tokens)
            parser.parse()

        except (TokenizerError, ParserError) as e:
            return str(e)

        return None
