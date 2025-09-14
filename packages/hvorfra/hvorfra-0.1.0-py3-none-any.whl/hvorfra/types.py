from ast import AST
from collections.abc import Callable
from functools import cache as ft_cache
from pathlib import Path
from typing import Any, NamedTuple

SELF = 0
PARENT = 1


class CodeLocation(NamedTuple):
    module_name: str | None
    path: Path
    line: int
    column: int


type AstPath = tuple[AST, ...]


def cache[C: Callable[..., Any]](f: C) -> C:
    return ft_cache(f)  # type: ignore[return-value]
