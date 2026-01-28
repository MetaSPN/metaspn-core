"""Statistical utilities for MetaSPN."""

import math
from typing import Optional, Union


def mean(values: list[Union[int, float]]) -> float:
    """Calculate arithmetic mean.

    Args:
        values: List of numeric values

    Returns:
        Mean value, or 0.0 if list is empty
    """
    if not values:
        return 0.0
    return sum(values) / len(values)


def std_dev(
    values: list[Union[int, float]],
    population: bool = True,
) -> float:
    """Calculate standard deviation.

    Args:
        values: List of numeric values
        population: If True, calculate population std dev (N),
                   else sample std dev (N-1)

    Returns:
        Standard deviation, or 0.0 if insufficient values
    """
    if not values:
        return 0.0

    n = len(values)
    if n < 2:
        return 0.0

    avg = mean(values)
    variance = sum((x - avg) ** 2 for x in values)

    divisor = n if population else (n - 1)
    return math.sqrt(variance / divisor)


def variance(
    values: list[Union[int, float]],
    population: bool = True,
) -> float:
    """Calculate variance.

    Args:
        values: List of numeric values
        population: If True, population variance, else sample variance

    Returns:
        Variance
    """
    std = std_dev(values, population)
    return std**2


def percentile(
    values: list[Union[int, float]],
    p: float,
) -> float:
    """Calculate percentile value.

    Args:
        values: List of numeric values
        p: Percentile (0-100)

    Returns:
        Value at given percentile
    """
    if not values:
        return 0.0

    if p < 0 or p > 100:
        raise ValueError("Percentile must be between 0 and 100")

    sorted_vals = sorted(values)
    n = len(sorted_vals)

    # Linear interpolation method
    k = (n - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)

    if f == c:
        return sorted_vals[int(k)]

    return sorted_vals[int(f)] * (c - k) + sorted_vals[int(c)] * (k - f)


def median(values: list[Union[int, float]]) -> float:
    """Calculate median value.

    Args:
        values: List of numeric values

    Returns:
        Median value
    """
    return percentile(values, 50)


def normalize(
    values: list[Union[int, float]],
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
) -> list[float]:
    """Normalize values to 0-1 range.

    Args:
        values: List of numeric values
        min_val: Minimum value for normalization (default: min of values)
        max_val: Maximum value for normalization (default: max of values)

    Returns:
        List of normalized values
    """
    if not values:
        return []

    if min_val is None:
        min_val = min(values)
    if max_val is None:
        max_val = max(values)

    value_range = max_val - min_val
    if value_range == 0:
        return [0.5] * len(values)

    return [(v - min_val) / value_range for v in values]


def z_score(
    values: list[Union[int, float]],
) -> list[float]:
    """Calculate z-scores for values.

    Args:
        values: List of numeric values

    Returns:
        List of z-scores
    """
    if not values or len(values) < 2:
        return [0.0] * len(values)

    avg = mean(values)
    std = std_dev(values)

    if std == 0:
        return [0.0] * len(values)

    return [(v - avg) / std for v in values]


def moving_average(
    values: list[Union[int, float]],
    window: int = 3,
) -> list[float]:
    """Calculate simple moving average.

    Args:
        values: List of numeric values
        window: Window size for averaging

    Returns:
        List of moving averages (same length, with early values averaged over smaller windows)
    """
    if not values:
        return []

    result = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        window_values = values[start : i + 1]
        result.append(mean(window_values))

    return result


def exponential_moving_average(
    values: list[Union[int, float]],
    alpha: float = 0.3,
) -> list[float]:
    """Calculate exponential moving average.

    Args:
        values: List of numeric values
        alpha: Smoothing factor (0 < alpha <= 1)

    Returns:
        List of EMA values
    """
    if not values:
        return []

    if not 0 < alpha <= 1:
        raise ValueError("Alpha must be between 0 and 1")

    result = [values[0]]
    for i in range(1, len(values)):
        ema = alpha * values[i] + (1 - alpha) * result[-1]
        result.append(ema)

    return result


def linear_regression(
    x: list[Union[int, float]],
    y: list[Union[int, float]],
) -> tuple[float, float]:
    """Calculate simple linear regression.

    Args:
        x: Independent variable values
        y: Dependent variable values

    Returns:
        Tuple of (slope, intercept)
    """
    if len(x) != len(y):
        raise ValueError("x and y must have same length")

    n = len(x)
    if n < 2:
        return (0.0, mean(y) if y else 0.0)

    x_mean = mean(x)
    y_mean = mean(y)

    numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

    if denominator == 0:
        return (0.0, y_mean)

    slope = numerator / denominator
    intercept = y_mean - slope * x_mean

    return (slope, intercept)


def clamp(
    value: Union[int, float],
    min_val: Union[int, float],
    max_val: Union[int, float],
) -> Union[int, float]:
    """Clamp a value to a range.

    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value

    Returns:
        Clamped value
    """
    return max(min_val, min(max_val, value))
