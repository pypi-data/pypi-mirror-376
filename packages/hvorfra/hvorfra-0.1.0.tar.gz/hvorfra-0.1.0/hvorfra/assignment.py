from ast import (
    AST,
    AnnAssign,
    Assign,
    Attribute,
    AugAssign,
    Constant,
    Dict,
    List,
    Name,
    Subscript,
    Tuple,
    keyword,
)
from functools import singledispatch

from hvorfra.types import AstPath, cache

STMT_ASSIGNMENT_TYPES = (Assign, AnnAssign, AugAssign)
EXPR_ASSIGNMENT_TYPES = (keyword, Dict)


@cache
def get_assignment_index(path: AstPath, *, include_exprs: bool = True) -> int | None:
    types: tuple[type[AST], ...]
    if include_exprs:
        types = (*STMT_ASSIGNMENT_TYPES, *EXPR_ASSIGNMENT_TYPES)
    else:
        types = STMT_ASSIGNMENT_TYPES

    for i in range(len(path), 0, -1):
        if isinstance(path[i - 1], types):
            return i - 1

    return None


@singledispatch
def _get_name(ast: AST, path: AstPath, index: int) -> str | None:
    raise TypeError("Don't know how to extract name from node.", ast)


@_get_name.register
def _get_name__assign(ast: Assign, path: AstPath, index: int) -> str | None:
    names = {_get_name(t, path, index) for t in ast.targets}
    if len(names) != 1:
        return None
    (name,) = names
    return name


@_get_name.register
def _get_name__aug_assign(ast: AugAssign, path: AstPath, index: int) -> str | None:
    return _get_name(ast.target, path, index)


@_get_name.register
def _get_name__ann_assign(ast: AnnAssign, path: AstPath, index: int) -> str | None:
    return _get_name(ast.target, path, index)


@_get_name.register
def _get_name__keyword(ast: keyword, path: AstPath, index: int) -> str | None:
    return ast.arg


@_get_name.register
def _get_name__dict(ast: Dict, path: AstPath, index: int) -> str | None:
    for key, value in zip(ast.keys, ast.values, strict=False):
        if key and (value is path[index + 1]):
            return _get_name(key, path, index)
    return None


@_get_name.register
def _get_name__attribute(ast: Attribute, path: AstPath, index: int) -> str | None:
    return ast.attr


@_get_name.register
def _get_name__subscript(ast: Subscript, path: AstPath, index: int) -> str | None:
    return _get_name(ast.value, path, index)


@_get_name.register
def _get_name__list(ast: List, path: AstPath, index: int) -> str | None:
    return None


@_get_name.register
def _get_name__tuple(ast: Tuple, path: AstPath, index: int) -> str | None:
    return None


@_get_name.register
def _get_name__constant(ast: Constant, path: AstPath, index: int) -> str | None:
    return ast.value if isinstance(ast.value, str) else None


@_get_name.register
def _get_name__name(ast: Name, path: AstPath, index: int) -> str | None:
    return ast.id


@cache
def get_assignment_name(path: AstPath, *, include_exprs: bool = True) -> str | None:
    index = get_assignment_index(path, include_exprs=include_exprs)
    if index is None:
        return None
    return _get_name(path[index], path, index)
