"""
Sequential scan operations used as the baseline comparison in the project.

This module models the simplest possible database access pattern: linear scans
through a list of row dictionaries, without any auxiliary index structures.
"""

from __future__ import annotations

from time import perf_counter
from typing import Any

from src.common.operator import Operator


Row = dict[str, Any]


def search(data: list[Row], field: str, operator: Operator, value: Any) -> list[Row]:
    """Return every row whose field matches the supplied comparison predicate."""
    matches: list[Row] = []

    for row in data:
        if operator(row[field], value):
            matches.append(row)

    return matches


def search_all(file_path: str, data: list[Row], field: str, operator: Operator, value: Any) -> list[float]:
    """Benchmark repeated sequential searches while preserving the legacy API shape."""
    del file_path

    timings_us: list[float] = []

    for _ in data:
        start = perf_counter()

        search(
            data=data,
            field=field,
            operator=operator,
            value=value,
        )

        end = perf_counter()
        timings_us.append((end - start) * 1_000_000)

    return timings_us


def insert_all(data: list[Row]) -> tuple[list[float], list[Row]]:
    """Benchmark appending rows to the in-memory list used as the baseline storage."""
    timings_us: list[float] = []
    stored_data: list[Row] = []

    for row in data:
        start = perf_counter()

        stored_data.append(row)

        end = perf_counter()
        timings_us.append((end - start) * 1_000_000)

    return timings_us, stored_data


def update_all(file_path: str, data: list[Row], field: str, value: Any) -> tuple[list[float], list[Row]]:
    """Benchmark updates across rows that match the requested field comparison."""
    del file_path

    timings_us: list[float] = []

    for row in data:
        start = perf_counter()

        if row[field] == value:
            row["pm25"] = 0.0
            row["pm10"] = 0.0

        end = perf_counter()
        timings_us.append((end - start) * 1_000_000)

    return timings_us, data


def delete_all(data: list[Row]) -> list[float]:
    """Benchmark deletions by removing rows from the list until it is empty."""
    timings_us: list[float] = []

    while data:
        start = perf_counter()

        data.pop()

        end = perf_counter()
        timings_us.append((end - start) * 1_000_000)

    return timings_us