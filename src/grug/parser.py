from __future__ import annotations

import math
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

from .error import GrugError, SourceSpan
from .tokenizer import SPACES_PER_INDENT, Token, TokenType
from .types import EntityStrType, HostFn, IdType, PrimitiveType, ResourceStrType, Type

MAX_PARSING_DEPTH = 100

MIN_F64 = struct.unpack("!d", struct.pack("!Q", 0x0010000000000000))[0]
MAX_F64 = struct.unpack("!d", struct.pack("!Q", 0x7FEFFFFFFFFFFFFF))[0]


@dataclass
class ParserError(Exception):
    span: SourceSpan
    message: strgit status
On branch main
Your branch and 'myfork/main' have diverged,
and have 23 and 19 different commits each, respectively.
  (use "git pull" if you want to integrate the remote branch with yours)

You have unmerged paths.
  (fix conflicts and run "git commit")
  (use "git merge --abort" to abort the merge)

Changes to be committed:
	modified:   .gitignore
	modified:   .vscode/launch.json
	deleted:    .vscode/settings.json
	modified:   README.md
	new file:   benchmarks.py
	new file:   examples/class/example.py
	new file:   examples/class/mod_api.json
	new file:   examples/class/mods/animals/labrador-Dog.grug
	modified:   examples/custom_package_prefixes/example.py
	modified:   examples/custom_package_prefixes/mod_api.json
	modified:   examples/custom_package_prefixes/mods/animals/labrador-Dog.grug
	modified:   examples/dict/example.py
	modified:   examples/dict/mod_api.json
	modified:   examples/dict/mods/animals/labrador-Dog.grug
	new file:   examples/dir_entry_not_found/example.py
	new file:   examples/dir_entry_not_found/mod_api.json
	new file:   examples/dir_entry_not_found/mods/animals/labrador-Dog.grug
	new file:   examples/dirs_cant_create_entity/example.py
	new file:   examples/dirs_cant_create_entity/mod_api.json
	new file:   examples/dirs_cant_create_entity/mods/animals/labrador-Dog.grug
	new file:   examples/entity/example.py
	new file:   examples/entity/mod_api.json
	new file:   examples/entity/mods/animals/labrador-Dog.grug
	modified:   examples/export_fn_not_defined/example.py
	modified:   examples/export_fn_not_defined/mod_api.json
	modified:   examples/export_fn_not_defined/mods/animals/labrador-Dog.grug
	modified:   examples/fib_memoized/example.py
	modified:   examples/fib_memoized/mod_api.json
	modified:   examples/fib_memoized/mods/animals/labrador-Dog.grug
	modified:   examples/fib_naive/example.py
	modified:   examples/fib_naive/mod_api.json
	modified:   examples/fib_naive/mods/animals/labrador-Dog.grug
	new file:   examples/files_are_not_indexable/example.py
	new file:   examples/files_are_not_indexable/mod_api.json
	new file:   examples/files_are_not_indexable/mods/animals/labrador-Dog.grug
	modified:   examples/global_list/example.py
	modified:   examples/global_list/mod_api.json
	modified:   examples/global_list/mods/animals/labrador-Dog.grug
	modified:   examples/host_fn_error/example.py
	modified:   examples/host_fn_error/mod_api.json
	modified:   examples/host_fn_error/mods/animals/labrador-Dog.grug
	new file:   examples/host_fn_error_in_method/example.py
	new file:   examples/host_fn_error_in_method/mod_api.json
	new file:   examples/host_fn_error_in_method/mods/animals/labrador-Dog.grug
	modified:   examples/host_fn_error_registered_twice/mod_api.json
	modified:   examples/host_fn_error_registered_twice/mods/animals/labrador-Dog.grug
	new file:   examples/host_fn_registration_error/example.py
	new file:   examples/host_fn_registration_error/mod_api.json
	new file:   examples/host_fn_registration_error/mods/animals/labrador-Dog.grug
	modified:   examples/list/example.py
	modified:   examples/list/mod_api.json
	modified:   examples/list/mods/animals/labrador-Dog.grug
	modified:   examples/minimal/example.py
	modified:   examples/minimal/mod_api.json
	modified:   examples/minimal/mods/animals/labrador-Dog.grug
	new file:   examples/mod_subdirectory/example.py
	new file:   examples/mod_subdirectory/mod_api.json
	new file:   examples/mod_subdirectory/mods/animals/dogs/labrador-Dog.grug
	new file:   examples/resource/example.py
	new file:   examples/resource/mod_api.json
	new file:   examples/resource/mods/animals/foo.txt
	new file:   examples/resource/mods/animals/labrador-Dog.grug
	new file:   examples/static_method/example.py
	new file:   examples/static_method/mod_api.json
	new file:   examples/static_method/mods/animals/labrador-Dog.grug
	new file:   examples/static_method_from_package/example.py
	new file:   examples/static_method_from_package/mod_api.json
	new file:   examples/static_method_from_package/mods/animals/labrador-Dog.grug
	modified:   examples/using_grug_packages/example.py
	modified:   examples/using_grug_packages/mod_api.json
	modified:   examples/using_grug_packages/mods/animals/labrador-Dog.grug
	deleted:    fuzz.py
	modified:   pyproject.toml
	modified:   src/grug/__init__.py
	modified:   src/grug/entity.py
	new file:   src/grug/error.py
	deleted:    src/grug/grug_value.py
	new file:   src/grug/mod_api.py
	modified:   src/grug/packages/grug_numpy/grug_numpy.py
	modified:   src/grug/packages/grug_numpy/tests/mod_api.json
	modified:   src/grug/packages/grug_numpy/tests/mods/misc/exp-Test.grug
	modified:   src/grug/packages/grug_stdlib/grug_stdlib.py
	modified:   src/grug/packages/grug_stdlib/tests/mod_api.json
	new file:   src/grug/packages/grug_stdlib/tests/mods/assert/assert-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/assert/assert_bool-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/assert/assert_id-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/assert/assert_number-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/assert/assert_string-Test.grug
	deleted:    src/grug/packages/grug_stdlib/tests/mods/casting/id_to_dict-Test.grug
	deleted:    src/grug/packages/grug_stdlib/tests/mods/casting/id_to_list-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/dict/dict-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/dict/dict_bool_bool_set-Test.grug
	new file:   src/grug/packages/grug_stdlib/tests/mods/dict/dict_from_keys-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/dict/dict_number_id_set-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/dict/dict_number_number_get-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/dict/dict_number_number_get_error_key_not_in_dict-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/dict/dict_number_number_set-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/dict/dict_string_string_set-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/list/list-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/list/list_bool_append-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/list/list_id_append-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/list/list_string_append-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/list/number/list_number_append-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/list/number/list_number_clear-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/list/number/list_number_copy-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/list/number/list_number_count-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/list/number/list_number_extend-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/list/number/list_number_has-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/list/number/list_number_index-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/list/number/list_number_insert-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/list/number/list_number_len-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/list/number/list_number_pop-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/list/number/list_number_pop_index-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/list/number/list_number_remove-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/list/number/list_number_reverse-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/list/number/list_number_sort-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/math/ceil-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/math/sqrt-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/print/print_bool-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/print/print_dict-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/print/print_id-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/print/print_list-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/print/print_number-Test.grug
	modified:   src/grug/packages/grug_stdlib/tests/mods/print/print_string-Test.grug
	modified:   src/grug/serializer.py
	new file:   src/grug/types.py
	modified:   tests.py
	new file:   tests/__init__.py
	modified:   tests/conftest.py

