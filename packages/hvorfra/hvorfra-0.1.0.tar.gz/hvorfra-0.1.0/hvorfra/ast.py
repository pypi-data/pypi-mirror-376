from ast import AST, Module, expr, parse, stmt
from functools import singledispatch
from pathlib import Path
from typing import Any

from hvorfra.types import AstPath, CodeLocation, cache


@cache
def get_ast(path: Path) -> Module:
    return parse(path.read_text(), str(path))


@singledispatch
def _find_node(ast: Any, location: CodeLocation, result: list[AST]) -> bool:
    raise TypeError("Unknown type of AST.", ast)


@_find_node.register
def _find_node__ast(ast: AST, location: CodeLocation, result: list[AST]) -> bool:
    line: int | None = None
    end_line: int | None = None
    column: int | None = None
    if isinstance(ast, stmt | expr):
        line = ast.lineno
        end_line = ast.end_lineno
        column = ast.col_offset

    # Optimization: Don't recurse into sub-trees we already know are out-of-bounds.
    if ((end_line is not None) and (end_line < location.line)) or (
        (line is not None) and (location.line < line)
    ):
        return False

    result.append(ast)

    if line == location.line and column == location.column:
        return True

    for field in ast._fields:
        found = _find_node(getattr(ast, field), location, result)
        if found:
            return True

    result.pop()
    return False


@_find_node.register(list)
def _find_node__list(ast: list[Any], location: CodeLocation, result: list[AST]) -> bool:
    for item in ast:
        found = _find_node(item, location, result)
        if found:
            return True
    return False


@_find_node.register
def _find_node__primitive(
    ast: bool | float | int | str | None,  # noqa: PYI041
    location: CodeLocation,
    result: list[AST],
) -> bool:
    return False


@cache
def get_ast_path(location: CodeLocation) -> AstPath:
    ast = get_ast(location.path)
    result: list[AST] = []
    assert _find_node(ast, location, result)
    return tuple(result)
