"""
Configuration values used across the benchmarking workflow.

The module centralizes runtime settings such as dataset locations, result
output directories, and the statistical trimming range used when summarizing
operation timing samples.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Application settings for a benchmark run.

    Attributes:
        dataset_path: Source CSV used as the benchmark input.
        result_path: Directory where CSV outputs are written.
        lower_fraction: Lower percentile boundary used in result summaries.
        upper_fraction: Upper percentile boundary used in result summaries.
    """

    dataset_path: Path
    result_path: Path
    lower_fraction: float = 0.25
    upper_fraction: float = 0.75

    def __post_init__(self) -> None:
        """Validate the configuration values after dataclass initialization."""
        if not 0 <= self.lower_fraction < self.upper_fraction <= 1:
            raise ValueError("Expected 0 <= lower_fraction < upper_fraction <= 1")

        
    @classmethod
    def from_env(
        cls,
        result_path: str | Path,
        *,
        lower_fraction: float = 0.25,
        upper_fraction: float = 0.75,
    ) -> "AppConfig":
        """Build an AppConfig instance from environment variables.

        The dataset path is required and is read from the .env file. The result
        directory and benchmarking fractions can be overridden by arguments or
        environment values.
        """
        values = dotenv_values(".env")

        dataset_file = values.get("DATASET_FILE_PATH")

        lower_fraction = float(values.get("LOWER_FRACTION", lower_fraction))
        upper_fraction = float(values.get("UPPER_FRACTION", upper_fraction))

        if not dataset_file:
            raise RuntimeError("DATASET_FILE_PATH is missing from .env")

        return cls(
            dataset_path=Path(dataset_file),
            result_path=Path(result_path),
            lower_fraction=lower_fraction,
            upper_fraction=upper_fraction,
        )