Unmerged paths:
  (use "git add <file>..." to mark resolution)
	both modified:   .github/workflows/build.yml
	both modified:   src/grug/grug_state.py
	both modified:   src/grug/parser.py
	both modified:   src/grug/tokenizer.py
	both modified:   src/grug/type_propagator.py
	both modified:   tests/test_grug.py

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	bin/
	error.md
	error1.md
	error2.md
	error3.md
	graphify-out/
	lib/
	lib64
	pyvenv.cfg
	tmux-client-34853.log



@dataclass
class TrueExpr:
    expr_span: SourceSpan
    result: Type = field(default_factory=lambda: PrimitiveType.BOOL)


@dataclass
class FalseExpr:
    expr_span: SourceSpan
    result: Type = field(default_factory=lambda: PrimitiveType.BOOL)


@dataclass
class StringExpr:
    string: str
    expr_span: SourceSpan
    result: Type = field(default_factory=lambda: PrimitiveType.STRING)


@dataclass
class ResourceExpr:
    string: str
    expr_span: SourceSpan
    result: Type = field(default_factory=lambda: ResourceStrType(extension=""))


@dataclass
class EntityExpr:
    string: str
    expr_span: SourceSpan
    result: Type = field(default_factory=lambda: EntityStrType(entity_type=None))


@dataclass
class IdentifierExpr:
    name: str
    expr_span: SourceSpan
    result: Type = field(default_factory=lambda: PrimitiveType.VOID)


@dataclass
class NumberExpr:
    value: float
    string: str
    expr_span: SourceSpan
    result: Type = field(default_factory=lambda: PrimitiveType.NUMBER)


@dataclass
class UnaryExpr:
    operator: TokenType
    expr: Expr
    expr_span: SourceSpan
    op_span: SourceSpan
    result: Type = field(default_factory=lambda: PrimitiveType.VOID)


@dataclass
class BinaryExpr:
    left_expr: Expr
    operator: TokenType
    right_expr: Expr
    expr_span: SourceSpan
    op_span: SourceSpan
    result: Type = field(default_factory=lambda: PrimitiveType.VOID)


@dataclass
class LogicalExpr:
    left_expr: Expr
    operator: TokenType
    right_expr: Expr
    expr_span: SourceSpan
    op_span: SourceSpan
    result: Type = field(default_factory=lambda: PrimitiveType.BOOL)


@dataclass
class CallExpr:
    receiver: Optional[Expr]
    fn_name: str
    expr_span: SourceSpan
    name_span: SourceSpan
    arguments: List[Expr] = field(default_factory=lambda: [])
    fn_ptr: Optional[HostFn] = None
    result: Type = field(default_factory=lambda: PrimitiveType.VOID)


