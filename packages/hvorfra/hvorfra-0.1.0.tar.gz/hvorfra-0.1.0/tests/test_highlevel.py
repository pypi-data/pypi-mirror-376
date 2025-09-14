from hvorfra import (
    LOCALS_STR,
    SELF,
    Names,
    assignment_full_name,
    assignment_module_name,
    assignment_name,
    assignment_qualname,
    get_assignment_names,
    get_scope_names,
    scope_full_name,
    scope_module_name,
    scope_name,
    scope_qualname,
)

_SCOPE_NAMES = get_scope_names(SELF)
_VAR_NAMES = get_assignment_names(SELF)


def test_names() -> None:
    names = Names("my.module", ("some", "name", "parts"))
    assert names.module_name == "my.module"
    assert names.name == "parts"
    assert names.qualname == "some.name.parts"
    assert names.full_name == "my.module.some.name.parts"


def test_get_scope_names() -> None:
    scope_names = get_scope_names(SELF)

    class Inner:
        scope_names = get_scope_names(SELF)

        def method(self) -> Names | None:
            return get_scope_names(SELF)

    inner = Inner()

    assert Names("tests.test_highlevel", ()) == _SCOPE_NAMES
    assert scope_names == Names("tests.test_highlevel", ("test_get_scope_names", LOCALS_STR))
    assert inner.scope_names == Names(
        "tests.test_highlevel", ("test_get_scope_names", LOCALS_STR, "Inner")
    )
    assert inner.method() == Names(
        "tests.test_highlevel", ("test_get_scope_names", LOCALS_STR, "Inner", "method", LOCALS_STR)
    )


def test_scope_module_name() -> None:
    assert scope_module_name(SELF) == "tests.test_highlevel"


def test_scope_name() -> None:
    assert scope_name(SELF) == LOCALS_STR


def test_scope_qualname() -> None:
    assert scope_qualname(SELF) == "test_scope_qualname.<locals>"


def test_scope_full_name() -> None:
    assert scope_full_name(SELF) == "tests.test_highlevel.test_scope_full_name.<locals>"


def test_get_assignment_names() -> None:
    var_names_1 = get_assignment_names(SELF)

    class Inner:
        var_names_2 = get_assignment_names(SELF)

        def method(self) -> Names | None:
            var_names_3 = get_assignment_names(SELF)
            return var_names_3  # NOQA: RET504

    inner = Inner()

    assert Names("tests.test_highlevel", ("_VAR_NAMES",)) == _VAR_NAMES
    assert var_names_1 == Names(
        "tests.test_highlevel", ("test_get_assignment_names", LOCALS_STR, "var_names_1")
    )
    assert inner.var_names_2 == Names(
        "tests.test_highlevel", ("test_get_assignment_names", LOCALS_STR, "Inner", "var_names_2")
    )
    assert inner.method() == Names(
        "tests.test_highlevel",
        ("test_get_assignment_names", LOCALS_STR, "Inner", "method", LOCALS_STR, "var_names_3"),
    )


def test_assignment_module_name() -> None:
    a = assignment_module_name(SELF)
    assert a == "tests.test_highlevel"


def test_assignment_name() -> None:
    a = assignment_name(SELF)
    assert a == "a"


def test_assignment_qualname() -> None:
    a = assignment_qualname(SELF)
    assert a == "test_assignment_qualname.<locals>.a"


def test_assignment_full_name() -> None:
    a = assignment_full_name(SELF)
    assert a == "tests.test_highlevel.test_assignment_full_name.<locals>.a"
