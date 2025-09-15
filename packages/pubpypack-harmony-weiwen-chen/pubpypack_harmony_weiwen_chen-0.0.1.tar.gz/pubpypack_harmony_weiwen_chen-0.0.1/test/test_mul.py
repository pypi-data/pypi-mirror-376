import operator

import pytest


@pytest.mark.parametrize(
    "input_one, input_two, expected",
    (
        (2, 3, 6),
        (-2, 3, -6),
        (-2, -3, 6),
        (0, 3, 0),
    ),
)
def test_mul(input_one: int, input_two: int, expected: int) -> None:
    assert operator.mul(input_one, input_two) == expected
