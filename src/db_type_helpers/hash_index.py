"""
Hash-based indexing implementation used in benchmark comparisons.

The structure stores rows in buckets keyed by a hash of the selected record key.
This keeps insertion, lookup, update, and deletion operations simple for the
benchmark harness.
"""

from time import perf_counter


class HashIndex:
    """A simple hash table that stores rows by a composite or single field key."""

    def __init__(self, size=100):
        """Initialize the hash index with a fixed number of buckets."""
        self.size = size
        self.buckets = [[] for _ in range(size)]

    def _index(self, key):
        """Return the bucket index for a given key."""
        return hash(key) % self.size

    def insert(self, key, value):
        """Insert or replace a key-value pair in the appropriate bucket."""
        index = self._index(key)
        bucket = self.buckets[index]

        try:
            for i, (existing_key, _) in enumerate(bucket):
                if existing_key == key:
                    bucket[i] = (key, value)
                    return

            bucket.append((key, value))

        except Exception as e:
            raise RuntimeError(f"[{self.__class__.__name__}] insert: Inserting failed") from e

    def search(self, key):
        """Return the stored value associated with the given key."""
        index = self._index(key)
        bucket = self.buckets[index]

        try:
            for existing_key, value in bucket:
                if existing_key == key:
                    return value

            raise KeyError(key)

        except Exception as e:
            raise RuntimeError(f"[{self.__class__.__name__}] search: Searching data failed") from e

    def delete(self, key):
        """Remove the value stored for a key from the mapped bucket."""
        index = self._index(key)
        bucket = self.buckets[index]

        try:
            for i, (existing_key, _) in enumerate(bucket):
                if existing_key == key:
                    del bucket[i]
                    return

            raise KeyError(key)

        except Exception as e:
            raise RuntimeError(f"[{self.__class__.__name__}] delete: Deleting failed") from e

    def update(self, key, new_val: dict) -> bool:
        """Update an existing row for the supplied key if it is present."""
        index = self._index(key)
        bucket = self.buckets[index]

        for i, (existing_key, _) in enumerate(bucket):
            if existing_key == key:
                bucket[i] = (key, new_val)
                return True

        return False

    def insert_all_data(self, data: list[dict], key_fields: str | tuple[str, ...]) -> list[float]:
        """Benchmark insertion by storing each row in the hash index."""
        length = len(data)

        if length < 1:
            ValueError(f"data: Length must be greater than 0")

        times_in_micro_sec = []

        try:
            for row in data:
                key = row[key_fields] if isinstance(key_fields, str) else tuple(row[f] for f in key_fields)

                start_time = perf_counter()
                self.insert(key, row)
                end_time = perf_counter()

                times_in_micro_sec.append((end_time - start_time) * 1_000_000)

            return times_in_micro_sec

        except Exception as e:
            raise RuntimeError(f"[{self.__class__.__name__}] insert_all_data: Inserting data failed") from e

    def search_all(self, data: list[dict], key_fields: str | tuple[str, ...]) -> list[float]:
        """Benchmark lookup by searching for every row key in the dataset."""
        length = len(data)

        if length < 1:
            ValueError(f"data: Length must be greater than 0")

        times_in_micro_sec = []

        try:
            for row in data:
                key = row[key_fields] if isinstance(key_fields, str) else tuple(row[f] for f in key_fields)

                start_time = perf_counter()
                self.search(key)
                end_time = perf_counter()

                times_in_micro_sec.append((end_time - start_time) * 1_000_000)

            return times_in_micro_sec

        except Exception as e:
            raise RuntimeError(f"[{self.__class__.__name__}] search_all: Searching data failed") from e

    def delete_all(self, data: list[dict], key_fields: str | tuple[str, ...]) -> list[float]:
        """Benchmark deletion by removing each unique record key in the dataset."""
        length = len(data)

        if length < 1:
            ValueError(f"data: Length must be greater than 0")

        times_in_micro_sec = []

        keys_to_delete = list(dict.fromkeys(
            row[key_fields] if isinstance(key_fields, str) else tuple(row[f] for f in key_fields)
            for row in data
        ))

        try:
            for key in keys_to_delete:
                start_time = perf_counter()
                self.delete(key)
                end_time = perf_counter()

                times_in_micro_sec.append((end_time - start_time) * 1_000_000)

            return times_in_micro_sec

        except Exception as e:
            raise RuntimeError(f"[{self.__class__.__name__}] delete_all: Deleting data failed") from e

    def update_all(self, data: list[dict], key_fields: str | tuple[str, ...], updates: dict) -> list[float]:
        """Benchmark updates by modifying each matching row in the index."""
        if len(data) < 1:
            raise ValueError("data: Length must be greater than 0")

        times_in_micro_sec = []

        try:
            for row in data:
                key = row[key_fields] if isinstance(key_fields, str) else tuple(row[f] for f in key_fields)
                updated_row = {**row, **updates}

                start_time = perf_counter()
                success = self.update(key, updated_row)
                end_time = perf_counter()

                if not success:
                    raise KeyError(key)

                times_in_micro_sec.append((end_time - start_time) * 1_000_000)

            return times_in_micro_sec

        except Exception as e:
            raise RuntimeError(f"[{self.__class__.__name__}] update_all: Updating data failed") from e