import sys
from collections.abc import Iterable

import termcolor

from imppkg.harmonic_mean import harmonic_mean


def main() -> None:
    nums = _parse_nums(sys.argv[1:])
    result = _calculate_results(nums)
    output = _format_output(result)
    print(output)


def _parse_nums(inputs: Iterable[str]) -> list[float]:
    try:
        return [float(x) for x in inputs]
    except ValueError:
        return []


def _calculate_results(nums: list[float]) -> float:
    try:
        return harmonic_mean(nums)
    except ZeroDivisionError:
        return 0.0


def _format_output(result: float) -> str:
    return termcolor.colored(
        str(result),
        color="red",
        on_color="on_cyan",
        attrs=("bold",),
    )
