from ast import AsyncFunctionDef, ClassDef, FunctionDef

from hvorfra.types import AstPath

LOCALS_STR = "<locals>"


def get_scope_name_parts(path: AstPath) -> tuple[str, ...] | None:
    result: list[str] = []
    for part in path:
        if isinstance(part, FunctionDef | AsyncFunctionDef):
            result.extend((part.name, LOCALS_STR))
        if isinstance(part, ClassDef):
            result.append(part.name)

    return tuple(result)
