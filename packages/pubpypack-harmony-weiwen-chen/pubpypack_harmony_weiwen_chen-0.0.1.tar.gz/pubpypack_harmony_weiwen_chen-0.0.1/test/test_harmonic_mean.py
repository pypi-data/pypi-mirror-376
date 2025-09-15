import sys

import pytest
import termcolor

from imppkg.harmony import main


@pytest.mark.parametrize(
    "inputs, expected",
    (
        (
            [
                "3",
                "3",
                "3",
            ],
            3.0,
        ),
        ([], 0.0),
        (["foo", "bar"], 0.0),
    ),
)
def test_harmony(inputs: list[str], monkeypatch, capsys, expected: float):
    monkeypatch.setattr(sys, "argv", ["harmony"] + inputs)

    main()

    assert capsys.readouterr().out.strip() == termcolor.colored(
        str(expected),
        color="red",
        on_color="on_cyan",
        attrs=("bold",),
    )


# FRUITS = ['apple',]


# def test_len() -> None:
#     assert len(FRUITS) == 1


# def test_append() -> None:
#     FRUITS.append('banana')
#     assert FRUITS == ['apple', 'banana',]
