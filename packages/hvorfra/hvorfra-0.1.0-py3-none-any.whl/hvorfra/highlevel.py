from dataclasses import dataclass
from functools import cache, cached_property

from hvorfra.assignment import get_assignment_name
from hvorfra.ast import get_ast_path
from hvorfra.scope import get_scope_name_parts
from hvorfra.stack import get_caller_location
from hvorfra.types import PARENT, CodeLocation


@dataclass(frozen=True)
class Names:
    module_name: str
    qualname_parts: tuple[str, ...]

    @property
    def name(self) -> str:
        return self.qualname_parts[-1]

    @cached_property
    def qualname(self) -> str:
        return ".".join(self.qualname_parts)

    @cached_property
    def full_name(self) -> str:
        return f"{self.module_name}.{self.qualname}"


@cache
def _get_scope_names(location: CodeLocation | None) -> Names | None:
    if location is None or location.module_name is None:
        return None
    ast_path = get_ast_path(location)
    scope_name_parts = get_scope_name_parts(ast_path)
    if scope_name_parts is None:
        return None
    return Names(location.module_name, scope_name_parts)


def get_scope_names(depth: int = PARENT) -> Names | None:
    return _get_scope_names(get_caller_location(depth + 1))


def scope_module_name(depth: int = PARENT) -> str:
    names = get_scope_names(depth + 1)
    assert names is not None
    return names.module_name


def scope_name(depth: int = PARENT) -> str:
    names = get_scope_names(depth + 1)
    assert names is not None
    return names.name


def scope_qualname(depth: int = PARENT) -> str:
    names = get_scope_names(depth + 1)
    assert names is not None
    return names.qualname


def scope_full_name(depth: int = PARENT) -> str:
    names = get_scope_names(depth + 1)
    assert names is not None
    return names.full_name


@cache
def _get_assignment_names(location: CodeLocation | None) -> Names | None:
    if location is None or location.module_name is None:
        return None
    ast_path = get_ast_path(location)
    scope_name_parts = get_scope_name_parts(ast_path)
    if scope_name_parts is None:
        return None
    assignment_name = get_assignment_name(ast_path)
    if assignment_name is None:
        return None
    return Names(location.module_name, (*scope_name_parts, assignment_name))


def get_assignment_names(depth: int = PARENT) -> Names | None:
    return _get_assignment_names(get_caller_location(depth + 1))


def assignment_module_name(depth: int = PARENT) -> str:
    names = get_assignment_names(depth + 1)
    assert names is not None
    return names.module_name


def assignment_name(depth: int = PARENT) -> str:
    names = get_assignment_names(depth + 1)
    assert names is not None
    return names.name


def assignment_qualname(depth: int = PARENT) -> str:
    names = get_assignment_names(depth + 1)
    assert names is not None
    return names.qualname


def assignment_full_name(depth: int = PARENT) -> str:
    names = get_assignment_names(depth + 1)
    assert names is not None
    return names.full_name
