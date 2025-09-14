from __future__ import annotations

from enum import Enum

from hvorfra import get_assignment_name, get_ast_path, get_caller_location


class AssignmentNamed:
    def __init__(self) -> None:
        location = get_caller_location()
        assert location is not None
        path = get_ast_path(location)
        self.expr_name = get_assignment_name(path, include_exprs=True)
        self.stmt_name = get_assignment_name(path, include_exprs=False)

    def __add__(self, other: AssignmentNamed) -> AssignmentNamed:
        return other


def test_get_assignment_name__assign() -> None:
    a = AssignmentNamed()
    assert a.expr_name == "a"
    assert a.stmt_name == "a"


def test_get_assignment_name__assign_many() -> None:
    a = b = AssignmentNamed()
    assert a.expr_name is None
    assert a.stmt_name is None
    assert b.expr_name is None
    assert b.stmt_name is None


def test_get_assignment_name__ann_assign() -> None:
    b: AssignmentNamed = AssignmentNamed()
    assert b.expr_name == "b"
    assert b.stmt_name == "b"


def test_get_assignment_name__aug_assign() -> None:
    c = AssignmentNamed()
    c.expr_name = None
    c.stmt_name = None
    c += AssignmentNamed()
    assert c.expr_name == "c"
    assert c.stmt_name == "c"


def test_get_assignment_name__call() -> None:
    def f(kw: AssignmentNamed) -> AssignmentNamed:
        return kw

    a = f(kw=AssignmentNamed())

    assert a.expr_name == "kw"
    assert a.stmt_name == "a"


def test_get_assignment_name__dict() -> None:
    d = {"key": AssignmentNamed()}

    assert d["key"].expr_name == "key"
    assert d["key"].stmt_name == "d"


def test_get_assignment_name__class() -> None:
    class A:
        mem = AssignmentNamed()

    a = A()

    assert a.mem.expr_name == "mem"
    assert a.mem.stmt_name == "mem"


def test_get_assignment_name__enum() -> None:
    class En(Enum):
        I = AssignmentNamed()

    assert En.I.value.expr_name == "I"
    assert En.I.value.stmt_name == "I"


def test_get_assignment_name__attribute() -> None:
    class A:
        mem: AssignmentNamed

    a = A()
    a.mem = AssignmentNamed()

    assert a.mem.expr_name == "mem"
    assert a.mem.stmt_name == "mem"


def test_get_assignment_name__subscript() -> None:
    l: list[AssignmentNamed | None] = [None]

    l[0] = AssignmentNamed()

    assert l[0]
    assert l[0].expr_name == "l"
    assert l[0].stmt_name == "l"


def test_get_assignment_name__list() -> None:
    [l] = [AssignmentNamed()]

    assert l.expr_name is None
    assert l.stmt_name is None


def test_get_assignment_name__tuple() -> None:
    (t,) = [AssignmentNamed()]

    assert t.expr_name is None
    assert t.stmt_name is None
