from enum import Enum
from pathlib import Path

from bunnets import coerce_params, typed


def test_coerce():
    # Tests that arguments are successfully coerced
    @coerce_params((0, bool))
    def inner_test(cast_to_bool):
        return cast_to_bool

    out = inner_test("yeah")

    assert out is True
    assert isinstance(out, bool)


def test_hinted_coerce():
    @typed
    def inner_test_simple(p: Path, i: int) -> None:
        assert isinstance(p, Path)
        assert isinstance(i, int)

    class inner_enum(Enum):
        Thing = "asdf"
        NotThing = "fdsa"

    @typed
    def inner_test_complex(p: inner_enum | str, i: list[inner_enum | int]) -> int:
        assert isinstance(p, str)
        assert len(i) == 3
        assert isinstance(i, list)
        assert isinstance(i[0], int)
        assert isinstance(i[1], inner_enum)
        assert isinstance(i[2], int)
        assert i[0] == 2
        assert i[2] == 9
        assert i[1] == inner_enum.Thing
        return str(len(i))

    inner_test_simple("/", "3")
    assert inner_test_complex(3, i=("2", "asdf", "9")) == 3
