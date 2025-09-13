from functools import lru_cache
import math as m
from collections import Counter
from typing import Sequence, Union, List

Numeric = Union[int, float]


def mean(values: List[Numeric]) -> float:
    """
    Calculate the mean (average) of a List of numbers.

    Args:
        values (List[int, float]): A List of integers or floats.

    Returns:
        float: The mean of the List.

    Raises:
        ValueError: If the input List is empty.
    """
    if not values:
        raise ValueError("Must contain at least one data point")

    return sum(values) / len(values)


def median(values: List[Numeric]) -> float:
    """
    Calculate the median of a List of numbers.

    Args:
        values (List[Union[int float]]): A List of integers or floats.

    Returns:
        float: The median of the List.

    Raises:
        ValueError: If the input List is empty.
    """
    if not values:
        raise ValueError("Must contain at least one data point")

    values = sorted(values)
    length: int = len(values)
    mid: int = length // 2

    if length % 2 == 1:
        return float(values[mid])
    else:
        return (values[mid - 1] + values[mid]) / 2


def mode(values: List[Numeric]) -> Union[Numeric, List[Numeric]]:
    """
    Compute the mode(s) of a List of numeric values.

    If multiple numbers have the same highest frequency,
    all such numbers are returned as a List.
    If only one number has the highest frequency, that single value is
    returned.

    Args:
        values (List[Union[int, float]]): A List of integers or floats.

    Returns:
        Union[int, float, List[Union[int, float]]]:
            The mode of the List. Returns a single value if there's one mode,
            or a List of values if multiple modes exist.

    Raises:
        ValueError: If the input List is empty.
    """
    if not values:
        raise ValueError("Must contain at least one data point")

    frequency = Counter(values)
    highest: Numeric = max(frequency.values())
    modes: List[Numeric] = [
        number for number, count in frequency.items() if count == highest
    ]

    return modes[0] if len(modes) == 1 else modes


def variance(values: Sequence[Numeric]) -> float:
    """
    Work out the variance of the given List of numbers(sample).

    Args:
        values (List[Union[int, float]]): a List of floats or integers.

    Returns:
        float: The variance of the List.
    """
    if not values:
        raise ValueError("Must contain at least one data point")
    mean_val = sum(values) / len(values)
    return sum((x - mean_val) ** 2 for x in values) / (len(values) - 1)


def std_dev(values: Sequence[Numeric]) -> float:
    """
    determine the standard deviation of the given List of number(sample).

    Args:
        values (List[Union[int, float]]): a List of floats or integers.

    Returns:
        float: The standard deviation of the List.
    """
    return m.sqrt(variance(values))


def pvariance(values: Sequence[Numeric]) -> float:
    """
    Work out the variance of the given List of numbers(population).

    Args:
        values (List[Union[int, float]]): a List of floats or integers.

    Returns:
        float: The variance of the List.
    """
    if not values:
        raise ValueError("Must contain at least one data point")

    mean_val = sum(values) / len(values)
    return sum((x - mean_val) ** 2 for x in values) / (len(values))


def pstd_dev(values: Sequence[Numeric]) -> float:
    """
    Determine the standard deviation of the given List of numbers(population).

    Args:
        values (List[Union[int, float]]): a List of floats or integers.

    Returns:
        float: The standard deviation of the List.
    """
    return m.sqrt(variance(values))
