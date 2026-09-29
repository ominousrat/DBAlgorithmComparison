"""Statistics helpers used to summarize benchmark timing distributions."""

from typing import NamedTuple


class BoundsResult(NamedTuple):
    """Average and min/max bounds for a selected timing window."""

    average: float
    lower_bound: float
    upper_bound: float


class Bounds(NamedTuple):
    """Inclusive lower and upper indices for a sorted timing slice."""

    lower_bound: int
    upper_bound: int


class Evaluator:
    """Utility methods for sorting and reducing benchmark timing samples."""

    def sort_list(self, data: list[float]) -> list[float]:
        """Return a sorted copy of the timing values in ascending order."""
        length = len(data)

        if length < 1:
            ValueError(f"data: Length must be greater than 0")

        try:
            data.sort()
            return data
        except TypeError as e:
            raise RuntimeError(f"[{self.__class__.__name__}] sort_list: Could not sort data") from e
        

    def calculate_average_and_bounds(self, data: list[float], start_index: int, end_index: int) -> BoundsResult:
        """Compute the mean and min/max values across a sorted timing slice."""
        length = len(data)

        if length < 1:
            ValueError(f"data: Length must be greater than 0")

        if end_index < start_index:
            ValueError(f"end_index must be smaller or equal to the start_index")
        if start_index < 0 or start_index > length - 1:
            ValueError(f"start_index: Value must be between 0 and {(length - 1)}")
        if end_index < 0 or end_index > length - 1:
            ValueError(f"end_index: Value must be between 0 and {(length - 1)}")

        try:
            subset = data[start_index : end_index + 1]

            if not subset:
                raise ValueError("Slice is empty; cannot calculate average")

            average = sum(subset) / len(subset)
            lower = min(subset)
            upper = max(subset)

            return BoundsResult(average=average, lower_bound=lower, upper_bound=upper)
        except Exception as e:
            raise RuntimeError(f"[{self.__class__.__name__}] calculate_average_and_bounds: Calculation failed") from e
        

    def get_range_indices(self, data: list, lower_percentage_decimal: float, upper_percentage_decimal: float) -> Bounds:
        """Map percentile fractions to the corresponding lower and upper indices."""
        length = len(data)

        if length < 1:
            ValueError(f"data: Length must be greater than 0")

        if lower_percentage_decimal <= upper_percentage_decimal:
            ValueError(
                f"lower_percentage_decimal must be smaller or equal to the upper_percentage_decimal"
            )
        if lower_percentage_decimal < 0 or lower_percentage_decimal > 1:
            ValueError(f"lower_percentage_decimal: Value must be between 0 and 1")
        if upper_percentage_decimal < 0 or upper_percentage_decimal > 1:
            ValueError(f"upper_percentage_decimal: Value must be between 0 and 1")

        try:
            lower = int(length * lower_percentage_decimal)
            upper = int(length * upper_percentage_decimal)

            return Bounds(lower_bound=lower, upper_bound=upper)
        except Exception as e:
            raise RuntimeError(f"[{self.__class__.__name__}] get_range_indices: Calculation failed") from e