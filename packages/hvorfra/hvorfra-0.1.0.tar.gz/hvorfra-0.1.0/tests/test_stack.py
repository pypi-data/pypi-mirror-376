from pathlib import Path

import pytest

from hvorfra import PARENT, SELF, CodeLocation, get_caller_location

MODULE = "tests.test_stack"
PATH = Path(__file__)
BASE_LINE = 22


@pytest.mark.parametrize(
    "depth,expected",
    [
        (SELF, CodeLocation(MODULE, PATH, BASE_LINE + 2, 15)),
        (PARENT, CodeLocation(MODULE, PATH, BASE_LINE + 7, 23)),
        (2, CodeLocation(MODULE, PATH, BASE_LINE + 9, 19)),
        (3, CodeLocation(MODULE, PATH, BASE_LINE + 13, 11)),
        (10_000, None),
    ],
)
def test_get_caller_location(depth: int, expected: CodeLocation | None) -> None:
    def f(depth: int) -> CodeLocation | None:
        return get_caller_location(depth)

    class A:
        def f(self, depth: int) -> CodeLocation | None:
            def g(d: int) -> CodeLocation | None:
                return f(d)

            return g(depth)

    a = A()

    assert a.f(depth) == expected
