"""Benchmark orchestration utilities for timing database operations."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from src.benchmarks.config import AppConfig
from src.benchmarks.memory_monitor import MemoryMonitor, MemoryStats
from src.common.csv_handler import write_all_lines
from src.common.evaluator import Evaluator


T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """Computed statistics for a benchmarked operation."""

    operation: str
    average_us: float
    lower_bound_us: float
    upper_bound_us: float


class BenchmarkRunner:
    """Run benchmark scenarios, collect timings, and persist the results."""

    def __init__(
        self,
        config: AppConfig,
        evaluator: Evaluator | None = None,
    ) -> None:
        """Create a runner bound to a configuration and result evaluator."""
        self.config = config
        self.evaluator = evaluator or Evaluator()

    def run(
        self,
        operation: str,
        function: Callable[[], list[float]],
    ) -> BenchmarkResult:
        """Execute one operation, capture timings, and summarize the distribution."""
        monitor = MemoryMonitor(
            output_path=(
                self.config.result_path
                / "memory"
                / f"{operation}.csv"
            )
        )

        monitor.start()

        try:
            timings_us = function()
        finally:
            monitor.stop()

        self._validate_timings(operation, timings_us)
        monitor.set_expected_sample_count(len(timings_us))
        monitor.join()

        sorted_timings = self.evaluator.sort_list(timings_us.copy())
        self._write_sorted_timings(operation, sorted_timings)

        memory_stats = monitor.calculate_stats(
            self.config.lower_fraction,
            self.config.upper_fraction,
        )
        result = self._calculate_result(operation, sorted_timings)

        self._print_memory_result(operation, memory_stats)
        self._print_result(result)

        return result

    def run_with_setup(
        self,
        operation: str,
        setup: Callable[[], T],
        function: Callable[[T], list[float]],
    ) -> BenchmarkResult:
        """Run an operation after creating a fresh state, excluding setup overhead."""
        state = setup()

        return self.run(
            operation,
            lambda: function(state),
        )

    def _calculate_result(
        self,
        operation: str,
        sorted_timings_us: list[float],
    ) -> BenchmarkResult:
        """Convert sorted timing samples into summary statistics for reporting."""
        if not sorted_timings_us:
            raise ValueError(
                f"Operation '{operation}' returned no timing values"
            )

        indices = self.evaluator.get_range_indices(
            sorted_timings_us,
            self.config.lower_fraction,
            self.config.upper_fraction,
        )

        stats = self.evaluator.calculate_average_and_bounds(
            sorted_timings_us,
            indices.lower_bound,
            indices.upper_bound,
        )

        return BenchmarkResult(
            operation=operation,
            average_us=stats.average,
            lower_bound_us=stats.lower_bound,
            upper_bound_us=stats.upper_bound,
        )

    def _validate_timings(
        self,
        operation: str,
        timings_us: list[float],
    ) -> None:
        """Ensure the measured timings have a valid shape and non-negative values."""
        if not isinstance(timings_us, list):
            raise TypeError(
                f"Operation '{operation}' must return list[float], "
                f"got {type(timings_us).__name__}"
            )

        if not timings_us:
            raise ValueError(
                f"Operation '{operation}' returned an empty timing list"
            )

        invalid_values = [
            value
            for value in timings_us
            if not isinstance(value, int | float)
            or isinstance(value, bool)
            or value < 0
        ]

        if invalid_values:
            raise ValueError(
                f"Operation '{operation}' returned invalid timing values: "
                f"{invalid_values[:5]}"
            )


    def _write_sorted_timings(
        self,
        operation: str,
        timings_us: list[float],
    ) -> None:
        """Save the sorted timing samples to a CSV file."""
        path = (
            self.config.result_path
            / "times"
            / f"{operation}.csv"
        )

        write_all_lines(str(path), timings_us)

    def _print_result(
        self,
        result: BenchmarkResult,
    ) -> None:
        """Print the summary statistics for a completed benchmark operation."""
        lower_percentage = int(
            self.config.lower_fraction * 100
        )

        upper_percentage = int(
            self.config.upper_fraction * 100
        )

        print(
            f"{result.operation}: "
            f"{lower_percentage}%="
            f"{result.lower_bound_us:.4f} μs, "
            f"{upper_percentage}%="
            f"{result.upper_bound_us:.4f} μs, "
            f"avg="
            f"{result.average_us:.4f} μs"
        )

    def _print_memory_result(
        self,
        operation: str,
        memory_stats: MemoryStats,
    ) -> None:
        """Print whole-PID process-memory bounds and the average."""
        lower_percentage = int(self.config.lower_fraction * 100)
        upper_percentage = int(self.config.upper_fraction * 100)

        print(
            f"{operation} PID memory: "
            f"{lower_percentage}%="
            f"{memory_stats.lower_bound_mib:.4f} MiB, "
            f"{upper_percentage}%="
            f"{memory_stats.upper_bound_mib:.4f} MiB, "
            f"avg="
            f"{memory_stats.average_mib:.4f} MiB"
        )