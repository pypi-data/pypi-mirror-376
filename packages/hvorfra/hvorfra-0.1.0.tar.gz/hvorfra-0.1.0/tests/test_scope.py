from hvorfra import LOCALS_STR, get_ast_path, get_caller_location, get_scope_name_parts


def assert_get_name_parts(qualname: str | None, expected: tuple[str, ...]) -> int:
    location = get_caller_location()
    assert location is not None
    path = get_ast_path(location)
    parts = get_scope_name_parts(path)
    assert parts is not None

    assert parts == expected

    if qualname is not None:
        qualname_parts = parts
        while qualname_parts[-1] == LOCALS_STR:
            qualname_parts = qualname_parts[:-1]
        assert ".".join(qualname_parts) == qualname

    return 42


def test_get_scope_name_parts() -> None:
    assert_get_name_parts(
        test_get_scope_name_parts.__qualname__, ("test_get_scope_name_parts", LOCALS_STR)
    )


def test_get_scope_name_parts__inner() -> None:
    def f() -> None:
        assert_get_name_parts(
            f.__qualname__, ("test_get_scope_name_parts__inner", LOCALS_STR, "f", LOCALS_STR)
        )

    f()


def test_get_scope_name_parts__class() -> None:
    class A:
        name_parts = assert_get_name_parts(
            None, ("test_get_scope_name_parts__class", LOCALS_STR, "A")
        )


def test_get_scope_name_parts__method() -> None:
    class A:
        def m(self) -> None:
            assert_get_name_parts(
                self.m.__qualname__,
                ("test_get_scope_name_parts__method", LOCALS_STR, "A", "m", LOCALS_STR),
            )

    A().m()


def test_get_scope_name_parts__deep() -> None:
    def f() -> None:
        class A:
            class B:
                def m(self) -> None:
                    def g() -> None:
                        assert_get_name_parts(
                            g.__qualname__,
                            (
                                "test_get_scope_name_parts__deep",
                                LOCALS_STR,
                                "f",
                                LOCALS_STR,
                                "A",
                                "B",
                                "m",
                                LOCALS_STR,
                                "g",
                                LOCALS_STR,
                            ),
                        )

                    g()

        A.B().m()

    f()
