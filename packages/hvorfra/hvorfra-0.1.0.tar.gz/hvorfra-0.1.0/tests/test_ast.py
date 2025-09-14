from ast import AST, Assign, Call, ClassDef, FunctionDef, Module

from hvorfra import SELF, get_ast_path, get_caller_location


def test_get_ast_path() -> None:
    class A:
        def f(self) -> tuple[AST, ...]:
            location = get_caller_location(SELF)
            assert location is not None
            return get_ast_path(location)

    a = A()
    types = [type(n) for n in a.f()]
    assert types == [Module, FunctionDef, ClassDef, FunctionDef, Assign, Call]
