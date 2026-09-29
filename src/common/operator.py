"""Shared comparison operators used by the search and filter routines."""

from enum import Enum
import operator


class Operator(Enum):
    """Enum mapping logical comparisons to their Python operator implementations."""

    EQUALS = operator.eq
    LESS = operator.lt
    GREATER = operator.gt
    LESS_EQUALS = operator.le
    GREATER_EQUALS = operator.ge
    NOT_EQUALS = operator.ne

    def __call__(self, x, y):
        """Apply the stored comparison function to two values.

        Example:
            Operator.EQUALS(3, 3) -> True
        """
        return self.value(x, y)