@dataclass
class ParenthesizedExpr:
    expr: Expr
    expr_span: SourceSpan
    result: Type = field(default_factory=lambda: PrimitiveType.VOID)


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
    expr: Expr
    name_span: SourceSpan
    type_span: SourceSpan


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
    return_span: SourceSpan
    value: Optional[Expr] = None


@dataclass
class WhileStatement:
    condition: Expr
    body_statements: List[Statement]


@dataclass
class BreakStatement:
    span: SourceSpan


@dataclass
class ContinueStatement:
    span: SourceSpan


@dataclass
class EmptyLineStatement:
    pass


@dataclass
class CommentStatement:
    string: str
    comment_span: SourceSpan


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


@dataclass(frozen=True)
class Parameter:
    name: str
    type: Type
    name_span: SourceSpan
    type_span: SourceSpan


@dataclass
class OnFn:
    fn_name: str
    span: SourceSpan
    parameters: List[Parameter] = field(default_factory=lambda: [])
    body_statements: List[Statement] = field(default_factory=lambda: [])


@dataclass
class HelperFn:
    fn_name: str
    span: SourceSpan
    parameters: List[Parameter] = field(default_factory=lambda: [])
    return_type: Type = PrimitiveType.VOID
    body_statements: List[Statement] = field(default_factory=lambda: [])


Ast = List[
    Union[VariableStatement, EmptyLineStatement, CommentStatement, OnFn, HelperFn]
]


