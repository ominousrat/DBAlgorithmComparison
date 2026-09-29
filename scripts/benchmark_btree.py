"""Benchmark runner for comparing the B-tree implementation against other storage types."""

from __future__ import annotations
from math import trunc

from src.db_type_helpers.b_tree import BTree
from src.benchmarks.config import AppConfig
from src.benchmarks.runner import BenchmarkRunner
from src.common.csv_handler import get_formatted_data
from src.common.evaluator import Evaluator
from src.common.operator import Operator

TOTAL_KEYS = 125_000
TREE_ORDER = trunc((((TOTAL_KEYS * 1.5 + 1) ** (1/3)) - 1) / 2) + 1
INDEX_COLUMNS = ("timestamp")
UPDATE_VALUES = {"dm25": "0.0", "dm10": "0.0"}
SEARCH_VALUES = ("2023-08-23 19:00:00")


def build_tree(data: list) -> BTree:
    """Create and populate a B-tree instance for a benchmark setup phase."""
    tree = BTree(TREE_ORDER)
    tree.insert_all_data(data, INDEX_COLUMNS)

    return tree


def main() -> None:
    """Execute the B-tree benchmark sequence for insert, search, update, and delete."""
    config = AppConfig.from_env("results/b_trees/indexed/less_equals/air_quality_125k")
    runner = BenchmarkRunner(config, Evaluator())
    data = get_formatted_data(str(config.dataset_path))

    runner.run(
        "insert",
        lambda: BTree(TREE_ORDER).insert_all_data(
            data,
            INDEX_COLUMNS,
        ),
    )

    runner.run_with_setup(
        "search",
        setup=lambda: build_tree(data),
        function=lambda tree: tree.search_all(
            data,
            INDEX_COLUMNS,
            Operator.LESS_EQUALS,
            SEARCH_VALUES,
            True,
        ),
    )

    runner.run_with_setup(
        "update",
        setup=lambda: build_tree(data),
        function=lambda tree: tree.update_all(
            data,
            INDEX_COLUMNS,
            UPDATE_VALUES,
        ),
    )

    runner.run_with_setup(
        "delete",
        setup=lambda: build_tree(data),
        function=lambda tree: tree.delete_all(
            data,
            INDEX_COLUMNS,
        ),
    )


if __name__ == "__main__":
    main()