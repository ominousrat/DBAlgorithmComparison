"""Benchmark runner for the baseline sequential-scan implementation."""

from __future__ import annotations

from copy import deepcopy

from src.benchmarks.config import AppConfig
from src.benchmarks.runner import BenchmarkRunner
from src.common.csv_handler import get_formatted_data
from src.common.evaluator import Evaluator
from src.common.operator import Operator
from src.db_type_helpers.sequential_search import (
    delete_all,
    insert_all,
    search_all,
    update_all,
)


SEARCH_COLUMN = "timestamp"
SEARCH_VALUE = "2023-08-23 19:00:00"


def main() -> None:
    """Execute the sequential-search benchmark for the core database operations."""
    config = AppConfig.from_env(
        "results/sequential_search/less_equals/ecommerce_sales_customer_analytics_25k"
    )

    runner = BenchmarkRunner(config, Evaluator())

    dataset_path = str(config.dataset_path)
    source_data = get_formatted_data(dataset_path)

    runner.run(
        "insert",
        lambda: insert_all(
            deepcopy(source_data),
        )[0],
    )

    runner.run(
        "search",
        lambda: search_all(
            dataset_path,
            deepcopy(source_data),
            SEARCH_COLUMN,
            Operator.LESS_EQUALS,
            SEARCH_VALUE,
        ),
    )

    runner.run(
        "update",
        lambda: update_all(
            dataset_path,
            deepcopy(source_data),
            SEARCH_COLUMN,
            SEARCH_VALUE,
        )[0],
    )

    runner.run(
        "delete",
        lambda: delete_all(
            deepcopy(source_data),
        ),
    )


if __name__ == "__main__":
    main()