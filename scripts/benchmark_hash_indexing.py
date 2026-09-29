"""Benchmark runner for hashing-based indexing comparisons."""

from __future__ import annotations

from src.benchmarks.config import AppConfig
from src.benchmarks.runner import BenchmarkRunner
from src.common.csv_handler import get_formatted_data
from src.common.evaluator import Evaluator
from src.db_type_helpers.hash_index import HashIndex


INDEX_COLUMNS = ("timestamp", "district_id")
UPDATE_VALUES = {"dm25": "0.0", "dm10": "0.0"}


def build_index(data: list) -> HashIndex:
    """Create and populate a hash index before measuring search, update, and delete."""
    index = HashIndex(max(1, len(data) // 3))
    index.insert_all_data(data, INDEX_COLUMNS)

    return index


def main() -> None:
    """Run the hash index benchmark sequence for the core CRUD operations."""
    config = AppConfig.from_env("results/hash_indexing/equals/air_quality_5k")
    runner = BenchmarkRunner(config, Evaluator())
    data = get_formatted_data(str(config.dataset_path))

    runner.run(
        "insert",
        lambda: HashIndex(max(1, len(data) // 3)).insert_all_data(
            data,
            INDEX_COLUMNS,
        ),
    )

    runner.run_with_setup(
        "search",
        setup=lambda: build_index(data),
        function=lambda index: index.search_all(
            data,
            INDEX_COLUMNS,
        ),
    )

    runner.run_with_setup(
        "update",
        setup=lambda: build_index(data),
        function=lambda index: index.update_all(
            data,
            INDEX_COLUMNS,
            UPDATE_VALUES,
        ),
    )

    runner.run_with_setup(
        "delete",
        setup=lambda: build_index(data),
        function=lambda index: index.delete_all(
            data,
            INDEX_COLUMNS,
        ),
    )


if __name__ == "__main__":
    main()