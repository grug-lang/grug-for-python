"""Visitor pattern for transforming grug AST.

This module provides visitor functions for traversing and modifying
grug AST nodes. The main use case is transforming function calls
(e.g., replacing `write()` with `write_safe()`).

Example usage:
    import grug
    
    state = grug.init()
    mods = state.compile_all_mods()
    
    # Replace all 'write' calls with 'write_safe'
    grug.visitor.transform_calls_in_dir(mods, 'write', 'write_safe')
    
    # Write back to files
    grug.visitor.write_dir_to_grug(mods, state.mods_dir_path)
"""

from typing import Callable, Dict, List, Optional, Union, Any
from pathlib import Path
import json

from .parser import (
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
    FalseExpr,
    HelperFn,
    IdentifierExpr,
    IfStatement,
    LogicalExpr,
    NumberExpr,
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
from .grug_state import GrugFile, GrugDir
from .serializer import Serializer


# Type for callback functions that transform expressions
ExprTransformer = Callable[[Expr], Optional[Expr]]
StmtTransformer = Callable[[Statement], Optional[Statement]]


def visit_expr(expr: Expr, callback: ExprTransformer) -> Expr:
    """
    Visit an expression and apply a transformation callback.
    
    The callback can return:
    - None: keep the original expression unchanged
    - A new Expr: replace the expression with the returned one
    
    This function recursively visits all sub-expressions.
    
    Args:
        expr: The expression to visit
        callback: A function that takes an Expr and returns Optional[Expr]
    
    Returns:
        The transformed expression (or original if callback returns None)
    
    Example:
        def replace_write(expr):
            if isinstance(expr, CallExpr) and expr.fn_name == 'write':
                expr.fn_name = 'write_safe'
            return None  # We modified in-place
        
        visit_expr(my_expr, replace_write)
    """
    # Apply callback first (pre-order traversal)
    result = callback(expr)
    if result is not None:
        expr = result
    
    # Recursively visit sub-expressions
    if isinstance(expr, UnaryExpr):
        expr.expr = visit_expr(expr.expr, callback)
    elif isinstance(expr, BinaryExpr):
        expr.left_expr = visit_expr(expr.left_expr, callback)
        expr.right_expr = visit_expr(expr.right_expr, callback)
    elif isinstance(expr, LogicalExpr):
        expr.left_expr = visit_expr(expr.left_expr, callback)
        expr.right_expr = visit_expr(expr.right_expr, callback)
    elif isinstance(expr, CallExpr):
        expr.arguments = [visit_expr(arg, callback) for arg in expr.arguments]
    elif isinstance(expr, ParenthesizedExpr):
        expr.expr = visit_expr(expr.expr, callback)
    
    # Terminal expressions (TrueExpr, FalseExpr, StringExpr, etc.) have no sub-expressions
    
    return expr


def visit_statement(stmt: Statement, expr_callback: ExprTransformer, stmt_callback: Optional[StmtTransformer] = None) -> Statement:
    """
    Visit a statement and apply transformation callbacks.
    
    Args:
        stmt: The statement to visit
        expr_callback: A function to transform expressions within the statement
        stmt_callback: Optional function to transform the statement itself
    
    Returns:
        The transformed statement
    """
    # Apply statement callback first
    if stmt_callback is not None:
        result = stmt_callback(stmt)
        if result is not None:
            stmt = result
    
    # Visit expressions within the statement
    if isinstance(stmt, VariableStatement):
        stmt.expr = visit_expr(stmt.expr, expr_callback)
    elif isinstance(stmt, CallStatement):
        # CallStatement contains a CallExpr
        stmt.expr = visit_expr(stmt.expr, expr_callback)
    elif isinstance(stmt, IfStatement):
        stmt.condition = visit_expr(stmt.condition, expr_callback)
        stmt.if_body = [visit_statement(s, expr_callback, stmt_callback) for s in stmt.if_body]
        stmt.else_body = [visit_statement(s, expr_callback, stmt_callback) for s in stmt.else_body]
    elif isinstance(stmt, ReturnStatement):
        if stmt.value is not None:
            stmt.value = visit_expr(stmt.value, expr_callback)
    elif isinstance(stmt, WhileStatement):
        stmt.condition = visit_expr(stmt.condition, expr_callback)
        stmt.body_statements = [visit_statement(s, expr_callback, stmt_callback) for s in stmt.body_statements]
    
    # EmptyLineStatement, BreakStatement, ContinueStatement, CommentStatement have no expressions
    
    return stmt


def visit_fn(fn: Union[OnFn, HelperFn], expr_callback: ExprTransformer, stmt_callback: Optional[StmtTransformer] = None) -> Union[OnFn, HelperFn]:
    """
    Visit a function (OnFn or HelperFn) and apply transformation callbacks.
    
    Args:
        fn: The function to visit
        expr_callback: A function to transform expressions
        stmt_callback: Optional function to transform statements
    
    Returns:
        The transformed function
    """
    fn.body_statements = [visit_statement(s, expr_callback, stmt_callback) for s in fn.body_statements]
    return fn


def visit_grug_file(grug_file: GrugFile, expr_callback: ExprTransformer, stmt_callback: Optional[StmtTransformer] = None) -> GrugFile:
    """
    Visit a GrugFile and apply transformation callbacks.
    
    This visits all global variables, on functions, and helper functions.
    
    Args:
        grug_file: The GrugFile to visit
        expr_callback: A function to transform expressions
        stmt_callback: Optional function to transform statements
    
    Returns:
        The transformed GrugFile
    """
    # Visit global variables
    grug_file.global_variables = [
        visit_statement(v, expr_callback, stmt_callback) 
        for v in grug_file.global_variables
    ]
    
    # Visit on_fns
    for fn_name, fn in grug_file.on_fns.items():
        grug_file.on_fns[fn_name] = visit_fn(fn, expr_callback, stmt_callback)
    
    # Visit helper_fns
    for fn_name, fn in grug_file.helper_fns.items():
        grug_file.helper_fns[fn_name] = visit_fn(fn, expr_callback, stmt_callback)
    
    return grug_file


def visit_grug_dir(grug_dir: GrugDir, expr_callback: ExprTransformer, stmt_callback: Optional[StmtTransformer] = None) -> GrugDir:
    """
    Visit a GrugDir recursively and apply transformation callbacks.
    
    Args:
        grug_dir: The GrugDir to visit
        expr_callback: A function to transform expressions
        stmt_callback: Optional function to transform statements
    
    Returns:
        The transformed GrugDir
    """
    # Visit all files in this directory
    for file_path, grug_file in grug_dir.files.items():
        grug_dir.files[file_path] = visit_grug_file(grug_file, expr_callback, stmt_callback)
    
    # Recursively visit subdirectories
    for dir_name, sub_dir in grug_dir.dirs.items():
        grug_dir.dirs[dir_name] = visit_grug_dir(sub_dir, expr_callback, stmt_callback)
    
    return grug_dir


def transform_call_expr(expr: Expr, old_name: str, new_name: str) -> Optional[CallExpr]:
    """
    Transformation callback that replaces function call names.
    
    Args:
        expr: The expression to check
        old_name: The old function name to replace
        new_name: The new function name
    
    Returns:
        Modified CallExpr if this is a matching call, None otherwise
    """
    if isinstance(expr, CallExpr) and expr.fn_name == old_name:
        expr.fn_name = new_name
        return expr
    return None


def transform_calls_in_file(grug_file: GrugFile, old_name: str, new_name: str) -> GrugFile:
    """
    Replace all function calls with old_name to new_name in a GrugFile.
    
    This is a convenience function for the common use case of renaming
    unsafe function calls to safe versions.
    
    Args:
        grug_file: The GrugFile to transform
        old_name: The old function name (e.g., 'write')
        new_name: The new function name (e.g., 'write_safe')
    
    Returns:
        The transformed GrugFile
    
    Example:
        state = grug.init()
        file = state.compile_grug_file('mymod/example-Entity.grug')
        transform_calls_in_file(file, 'write', 'write_safe')
    """
    callback = lambda expr: transform_call_expr(expr, old_name, new_name)
    return visit_grug_file(grug_file, callback)


def transform_calls_in_dir(grug_dir: GrugDir, old_name: str, new_name: str) -> GrugDir:
    """
    Replace all function calls with old_name to new_name in a GrugDir.
    
    This recursively transforms all grug files in the directory tree.
    
    Args:
        grug_dir: The GrugDir to transform
        old_name: The old function name
        new_name: The new function name
    
    Returns:
        The transformed GrugDir
    
    Example:
        state = grug.init()
        mods = state.compile_all_mods()
        transform_calls_in_dir(mods, 'write', 'write_safe')
        write_dir_to_grug(mods, 'mods')
    """
    callback = lambda expr: transform_call_expr(expr, old_name, new_name)
    return visit_grug_dir(grug_dir, callback)


def grug_file_to_ast_dict(grug_file: GrugFile) -> List[Dict[str, Any]]:
    """
    Convert a GrugFile to a JSON-serializable dict representation.
    
    This creates an AST that can be serialized to JSON and then
    converted back to grug source code using Serializer.ast_to_grug().
    
    Args:
        grug_file: The GrugFile to convert
    
    Returns:
        A list of dict objects representing the AST
    """
    ast: Ast = []
    
    # Add global variables
    for var in grug_file.global_variables:
        ast.append(var)
    
    # Add on_fns and helper_fns in the order they appear in the file
    # We need to preserve the original order, but GrugFile stores them in dicts
    # For now, we'll add on_fns first, then helper_fns (as the parser requires)
    for fn_name, fn in grug_file.on_fns.items():
        ast.append(fn)
    
    for fn_name, fn in grug_file.helper_fns.items():
        ast.append(fn)
    
    # Serialize to JSON-serializable dict
    return [Serializer._serialize_global_statement(node) for node in ast]


def write_grug_file(grug_file: GrugFile, output_path: str) -> None:
    """
    Write a GrugFile back to a .grug file.
    
    Args:
        grug_file: The GrugFile to write
        output_path: The path to write the .grug file to
    """
    ast_dict = grug_file_to_ast_dict(grug_file)
    grug_text = Serializer.ast_to_grug(ast_dict)
    Path(output_path).write_text(grug_text)


def write_dir_to_grug(grug_dir: GrugDir, mods_dir_path: str) -> None:
    """
    Write all GrugFiles in a GrugDir back to .grug files.
    
    This recursively writes all transformed files back to their original
    locations (or new locations if mods_dir_path is different).
    
    Args:
        grug_dir: The GrugDir containing the GrugFiles
        mods_dir_path: The base directory path to write files to
    """
    # Write all files in this directory
    for file_path, grug_file in grug_dir.files.items():
        output_path = Path(mods_dir_path) / file_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        write_grug_file(grug_file, str(output_path))
    
    # Recursively write subdirectories
    for dir_name, sub_dir in grug_dir.dirs.items():
        write_dir_to_grug(sub_dir, mods_dir_path)


def find_all_calls(grug_dir: GrugDir, fn_name: str) -> List[tuple]:
    """
    Find all function calls with a given name in a GrugDir.
    
    This is useful for auditing unsafe function calls before transformation.
    
    Args:
        grug_dir: The GrugDir to search
        fn_name: The function name to find
    
    Returns:
        A list of tuples (file_path, fn_name, call_expr) for each matching call
    
    Example:
        state = grug.init()
        mods = state.compile_all_mods()
        unsafe_calls = find_all_calls(mods, 'write')
        for file_path, context, call in unsafe_calls:
            print(f'{file_path}: found write() call')
    """
    results: List[tuple] = []
    
    def find_in_file(grug_file: GrugFile):
        def finder(expr: Expr) -> Optional[Expr]:
            if isinstance(expr, CallExpr) and expr.fn_name == fn_name:
                results.append((grug_file.relative_path, expr))
            return None
        
        visit_grug_file(grug_file, finder)
    
    # Search all files
    for file_path, grug_file in grug_dir.files.items():
        find_in_file(grug_file)
    
    # Recursively search subdirectories
    for dir_name, sub_dir in grug_dir.dirs.items():
        results.extend(find_all_calls(sub_dir, fn_name))
    
    return results


def count_calls(grug_dir: GrugDir, fn_name: str) -> int:
    """
    Count the number of function calls with a given name in a GrugDir.
    
    Args:
        grug_dir: The GrugDir to search
        fn_name: The function name to count
    
    Returns:
        The number of matching calls
    """
    return len(find_all_calls(grug_dir, fn_name))