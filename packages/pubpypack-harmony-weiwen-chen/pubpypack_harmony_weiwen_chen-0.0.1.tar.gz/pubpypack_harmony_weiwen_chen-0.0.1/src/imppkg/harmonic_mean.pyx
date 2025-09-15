from collections.abc import Sequence


def harmonic_mean(nums: Sequence[float]) -> float:
    return len(nums) / sum(
        1 / num for num in nums
    )
