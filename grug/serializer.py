import json
from io import StringIO
from typing import Any, Dict, List, Union

from .frontend import (
    Argument,
    Ast,
    BinaryExpr,
    BreakStatement,
    CallExpr,
    CallStatement,
    CommentStatement,
    ContinueStatement,
    EmptyLineStatement,
    EntityExpr,
    Expr,
    F32Expr,
    FalseExpr,
    HelperFn,
    I32Expr,
    IdentifierExpr,
    IfStatement,
    LogicalExpr,
    OnFn,
    ParenthesizedExpr,
    ResourceExpr,
    ReturnStatement,
    Statement,
    StringExpr,
    TrueExpr,
    UnaryExpr,
    VariableStatement,
    WhileStatement,
)


class Serializer:
    """Serializes AST to JSON text or Grug source code."""

    @staticmethod
    def _serialize_expr(expr: Expr) -> dict[str, Any]:
        """Serialize an expression node to dict."""
        result: dict[str, Any] = {}

        # Get the type name from the class name
        result["type"] = expr.__class__.__name__.replace("Expr", "").upper() + "_EXPR"

        # Handle different expression types
        if isinstance(expr, (TrueExpr, FalseExpr)):
            pass  # No additional fields
        elif isinstance(
            expr,
            (
                StringExpr,
                ResourceExpr,
                EntityExpr,
                IdentifierExpr,
            ),
        ):
            result["str"] = (
                expr.name if isinstance(expr, IdentifierExpr) else expr.string
            )
        elif isinstance(expr, I32Expr):
            result["value"] = str(expr.i32)
        elif isinstance(expr, F32Expr):
            result["value"] = expr.string
        elif isinstance(expr, UnaryExpr):
            result["operator"] = expr.operator.name
            result["expr"] = Serializer._serialize_expr(expr.expr)
        elif isinstance(expr, (BinaryExpr, LogicalExpr)):
            result["left_expr"] = Serializer._serialize_expr(expr.left_expr)
            result["operator"] = expr.operator.name
            result["right_expr"] = Serializer._serialize_expr(expr.right_expr)
        elif isinstance(expr, CallExpr):
            result["name"] = expr.fn_name
            if expr.arguments:
                result["arguments"] = [
                    Serializer._serialize_expr(arg) for arg in expr.arguments
                ]
        else:
            assert isinstance(expr, ParenthesizedExpr)
            result["expr"] = Serializer._serialize_expr(expr.expr)

        return result

    @staticmethod
    def _serialize_statement(stmt: Statement) -> dict[str, Any]:
        """Serialize a statement node to dict."""
        result: dict[str, Any] = {}

        # Get the type name from the class name
        result["type"] = (
            stmt.__class__.__name__.replace("Statement", "").upper() + "_STATEMENT"
        )

        if isinstance(stmt, VariableStatement):
            result["name"] = stmt.name
            if stmt.type:
                result["variable_type"] = stmt.type_name
            result["assignment"] = Serializer._serialize_expr(stmt.assignment_expr)
        elif isinstance(stmt, CallStatement):
            call_expr = stmt.expr
            result["name"] = call_expr.fn_name
            if call_expr.arguments:
                result["arguments"] = [
                    Serializer._serialize_expr(arg) for arg in call_expr.arguments
                ]
        elif isinstance(stmt, IfStatement):
            result["condition"] = Serializer._serialize_expr(stmt.condition)
            if stmt.if_body:
                result["if_statements"] = [
                    Serializer._serialize_statement(s) for s in stmt.if_body
                ]
            if hasattr(stmt, "else_body_statements") and stmt.else_body:
                result["else_statements"] = [
                    Serializer._serialize_statement(s) for s in stmt.else_body
                ]
        elif isinstance(stmt, ReturnStatement):
            if stmt.value:
                result["expr"] = Serializer._serialize_expr(stmt.value)
        elif isinstance(stmt, WhileStatement):
            result["condition"] = Serializer._serialize_expr(stmt.condition)
            result["statements"] = [
                Serializer._serialize_statement(s) for s in stmt.body_statements
            ]
        elif isinstance(stmt, CommentStatement):
            result["comment"] = stmt.string
        else:
            assert isinstance(
                stmt,
                (
                    BreakStatement,
                    ContinueStatement,
                    EmptyLineStatement,
                ),
            )

        return result

    @staticmethod
    def _serialize_arguments(arguments: list[Argument]) -> list[dict[str, str]]:
        """Serialize function arguments to list of dicts."""
        return [{"name": arg.name, "type": arg.type_name} for arg in arguments]

    @staticmethod
    def _serialize_global_statement(
        global_stmt: Union[
            VariableStatement, EmptyLineStatement, CommentStatement, OnFn, HelperFn
        ],
    ) -> dict[str, Any]:
        """Serialize a global statement node to dict."""
        result: dict[str, Any] = {}

        if isinstance(global_stmt, OnFn):
            result["type"] = "GLOBAL_ON_FN"
            result["name"] = global_stmt.fn_name
            if global_stmt.arguments:
                result["arguments"] = Serializer._serialize_arguments(
                    global_stmt.arguments
                )
            result["statements"] = [
                Serializer._serialize_statement(s) for s in global_stmt.body_statements
            ]
        elif isinstance(global_stmt, HelperFn):
            result["type"] = "GLOBAL_HELPER_FN"
            result["name"] = global_stmt.fn_name
            if global_stmt.arguments:
                result["arguments"] = Serializer._serialize_arguments(
                    global_stmt.arguments
                )
            if hasattr(global_stmt, "return_type") and global_stmt.return_type:
                result["return_type"] = global_stmt.return_type_name
            result["statements"] = [
                Serializer._serialize_statement(s) for s in global_stmt.body_statements
            ]
        elif isinstance(global_stmt, VariableStatement):
            result["type"] = "GLOBAL_VARIABLE"
            result["name"] = global_stmt.name
            result["variable_type"] = global_stmt.type_name
            result["assignment"] = Serializer._serialize_expr(
                global_stmt.assignment_expr
            )
        elif isinstance(global_stmt, CommentStatement):
            result["type"] = "GLOBAL_COMMENT"
            result["comment"] = global_stmt.string
        else:
            assert isinstance(global_stmt, EmptyLineStatement)
            result["type"] = "GLOBAL_EMPTY_LINE"

        return result

    @staticmethod
    def ast_to_json_text(ast: Ast) -> str:
        """Convert AST to JSON text representation."""
        serialized = [Serializer._serialize_global_statement(node) for node in ast]
        return json.dumps(serialized, separators=(",", ":"))
        # return json.dumps(serialized, indent=4)  # TODO: Ensure this works too!

    @staticmethod
    def ast_to_grug(ast: List[Dict[str, Any]]) -> str:
        """Convert AST to Grug source code."""
        output = StringIO()
        indentation = [0]  # Using list to make it mutable in nested functions

        def write(text: str) -> None:
            """Write text to output."""
            output.write(text)

        def apply_indentation() -> None:
            """Apply current indentation level."""
            write("    " * indentation[0])

        def apply_expr(expr: Dict[str, Any]) -> None:
            """Generate code for an expression."""
            assert isinstance(expr, dict), "Expression must be a dict"
            assert "type" in expr, "Expression must have a 'type' field"

            expr_type = expr["type"]

            if expr_type == "TRUE_EXPR":
                write("true")
            elif expr_type == "FALSE_EXPR":
                write("false")
            elif expr_type == "STRING_EXPR":
                write(f'"{expr["str"]}"')
            elif expr_type == "IDENTIFIER_EXPR":
                write(expr["str"])
            elif expr_type == "I32_EXPR":
                write(expr["value"])
            elif expr_type == "F32_EXPR":
                write(expr["value"])
            elif expr_type == "UNARY_EXPR":
                operator = expr["operator"]
                if operator == "MINUS_TOKEN":
                    write("-")
                elif operator == "NOT_TOKEN":
                    write("not ")
                apply_expr(expr["expr"])
            elif expr_type == "BINARY_EXPR":
                apply_expr(expr["left_expr"])
                operator = get_binary_operator(expr["operator"])
                write(f" {operator} ")
                apply_expr(expr["right_expr"])
            elif expr_type == "LOGICAL_EXPR":
                apply_expr(expr["left_expr"])
                operator = get_logical_operator(expr["operator"])
                write(f" {operator} ")
                apply_expr(expr["right_expr"])
            elif expr_type == "CALL_EXPR":
                write(f'{expr["name"]}(')
                if "arguments" in expr:
                    for i, arg in enumerate(expr["arguments"]):
                        if i > 0:
                            write(", ")
                        apply_expr(arg)
                write(")")
            elif expr_type == "PARENTHESIZED_EXPR":
                write("(")
                apply_expr(expr["expr"])
                write(")")

        def get_logical_operator(token: str) -> str:
            """Convert token to logical operator."""
            if token == "AND_TOKEN":
                return "and"
            elif token == "OR_TOKEN":
                return "or"
            raise ValueError(f"Unknown logical operator: {token}")

        def get_binary_operator(token: str) -> str:
            """Convert token to binary operator."""
            operators = {
                "PLUS_TOKEN": "+",
                "MINUS_TOKEN": "-",
                "MULTIPLICATION_TOKEN": "*",
                "DIVISION_TOKEN": "/",
                "REMAINDER_TOKEN": "%",
                "EQUALS_TOKEN": "==",
                "NOT_EQUALS_TOKEN": "!=",
                "GREATER_OR_EQUAL_TOKEN": ">=",
                "GREATER_TOKEN": ">",
                "LESS_OR_EQUAL_TOKEN": "<=",
                "LESS_TOKEN": "<",
            }
            if token in operators:
                return operators[token]
            raise ValueError(f"Unknown binary operator: {token}")

        def try_get_else_if(
            else_statements: List[Dict[str, Any]],
        ) -> Union[Dict[str, Any], None]:
            """Check if else block is actually an else-if."""
            if (
                len(else_statements) > 0
                and else_statements[0].get("type") == "IF_STATEMENT"
            ):
                return else_statements[0]
            return None

        def apply_comment(statement: Dict[str, Any]) -> None:
            """Generate code for a comment."""
            write(f'# {statement["comment"]}\n')

        def apply_if_statement(statement: Dict[str, Any]) -> None:
            """Generate code for an if statement."""
            write("if ")
            apply_expr(statement["condition"])
            write(" {\n")

            if "if_statements" in statement:
                apply_statements(statement["if_statements"])

            if "else_statements" in statement:
                apply_indentation()
                write("} else ")

                else_if_node = try_get_else_if(statement["else_statements"])
                if else_if_node:
                    apply_if_statement(else_if_node)
                else:
                    write("{\n")
                    apply_statements(statement["else_statements"])
                    apply_indentation()
                    write("}\n")
            else:
                apply_indentation()
                write("}\n")

        def apply_statement(statement: Dict[str, Any]) -> None:
            """Generate code for a statement."""
            stmt_type = statement["type"]

            if stmt_type == "VARIABLE_STATEMENT":
                write(statement["name"])

                if "variable_type" in statement:
                    write(f': {statement["variable_type"]}')

                if "assignment" in statement:
                    write(" = ")
                    apply_expr(statement["assignment"])

                write("\n")

            elif stmt_type == "CALL_STATEMENT":
                write(f'{statement["name"]}(')
                if "arguments" in statement:
                    for i, arg in enumerate(statement["arguments"]):
                        if i > 0:
                            write(", ")
                        apply_expr(arg)
                write(")\n")

            elif stmt_type == "IF_STATEMENT":
                apply_if_statement(statement)

            elif stmt_type == "RETURN_STATEMENT":
                write("return")
                if "expr" in statement:
                    write(" ")
                    apply_expr(statement["expr"])
                write("\n")

            elif stmt_type == "WHILE_STATEMENT":
                write("while ")
                apply_expr(statement["condition"])
                write(" {\n")
                apply_statements(statement["statements"])
                apply_indentation()
                write("}\n")

            elif stmt_type == "BREAK_STATEMENT":
                write("break\n")

            elif stmt_type == "CONTINUE_STATEMENT":
                write("continue\n")

            elif stmt_type == "COMMENT_STATEMENT":
                apply_comment(statement)

        def apply_statements(statements: List[Dict[str, Any]]) -> None:
            """Generate code for a list of statements."""
            indentation[0] += 1

            for statement in statements:
                if statement["type"] == "EMPTY_LINE_STATEMENT":
                    write("\n")
                else:
                    apply_indentation()
                    apply_statement(statement)

            indentation[0] -= 1

        def apply_arguments(arguments: List[Dict[str, Any]]) -> None:
            """Generate code for function arguments."""
            for i, arg in enumerate(arguments):
                if i > 0:
                    write(", ")
                write(f'{arg["name"]}: {arg["type"]}')

        def apply_helper_fn(statement: Dict[str, Any]) -> None:
            """Generate code for a helper function."""
            write(f'{statement["name"]}(')

            if "arguments" in statement:
                apply_arguments(statement["arguments"])

            write(")")

            if "return_type" in statement:
                write(f' {statement["return_type"]}')

            write(" {\n")

            if "statements" in statement:
                apply_statements(statement["statements"])

            write("}\n")

        def apply_on_fn(statement: Dict[str, Any]) -> None:
            """Generate code for an on function."""
            write(f'{statement["name"]}(')

            if "arguments" in statement:
                apply_arguments(statement["arguments"])

            write(") {\n")

            if "statements" in statement:
                apply_statements(statement["statements"])

            write("}\n")

        def apply_global_variable(statement: Dict[str, Any]) -> None:
            """Generate code for a global variable."""
            write(f'{statement["name"]}: {statement["variable_type"]} = ')
            apply_expr(statement["assignment"])
            write("\n")

        def apply_root(root: List[Dict[str, Any]]) -> None:
            """Generate code for the root AST node."""
            for statement in root:
                stmt_type = statement["type"]

                if stmt_type == "GLOBAL_VARIABLE":
                    apply_global_variable(statement)
                elif stmt_type == "GLOBAL_ON_FN":
                    apply_on_fn(statement)
                elif stmt_type == "GLOBAL_HELPER_FN":
                    apply_helper_fn(statement)
                elif stmt_type == "GLOBAL_EMPTY_LINE":
                    write("\n")
                elif stmt_type == "GLOBAL_COMMENT":
                    apply_comment(statement)

        # Main execution
        apply_root(ast)
        return output.getvalue()
