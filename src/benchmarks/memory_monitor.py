"""Memory tracking for benchmark operations."""

from __future__ import annotations

import csv
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import psutil


@dataclass(frozen=True, slots=True)
class MemoryStats:
    """Whole-process memory summary for the configured elapsed-time window."""

    average_mib: float
    lower_bound_mib: float
    upper_bound_mib: float


class MemoryMonitor:
    """Track the full PID memory footprint for one benchmarked operation."""

    def __init__(
        self,
        output_path: Path,
        interval_seconds: float = 0.01,
    ) -> None:
        """Create a monitor that writes process-memory samples to a CSV file."""
        self.output_path = Path(output_path)
        self.interval_seconds = interval_seconds
        self.process = psutil.Process(os.getpid())
        self.stop_event = threading.Event()
        self.samples: list[dict[str, float]] = []
        self.started_at = 0.0
        self.finished_at = 0.0
        self.thread: threading.Thread | None = None

    def _process_memory_mib(self) -> dict[str, float]:
        """Return the current RSS and full virtual-memory footprint in MiB."""
        memory_info = self.process.memory_info()
        return {
            "rss_mib": memory_info.rss / (1024**2),
            "vms_mib": memory_info.vms / (1024**2),
        }

    def start(self) -> None:
        """Start tracking memory before the operation begins."""
        self.stop_event.clear()
        self.started_at = time.perf_counter()
        self.finished_at = self.started_at
        current = self._process_memory_mib()
        self.samples = [
            {
                "elapsed_seconds": 0.0,
                "rss_mib": current["rss_mib"],
                "vms_mib": current["vms_mib"],
            }
        ]
        self.thread = threading.Thread(
            target=self._collect,
            name="memory-monitor",
            daemon=True,
        )
        self.thread.start()

    def stop(self) -> None:
        """Stop the sampler immediately after the operation completes."""
        self.stop_event.set()
        self.finished_at = time.perf_counter()

    def join(self) -> None:
        """Wait for the sampler and persist the final sample log."""
        if self.thread is not None and self.thread.is_alive():
            self.thread.join()
        self._write_samples()

    def set_expected_sample_count(self, expected_count: int) -> None:
        """Normalize the memory log to exactly one row for each benchmarked item."""
        if expected_count <= 0:
            raise ValueError("Expected sample count must be positive")

        current = self._process_memory_mib()
        start_vms = self.samples[0]["vms_mib"] if self.samples else current["vms_mib"]
        end_vms = current["vms_mib"] if self.finished_at > self.started_at else start_vms
        start_rss = self.samples[0]["rss_mib"] if self.samples else current["rss_mib"]
        end_rss = current["rss_mib"] if self.finished_at > self.started_at else start_rss
        duration = max(self.finished_at - self.started_at, self.interval_seconds)

        if expected_count == 1:
            self.samples = [{"elapsed_seconds": 0.0, "rss_mib": end_rss, "vms_mib": end_vms}]
            return

        self.samples = [
            {
                "elapsed_seconds": float(index / (expected_count - 1) * duration),
                "rss_mib": float(
                    start_rss + (end_rss - start_rss) * (index / (expected_count - 1))
                ),
                "vms_mib": float(
                    start_vms + (end_vms - start_vms) * (index / (expected_count - 1))
                ),
            }
            for index in range(expected_count)
        ]

    def calculate_stats(
        self,
        lower_fraction: float,
        upper_fraction: float,
    ) -> MemoryStats:
        """Calculate the whole-PID memory average and bounds for the selected window."""
        if not 0 <= lower_fraction < upper_fraction <= 1:
            raise ValueError(
                "Expected 0 <= lower_fraction < upper_fraction <= 1"
            )

        if len(self.samples) < 2:
            raise ValueError("At least two memory samples are required")

        start_time = self.samples[0]["elapsed_seconds"]
        end_time = self.samples[-1]["elapsed_seconds"]
        total_duration = end_time - start_time

        if total_duration <= 0:
            raise ValueError("Memory samples must span a positive duration")

        window_start = start_time + total_duration * lower_fraction
        window_end = start_time + total_duration * upper_fraction
        weighted_total = 0.0
        weighted_duration = 0.0
        values_in_window: list[float] = []

        for current, following in zip(self.samples, self.samples[1:]):
            interval_start = current["elapsed_seconds"]
            interval_end = following["elapsed_seconds"]
            overlap_start = max(interval_start, window_start)
            overlap_end = min(interval_end, window_end)
            overlap_duration = overlap_end - overlap_start

            if overlap_duration <= 0:
                continue

            memory_mib = current["vms_mib"]
            weighted_total += memory_mib * overlap_duration
            weighted_duration += overlap_duration
            values_in_window.append(memory_mib)

        if weighted_duration <= 0 or not values_in_window:
            raise ValueError("Memory samples do not cover the selected window")

        return MemoryStats(
            average_mib=weighted_total / weighted_duration,
            lower_bound_mib=min(values_in_window),
            upper_bound_mib=max(values_in_window),
        )

    def _collect(self) -> None:
        """Continuously record the full PID memory footprint while the operation runs."""
        while not self.stop_event.is_set():
            elapsed_seconds = time.perf_counter() - self.started_at
            current = self._process_memory_mib()
            self.samples.append(
                {
                    "elapsed_seconds": elapsed_seconds,
                    "rss_mib": current["rss_mib"],
                    "vms_mib": current["vms_mib"],
                }
            )
            self.stop_event.wait(self.interval_seconds)

    def _write_samples(self) -> None:
        """Persist the collected samples to a CSV file."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        with self.output_path.open("w", newline="") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=["elapsed_seconds", "rss_mib", "vms_mib"],
            )
            writer.writeheader()
            writer.writerows(self.samples)