class Parser:
    def __init__(self, tokens: List[Token], file_path: Path, source_text: str):
        self.tokens = tokens
        self.file_path = file_path
        self.source_text = source_text
        self.ast: Ast = []
        self.helper_fns: Dict[str, HelperFn] = {}
        self.on_fns: Dict[str, OnFn] = {}
        self.statements = []
        self.arguments = []
        self.parsing_depth = 0
        self.loop_depth = 0
        self.indentation = 0
        self.called_helper_fn_names: Set[str] = set()
        self.current_function: Optional[str] = None

    def new_error(self, err_span: SourceSpan, error_message: str) -> GrugError:
        return GrugError.new_compile_error(
            self.file_path,
            self.current_function,
            self.source_text,
            err_span,
            error_message,
        )

    @staticmethod
    def type_contains_entity(typ: Type) -> bool:
        if isinstance(typ, EntityStrType):
            return True
        if isinstance(typ, IdType):
            for generic_type in typ.generics:
                if Parser.type_contains_entity(generic_type):
                    return True
            return False
        return False

    @staticmethod
    def type_contains_resource(typ: Type) -> bool:
        if isinstance(typ, ResourceStrType):
            return True
        if isinstance(typ, IdType):
            for generic_type in typ.generics:
                if Parser.type_contains_resource(generic_type):
                    return True
            return False
        return False

    def token_span(self, token_index: int) -> SourceSpan:
        if token_index < len(self.tokens):
            return self.tokens[token_index].span
        # We never call token_span if self.tokens is empty
        return self.tokens[-1].span

    def parse(self):
        seen_on_fn = False
        seen_newline = False
        newline_allowed = False
        newline_required = False

        i = [0]  # Use a list to allow modification by called functions
        while i[0] < len(self.tokens):
            token = self.tokens[i[0]]

            if (
                token.type == TokenType.WORD_TOKEN
                and i[0] + 1 < len(self.tokens)
                and self.tokens[i[0] + 1].type == TokenType.COLON_TOKEN
            ):
                if seen_on_fn:
        try:
            i = [0]  # Use a list to allow modification by called functions
            while i[0] < len(self.tokens):
                token = self.tokens[i[0]]

                if (
                    token.type == TokenType.WORD_TOKEN
                    and i[0] + 1 < len(self.tokens)
                    and self.tokens[i[0] + 1].type == TokenType.COLON_TOKEN
                ):
                    if seen_on_fn:
                        raise self.new_error(
                            token.span,
                            "Cannot declare member variables after on_ functions",
                        )

                    self.ast.append(self.parse_global_variable(i))

                    self.consume_token_type(i, TokenType.NEWLINE_TOKEN)

                    newline_allowed = True
                    newline_required = True

                    continue

                elif token.type == TokenType.EXPORT_TOKEN:
                    self.assert_token_type(i[0] + 1, TokenType.SPACE_TOKEN)
                    name_token = self.peek_token(i[0] + 2)
                    if newline_required:
                        raise ParserError(name_token.span, f"Expected an empty line")

                    fn = self.parse_export_fn(i)
                    if fn.fn_name in self.on_fns:
                        raise GrugError.new_compile_error(
                            self.file_path,
                            fn.fn_name,
                            self.source_text,
                            fn.span,
                            f"The function '{fn.fn_name}' was defined several times in the same file",
                        )
                    self.on_fns[fn.fn_name] = fn

                    self.consume_token_type(i, TokenType.NEWLINE_TOKEN)

                    seen_on_fn = True

                    newline_allowed = True
                    newline_required = True

                    continue

                elif token.type == TokenType.LOCAL_TOKEN:
                    self.assert_token_type(i[0] + 1, TokenType.SPACE_TOKEN)
                    self.assert_token_type(i[0] + 2, TokenType.WORD_TOKEN)
                    name_token = self.peek_token(i[0] + 2)
                    if newline_required:
                        raise ParserError(name_token.span, f"Expected an empty line")

                    fn = self.parse_local_fn(i)
                    if fn.fn_name in self.helper_fns:
                        raise GrugError.new_compile_error(
                            self.file_path,
                            fn.fn_name,
                            self.source_text,
                            fn.span,
                            f"The function '{fn.fn_name}' was defined several times in the same file",
                        )
                    self.helper_fns[fn.fn_name] = fn

                    self.consume_token_type(i, TokenType.NEWLINE_TOKEN)

                    newline_allowed = True
                    newline_required = True

                    continue

                elif token.type == TokenType.NEWLINE_TOKEN:
                    if not newline_allowed:
                        raise ParserError(token.span, f"Unexpected empty line")

                    seen_newline = True

                    newline_allowed = False
                    newline_required = False

                    self.ast.append(EmptyLineStatement())
                    i[0] += 1
                    continue

                elif token.type == TokenType.COMMENT_TOKEN:
                    newline_allowed = True
                    self.ast.append(CommentStatement(token.value, token.span))
                    i[0] += 1
                    self.consume_token_type(i, TokenType.NEWLINE_TOKEN)
                    continue

                else:
                    raise ParserError(
                        token.span,
                        f"Unexpected token '{token.value}' on line {self.get_token_line_number(i[0])}",
                    )

                self.ast.append(self.parse_global_variable(i))

                self.consume_token_type(i, TokenType.NEWLINE_TOKEN)

                newline_allowed = True
                newline_required = True

                continue

            elif (
                token.type == TokenType.WORD_TOKEN
                and token.value.startswith("on_")
                and i[0] + 1 < len(self.tokens)
                and self.tokens[i[0] + 1].type == TokenType.OPEN_PARENTHESIS_TOKEN
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

                continue

            elif (
                token.type == TokenType.WORD_TOKEN
                and token.value.startswith("helper_")
                and i[0] + 1 < len(self.tokens)
                and self.tokens[i[0] + 1].type == TokenType.OPEN_PARENTHESIS_TOKEN
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

                continue

            elif token.type == TokenType.NEWLINE_TOKEN:
                if not newline_allowed:
                    raise ParserError(
                        f"Unexpected empty line, on line {self.get_token_line_number(i[0])}"
                    )

                seen_newline = True

                newline_allowed = False
                newline_required = False

                self.ast.append(EmptyLineStatement())
                i[0] += 1
                continue

            elif token.type == TokenType.COMMENT_TOKEN:
                newline_allowed = True
                self.ast.append(CommentStatement(token.value))
                i[0] += 1
                self.consume_token_type(i, TokenType.NEWLINE_TOKEN)
                continue

            else:
            if seen_newline and not newline_allowed:
                raise ParserError(
                    self.token_span(len(self.tokens) - 1), f"Unexpected empty line"
                )
        except ParserError as err:
            raise self.new_error(err.span, err.message) from err

        return self.ast

    def peek_token(self, token_index: int):
        if token_index >= len(self.tokens):
            raise ParserError(self.token_span(token_index), f"unexpected end of file")
        return self.tokens[token_index]

    def consume_token(self, i: List[int]):
        token_index = i[0]
        token = self.peek_token(token_index)
        i[0] += 1
        return token

    def assert_token_type(self, token_index: int, expected_type: TokenType):
        try:
            token = self.peek_token(token_index)
        except Exception as _:
            raise ParserError(
                self.token_span(token_index),
                f"Expected {expected_type} but got end of file",
            )
        if token.type != expected_type:
            raise ParserError(
                token.span, f"Expected {expected_type} but got {token.type}"
            )

    def consume_token_type(self, i: List[int], expected_type: TokenType):
        self.assert_token_type(i[0], expected_type)
        i[0] += 1
        return self.tokens[i[0] - 1]

    def get_token_line_number(self, token_index: int):
        assert token_index < len(self.tokens)
        line_number = 1
        for idx in range(token_index):
            if self.tokens[idx].type == TokenType.NEWLINE_TOKEN:
                line_number += 1
        return line_number

    def parse_statement(self, i: List[int]):
        self.increase_parsing_depth(i)
        switch_token = self.peek_token(i[0])

        if switch_token.type == TokenType.WORD_TOKEN:
            token = self.peek_token(i[0] + 1)
            if (
                token.type == TokenType.OPEN_PARENTHESIS_TOKEN
                or token.type == TokenType.DOT_TOKEN
            ):
                expr = self.parse_call(i)
                expr = self.try_parse_method(expr, i)

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
                    self.peek_token(i[0] + 1).span,
                    f"Expected '(', or ':', or ' =' after the word '{switch_token.value}' on line {self.get_token_line_number(i[0])}",
                )
        elif switch_token.type == TokenType.IF_TOKEN:
            statement = self.parse_if_statement(i)
        elif switch_token.type == TokenType.RETURN_TOKEN:
            i[0] += 1
            token = self.peek_token(i[0])
            if token.type == TokenType.NEWLINE_TOKEN:
                statement = ReturnStatement(switch_token.span)
            else:
                self.consume_space(i)
                expr = self.parse_expression(i)
                statement = ReturnStatement(switch_token.span, expr)
        elif switch_token.type == TokenType.WHILE_TOKEN:
            i[0] += 1
            statement = self.parse_while_statement(i)
        elif switch_token.type == TokenType.BREAK_TOKEN:
            if self.loop_depth == 0:
                raise self.new_error(
                    switch_token.span,
                    f"There is a break statement that isn't inside of a while loop",
                )
            i[0] += 1
            statement = BreakStatement(switch_token.span)
        elif switch_token.type == TokenType.CONTINUE_TOKEN:
            if self.loop_depth == 0:
                raise self.new_error(
                    switch_token.span,
                    f"There is a continue statement that isn't inside of a while loop",
                )
            i[0] += 1
            statement = ContinueStatement(switch_token.span)
        elif switch_token.type == TokenType.COMMENT_TOKEN:
            i[0] += 1
            statement = CommentStatement(switch_token.value, switch_token.span)
        else:
            raise ParserError(
                switch_token.span,
                f"Expected a statement token, but got {switch_token.type} on line {self.get_token_line_number(i[0])}",
            )

        self.decrease_parsing_depth()
        return statement

    def parse_type(self, i: List[int]) -> Tuple[Type, SourceSpan]:
        type_token = self.consume_token_type(i, TokenType.WORD_TOKEN)
        type_name = type_token.value

        if type_name == "bool":
            return PrimitiveType.BOOL, type_token.span
        if type_name == "number":
            return PrimitiveType.NUMBER, type_token.span
        if type_name == "string":
            return PrimitiveType.STRING, type_token.span
        if type_name == "resource":
            return ResourceStrType(extension=""), type_token.span
        if type_name == "entity":
            return EntityStrType(entity_type=None), type_token.span

        generics: List[Type] = []
        if (
            i[0] < len(self.tokens)
            and self.peek_token(i[0]).type == TokenType.OPEN_BRACKET_TOKEN
        ):
            i[0] += 1
            generics.append(self.parse_type(i)[0])

            while (
                i[0] < len(self.tokens)
                and self.peek_token(i[0]).type == TokenType.COMMA_TOKEN
            ):
                i[0] += 1
                self.consume_space(i)
                generics.append(self.parse_type(i)[0])

            self.consume_token_type(i, TokenType.CLOSE_BRACKET_TOKEN)

        return IdType(type_name, generics), type_token.span

    def parse_parameters(self, i: List[int]):
        parameters: List[Parameter] = []

        # First argument
        name_token = self.consume_token(i)
        param_name = name_token.value

        self.consume_token_type(i, TokenType.COLON_TOKEN)

        self.consume_space(i)

        param_type, type_span = self.parse_type(i)

        if Parser.type_contains_entity(param_type):
            raise self.new_error(
                type_span,
                f"The argument '{param_name}' can't contain 'entity' in its type",
            )

        if Parser.type_contains_resource(param_type):
            raise self.new_error(
                type_span,
                f"The argument '{param_name}' can't contain 'resource' in its type",
            )

        parameters.append(
            Parameter(
                param_name,
                param_type,
                name_span=name_token.span,
                type_span=type_span,
            )
        )

        # Every argument after the first one starts with a comma
        while True:
            token = self.peek_token(i[0])
            if token.type != TokenType.COMMA_TOKEN:
                break
            i[0] += 1

            self.consume_space(i)
            self.assert_token_type(i[0], TokenType.WORD_TOKEN)
            name_token = self.consume_token(i)
            param_name = name_token.value

            self.consume_token_type(i, TokenType.COLON_TOKEN)

            self.consume_space(i)

            param_type, type_span = self.parse_type(i)

            if Parser.type_contains_entity(param_type):
                raise self.new_error(
                    type_span,
                    f"The argument '{param_name}' can't contain 'entity' in its type",
                )
            if Parser.type_contains_resource(param_type):
                raise self.new_error(
                    type_span,
                    f"The argument '{param_name}' can't contain 'resource' in its type",
                )

            parameters.append(
                Parameter(
                    param_name,
                    param_type,
                    name_span=name_token.span,
                    type_span=type_span,
                )
            )

        return parameters

    def parse_local_fn(self, i: List[int]):
        # local token
        self.consume_token(i)
        # space token
        self.consume_space(i)

        fn_name = self.consume_token(i)

        fn = HelperFn(fn_name.value, fn_name.span)
        self.current_function = fn.fn_name
        if not fn.fn_name.startswith("_"):
            raise self.new_error(
                fn_name.span, f"Local function name must begin with '_'"
            )

        if fn.fn_name not in self.called_helper_fn_names:
            raise self.new_error(
                fn.span,
                f"{fn.fn_name}() is defined before the first time it gets called",
            )

        self.consume_token_type(i, TokenType.OPEN_PARENTHESIS_TOKEN)

        token = self.peek_token(i[0])
        if token.type == TokenType.WORD_TOKEN:
            fn.parameters = self.parse_parameters(i)

        self.consume_token_type(i, TokenType.CLOSE_PARENTHESIS_TOKEN)

        self.assert_token_type(i[0], TokenType.SPACE_TOKEN)
        token = self.peek_token(i[0] + 1)
        if token.type == TokenType.WORD_TOKEN:
            i[0] += 1
            fn.return_type, type_span = self.parse_type(i)

            if Parser.type_contains_entity(fn.return_type):
                raise self.new_error(
                    type_span,
                    f"The function '{fn.fn_name}' can't contain 'entity' in its return type",
                )
            if Parser.type_contains_resource(fn.return_type):
                raise self.new_error(
                    type_span,
                    f"The function '{fn.fn_name}' can't contain 'resource' in its return type",
                )

        self.indentation = 0
        fn.body_statements = self.parse_statements(i)

        if all(
            isinstance(s, (EmptyLineStatement, CommentStatement))
            for s in fn.body_statements
        ):
            raise self.new_error(fn.span, f"{fn.fn_name}() can't be empty")

        self.ast.append(fn)
        self.current_function = None
        return fn

    def parse_export_fn(self, i: List[int]):
        # export token
        self.consume_token(i)
        # space token
        self.consume_space(i)
        # name token
        name_token = self.consume_token_type(i, TokenType.WORD_TOKEN)
        if self.helper_fns:
            raise GrugError.new_compile_error(
                self.file_path,
                name_token.value,
                self.source_text,
                name_token.span,
                f"{name_token.value}() must be defined before all local functions",
            )

        fn = OnFn(name_token.value, name_token.span)
        previous_function = self.current_function
        self.current_function = fn.fn_name

        self.consume_token_type(i, TokenType.OPEN_PARENTHESIS_TOKEN)
        next_tok = self.peek_token(i[0])
        if next_tok.type == TokenType.WORD_TOKEN:
            fn.parameters = self.parse_parameters(i)
        self.consume_token_type(i, TokenType.CLOSE_PARENTHESIS_TOKEN)

        fn.body_statements = self.parse_statements(i)
        if all(
            isinstance(s, (EmptyLineStatement, CommentStatement))
            for s in fn.body_statements
        ):
            raise self.new_error(fn.span, f"{fn.fn_name}() can't be empty")

        self.ast.append(fn)
        self.current_function = previous_function
        return fn

    def parse_statements(self, i: List[int]):
        stmts: List[Statement] = []

        self.increase_parsing_depth(i)
        self.consume_space(i)
        self.consume_token_type(i, TokenType.OPEN_BRACE_TOKEN)
        self.consume_token_type(i, TokenType.NEWLINE_TOKEN)

        self.indentation += 1

        seen_newline = False
        newline_allowed = False

        while True:
            if self.is_end_of_block(i):
                break

            tok = self.peek_token(i[0])
            if tok.type == TokenType.NEWLINE_TOKEN:
                if not newline_allowed:
                    raise ParserError(tok.span, f"Unexpected empty line")
                i[0] += 1
                seen_newline = True
                newline_allowed = False
                stmts.append(EmptyLineStatement())
            else:
                newline_allowed = True

                self.consume_indentation(i)
                if self.peek_token(i[0]).type == TokenType.NEWLINE_TOKEN:
                    raise ParserError(tok.span, "Empty line cannot have indentation")

                stmt = self.parse_statement(i)
                stmts.append(stmt)

                self.consume_token_type(i, TokenType.NEWLINE_TOKEN)

        if seen_newline and not newline_allowed:
            raise ParserError(self.token_span(i[0] - 1), f"Unexpected empty line")

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
                tok.span, f"Expected token type SPACE_TOKEN, but got {tok.type}"
            )
        i[0] += 1

    def consume_indentation(self, i: List[int]):
        self.assert_token_type(i[0], TokenType.INDENTATION_TOKEN)
        spaces = len(self.peek_token(i[0]).value)
        expected = self.indentation * SPACES_PER_INDENT
        if spaces != expected:
            raise ParserError(
                self.peek_token(i[0]).span,
                f"Expected {expected} spaces, but got {spaces} spaces",
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
                tok.span,
                f"Expected indentation, line break, or '}}' but got '{tok.value}'",
            )

    def increase_parsing_depth(self, i: List[int]):
        self.parsing_depth += 1
        # TODO: We don't cover this test yet
        if self.parsing_depth >= MAX_PARSING_DEPTH:  # pragma: no cover
            raise ParserError(
                self.token_span(i[0]),
                f"There is a function that contains more than {MAX_PARSING_DEPTH} levels of nested expressions",
            )

    def decrease_parsing_depth(self):
        assert self.parsing_depth > 0
        self.parsing_depth -= 1

    def parse_local_variable(self, i: List[int]):
        var_token = self.consume_token(i)
        var_name = var_token.value

        var_type = None
        type_span = var_token.span

        if self.peek_token(i[0]).type == TokenType.COLON_TOKEN:
            i[0] += 1

            if var_name == "me":
                raise self.new_error(var_token.span, "variable cannot be named 'me'")

            self.consume_space(i)

            var_type, type_span = self.parse_type(i)

            if Parser.type_contains_resource(var_type):
                raise self.new_error(
                    type_span,
                    f"The variable '{var_name}' can't contain 'resource' in its type",
                )
            if Parser.type_contains_entity(var_type):
                raise self.new_error(
                    type_span,
                    f"The variable '{var_name}' can't contain 'entity' in its type",
                )

        if self.peek_token(i[0]).type != TokenType.SPACE_TOKEN:
            next_token = self.peek_token(i[0])
            err_span = SourceSpan(next_token.span.line, next_token.span.offset)
            raise self.new_error(
                err_span, f"Variable '{var_name}' was not assigned a value"
            )

        self.consume_space(i)

        self.consume_token_type(i, TokenType.ASSIGNMENT_TOKEN)

        if var_name == "me":
            raise self.new_error(
                var_token.span,
                "Assigning a new value to the entity's 'me' variable is not allowed",
            )

        self.consume_space(i)

        expr = self.parse_expression(i)

        return VariableStatement(var_name, var_type, expr, var_token.span, type_span)

    def parse_global_variable(self, i: List[int]):
        name_token = self.consume_token(i)
        global_name = name_token.value

        if global_name == "me":
            raise self.new_error(name_token.span, "variable cannot be named 'me'")

        self.consume_token_type(i, TokenType.COLON_TOKEN)
        self.consume_space(i)

        global_type, type_span = self.parse_type(i)

        if Parser.type_contains_resource(global_type):
            raise self.new_error(
                type_span,
                f"The global variable '{global_name}' can't contain 'resource' in its type",
            )
        if Parser.type_contains_entity(global_type):
            raise self.new_error(
                type_span,
                f"The global variable '{global_name}' can't contain 'entity' in its type",
            )

        next_token = self.peek_token(i[0])
        if next_token.type != TokenType.SPACE_TOKEN:
            raise self.new_error(
                next_token.span,
                f"The global variable '{global_name}' was not assigned a value",
            )

        self.consume_space(i)
        self.consume_token_type(i, TokenType.ASSIGNMENT_TOKEN)

        self.consume_space(i)
        expr = self.parse_expression(i)

        return VariableStatement(
            global_name, global_type, expr, name_token.span, type_span
        )

    def parse_unary(self, i: List[int]):
        self.increase_parsing_depth(i)
        token = self.peek_token(i[0])
        if token.type in (TokenType.MINUS_TOKEN, TokenType.NOT_TOKEN):
            i[0] += 1
            if token.type == TokenType.NOT_TOKEN:
                self.consume_space(i)
            expr = UnaryExpr(
                token.type,
                self.parse_unary(i),
                expr_span=token.span,
                op_span=token.span,
            )
            self.decrease_parsing_depth()
            return expr
        self.decrease_parsing_depth()
        expr = self.parse_call(i)
        expr = self.try_parse_method(expr, i)
        return expr

    def parse_call(self, i: List[int]):
        self.increase_parsing_depth(i)

        expr = self.parse_primary(i)

        token = self.peek_token(i[0])

        if token.type != TokenType.OPEN_PARENTHESIS_TOKEN:
            self.decrease_parsing_depth()
            return expr

        if not isinstance(expr, IdentifierExpr):
            raise ParserError(token.span, "Expected ')' but got '('")

        fn_name = expr.name
        expr = CallExpr(
            None, fn_name, expr_span=expr.expr_span, name_span=expr.expr_span
        )

        if fn_name.startswith("_"):
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

    def str_to_number(self, s: str, span: SourceSpan):
        f = float(s)

        # Overflow
        if not math.isfinite(f) or abs(f) > MAX_F64:
            raise self.new_error(span, f"The number {s} is too big")

        # Underflow
        if f != 0.0 and abs(f) < MIN_F64:
            raise self.new_error(span, f"The number {s} is too close to zero")

        # Check if conversion resulted in zero due to underflow
        if f == 0.0:
            # Check if the string actually represents zero or if it underflowed
            if any(c in s for c in "123456789"):
                raise self.new_error(span, f"The number {s} is too close to zero")

        return f

    def parse_primary(self, i: List[int]):
        self.increase_parsing_depth(i)

        token = self.peek_token(i[0])

        expr: Expr

        if token.type == TokenType.OPEN_PARENTHESIS_TOKEN:
            i[0] += 1
            expr = ParenthesizedExpr(self.parse_expression(i), expr_span=token.span)
            self.consume_token_type(i, TokenType.CLOSE_PARENTHESIS_TOKEN)
        elif token.type == TokenType.TRUE_TOKEN:
            i[0] += 1
            expr = TrueExpr()
        elif token.type == TokenType.FALSE_TOKEN:
            i[0] += 1
            expr = FalseExpr()
        elif token.type == TokenType.STRING_TOKEN:
            i[0] += 1
            expr = StringExpr(token.value)
        elif token.type == TokenType.ENTITY_TOKEN:
            i[0] += 1
            expr = EntityExpr(token.value)
        elif token.type == TokenType.RESOURCE_TOKEN:
            i[0] += 1
            expr = ResourceExpr(token.value)
        elif token.type == TokenType.WORD_TOKEN:
            i[0] += 1
            expr = IdentifierExpr(token.value)
        elif token.type == TokenType.NUMBER_TOKEN:
            expr = TrueExpr(expr_span=token.span)
        elif token.type == TokenType.FALSE_TOKEN:
            i[0] += 1
            expr = FalseExpr(expr_span=token.span)
        elif token.type == TokenType.STRING_TOKEN:
            i[0] += 1
            expr = StringExpr(token.value, expr_span=token.span)
        elif token.type == TokenType.ENTITY_TOKEN:
            i[0] += 1
            expr = EntityExpr(token.value, expr_span=token.span)
        elif token.type == TokenType.RESOURCE_TOKEN:
            i[0] += 1
            expr = ResourceExpr(token.value, expr_span=token.span)
        elif token.type == TokenType.WORD_TOKEN:
            i[0] += 1
            expr = IdentifierExpr(token.value, expr_span=token.span)
        elif token.type == TokenType.NUMBER_TOKEN:
            i[0] += 1
            expr = NumberExpr(
                self.str_to_number(token.value, token.span),
                token.value,
                expr_span=token.span,
            )
        else:
            raise ParserError(
                f"Expected a primary expression token, but got token type {token.type.name} on line {self.get_token_line_number(i[0])}"
                token.span, f"Expected a primary expression token but got {token.type}"
            )

        self.decrease_parsing_depth()
        return expr

    def try_parse_method(self, expr: Expr, i: List[int]):
        # If a "." token is next, parse a method call and return, else try
        # parsing a normal call

        while self.peek_token(i[0]).type == TokenType.DOT_TOKEN:
            i[0] += 1
            receiver = expr

            name_token = self.peek_token(i[0])
            # name must be word
            self.assert_token_type(i[0], TokenType.WORD_TOKEN)
            i[0] += 1

            token = self.peek_token(i[0])
            if token.type != TokenType.OPEN_PARENTHESIS_TOKEN:
                # Reserved for struct field accesses
                raise ParserError(token.span, "Method call expected '('")
            i[0] += 1

            expr = CallExpr(
                receiver,
                name_token.value,
                expr_span=receiver.expr_span,
                name_span=name_token.span,
            )

            token = self.peek_token(i[0])
            if token.type == TokenType.CLOSE_PARENTHESIS_TOKEN:
                i[0] += 1
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
                op_token = self.consume_token(i)
                op = op_token.type
                self.consume_space(i)
                right_expr = self.parse_unary(i)
                expr = BinaryExpr(
                    expr,
                    op,
                    right_expr,
                    expr_span=expr.expr_span,
                    op_span=op_token.span,
                )
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
                op_token = self.consume_token(i)
                op = op_token.type
                self.consume_space(i)
                right_expr = self.parse_factor(i)
                expr = BinaryExpr(
                    expr,
                    op,
                    right_expr,
                    expr_span=expr.expr_span,
                    op_span=op_token.span,
                )
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
                op_token = self.consume_token(i)
                op = op_token.type
                self.consume_space(i)
                right_expr = self.parse_term(i)
                expr = BinaryExpr(
                    expr,
                    op,
                    right_expr,
                    expr_span=expr.expr_span,
                    op_span=op_token.span,
                )
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
                op_token = self.consume_token(i)
                op = op_token.type
                self.consume_space(i)
                right_expr = self.parse_comparison(i)
                expr = BinaryExpr(
                    expr,
                    op,
                    right_expr,
                    expr_span=expr.expr_span,
                    op_span=op_token.span,
                )
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
                op_token = self.consume_token(i)
                op = op_token.type
                self.consume_space(i)
                right_expr = self.parse_equality(i)
                expr = LogicalExpr(
                    expr,
                    op,
                    right_expr,
                    expr_span=expr.expr_span,
                    op_span=op_token.span,
                )
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
                op_token = self.consume_token(i)
                op = op_token.type
                self.consume_space(i)
                right_expr = self.parse_and(i)
                expr = LogicalExpr(
                    expr,
                    op,
                    right_expr,
                    expr_span=expr.expr_span,
                    op_span=op_token.span,
                )
            else:
                break
        return expr

    def parse_expression(self, i: List[int]) -> Expr:
        self.increase_parsing_depth(i)
        expr = self.parse_or(i)
        self.decrease_parsing_depth()
        return expr

    def parse_if_statement(self, i: List[int]):
        self.increase_parsing_depth(i)
        ifs: List[Tuple[Expr, List[Statement]]] = []
        while True:
            # consume if token
            i[0] += 1
            self.consume_space(i)
            condition = self.parse_expression(i)
            if_body = self.parse_statements(i)

            tok = self.peek_token(i[0])
            if tok and tok.type == TokenType.SPACE_TOKEN:
                i[0] += 1

                self.consume_token_type(i, TokenType.ELSE_TOKEN)

                if (
                    self.peek_token(i[0]).type == TokenType.SPACE_TOKEN
                    and self.peek_token(i[0] + 1).type == TokenType.IF_TOKEN
                ):
                    i[0] += 1
                    ifs.append((condition, if_body))
                    continue
                else:
                    else_body = self.parse_statements(i)
            else:
                else_body = []

            ifs.append((condition, if_body))
            break

        current = ifs.pop()
        current = IfStatement(current[0], current[1], else_body)

        for statement in reversed(ifs):
            current = IfStatement(statement[0], statement[1], [current])

        self.decrease_parsing_depth()
        return current

    def parse_while_statement(self, i: List[int]):
        self.increase_parsing_depth(i)
        self.consume_space(i)
        condition = self.parse_expression(i)

        self.loop_depth += 1
        body = self.parse_statements(i)
        self.loop_depth -= 1

        self.decrease_parsing_depth()
        return WhileStatement(condition, body)
