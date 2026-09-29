"""Utilities for reading and writing CSV files used by the benchmark suite."""

import csv
from pathlib import Path


def ensure_directory_exists(filepath: str) -> None:
    """Create the parent directory for a file if it does not already exist."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)


def read_data(filepath: str) -> list:
    """Read a CSV file and return its rows without the header record."""
    with open(filepath, mode="r") as file:
        data = []

        reader = csv.reader(file)
        for row in reader:
            data.append(row)

    return data[1:]


def write_data(filepath: str, data: list) -> None:
    """Overwrite a CSV file with the supplied rows."""
    ensure_directory_exists(filepath)

    with open(filepath, mode="w", newline="") as file:
        writer = csv.writer(file)

        writer.writerows(data)


def write_lines(filepath: str, data: list[dict]) -> None:
    """Append dictionary rows to a CSV file using the values in insertion order."""
    ensure_directory_exists(filepath)

    with open(filepath, mode="a", newline="") as file:
        writer = csv.writer(file)
        for row in data:
            writer.writerow(row.values())


def write_all_lines(filepath: str, data: list[dict]) -> None:
    """Write a flat list of numeric values to a CSV file, one value per row."""
    ensure_directory_exists(filepath)

    with open(filepath, mode="w", newline="") as file:
        writer = csv.writer(file)
        for row in data:
            writer.writerow([row])


def get_columns(filepath: str):
    """Return the column names declared in the header row of a CSV file."""
    with open(filepath, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        columns = reader.fieldnames

        return columns


def get_formatted_data(filepath: str):
    """Load a CSV file as a list of dictionaries keyed by the column names."""
    with open(filepath, newline="", encoding="utf-8") as file:
        reader = list(csv.DictReader(file))

        return reader
