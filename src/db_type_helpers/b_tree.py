"""
B-tree implementation used as one of the benchmarked database access patterns.

The tree stores rows keyed by one or more columns and supports the operations
required by the benchmark harness: insertion, search, update, and deletion.
"""

import bisect
from time import perf_counter
from src.common.operator import Operator


class BTreeNode:
    """Single node in a B-tree containing sorted keys and child references."""

    def __init__(self, leaf: bool = False):
        """Create a node with optional child pointers for non-leaf nodes."""
        self.leaf = leaf
        self.keys = []
        self.values = []
        self.children = []


class BTree:
    """A B-tree implementation with ordered keys and row payloads."""

    def __init__(self, t: int = 3):
        """Create a B-tree with the minimum degree set by t."""
        if t < 2:
            raise ValueError("Minimum degree t must be >= 2")

        self.t = t
        self.root = BTreeNode(leaf=True)

    def search(self, key, node: BTreeNode | None = None):
        """Return the stored value for the supplied key, if present."""
        if node is None:
            node = self.root

        index = bisect.bisect_left(node.keys, key)

        if index < len(node.keys) and node.keys[index] == key:
            return node.values[index]

        if node.leaf:
            return None

        return self.search(key, node.children[index])

    def search_operator(self, compare_value, operator_: Operator) -> list[dict]:
        """Search using a comparison operator over the tree's stored keys."""
        if not isinstance(operator_, Operator):
            raise TypeError("operator_ must be an Operator")

        if operator_ is Operator.EQUALS:
            value = self.search(compare_value)
            return [] if value is None else [value]

        results = []

        if operator_ is Operator.LESS:
            self._search_less(self.root, compare_value, inclusive=False, results=results)

        elif operator_ is Operator.LESS_EQUALS:
            self._search_less(self.root, compare_value, inclusive=True, results=results)

        elif operator_ is Operator.GREATER:
            self._search_greater(self.root, compare_value, inclusive=False, results=results)

        elif operator_ is Operator.GREATER_EQUALS:
            self._search_greater(self.root, compare_value, inclusive=True, results=results)
        
        elif operator_ is Operator.NOT_EQUALS:
            self._search_not_equals(self.root, compare_value, results)

        return results


    def _collect_all(self, node: BTreeNode, results: list[dict]) -> None:
        for index, value in enumerate(node.values):
            if not node.leaf:
                self._collect_all(node.children[index], results)

            results.append(value)

        if not node.leaf:
            self._collect_all(node.children[-1], results)


    def _search_less(self, node: BTreeNode, compare_value, inclusive: bool, results: list[dict]) -> None:
        for index, key in enumerate(node.keys):
            matches = key <= compare_value if inclusive else key < compare_value

            if matches:
                if not node.leaf:
                    self._collect_all(node.children[index], results)

                results.append(node.values[index])

                continue

            if not node.leaf:
                self._search_less(node.children[index], compare_value, inclusive, results)

            return

        if not node.leaf:
            self._collect_all(node.children[-1], results)


    def _search_greater(self, node: BTreeNode, compare_value, inclusive: bool, results: list[dict]) -> None:
        for index, key in enumerate(node.keys):
            matches = key >= compare_value if inclusive else key > compare_value

            if not matches:
                continue

            if not node.leaf:
                self._search_greater(node.children[index], compare_value, inclusive, results)

            results.append(node.values[index])

            for later_index in range(index + 1, len(node.keys)):
                if not node.leaf:
                    self._collect_all(node.children[later_index], results)

                results.append(node.values[later_index])

            if not node.leaf:
                self._collect_all(node.children[-1], results)

            return

        if not node.leaf:
            self._search_greater(node.children[-1], compare_value, inclusive, results)


    def _search_not_equals(self, node: BTreeNode, compare_value, results: list[dict]) -> None:
        for index, key in enumerate(node.keys):
            if not node.leaf:
                self._search_not_equals(node.children[index], compare_value, results)

            if key != compare_value:
                results.append(node.values[index])

        if not node.leaf:
            self._search_not_equals(node.children[-1], compare_value, results)

    def _search_row_fields(self, fields: str | tuple[str, ...], compare_value, operator_: Operator) -> list[dict]:
        results = []

        self._search_row_fields_recursive(self.root, fields, compare_value, operator_, results)

        return results


    def _search_row_fields_recursive(self, node: BTreeNode, fields: str | tuple[str, ...], compare_value, operator_: Operator, results: list[dict]) -> None:
        for index, row in enumerate(node.values):
            if not node.leaf:
                self._search_row_fields_recursive(node.children[index], fields, compare_value, operator_, results)

            row_value = self._make_key(row, fields)
            if operator_(row_value, compare_value):
                results.append(row)

        if not node.leaf:
            self._search_row_fields_recursive(node.children[-1], fields, compare_value, operator_, results)


    def insert(self, key, val: dict):
        """Insert a row into the tree under the supplied key."""
        root = self.root

        if len(root.keys) == (2 * self.t - 1):
            new_root = BTreeNode(leaf=False)
            new_root.children.append(self.root)
            self._split_child(new_root, 0)
            self.root = new_root
            self._insert_non_full(new_root, key, val)

        else:
            self._insert_non_full(root, key, val)


    def _split_child(self, parent: BTreeNode, i: int):
        t = self.t
        child = parent.children[i]
        sibling = BTreeNode(leaf=child.leaf)

        median_key = child.keys[t - 1]
        median_val = child.values[t - 1]

        sibling.keys = child.keys[t:]
        sibling.values = child.values[t:]

        if not child.leaf:
            sibling.children = child.children[t:]

        child.keys = child.keys[:t - 1]
        child.values = child.values[:t - 1]

        if not child.leaf:
            child.children = child.children[:t]

        parent.children.insert(i + 1, sibling)
        parent.keys.insert(i, median_key)
        parent.values.insert(i, median_val)


    def _insert_non_full(self, node: BTreeNode, key, val: dict):
        idx = bisect.bisect_left(node.keys, key)

        if idx < len(node.keys) and node.keys[idx] == key:
            node.values[idx] = val

            return

        if node.leaf:
            node.keys.insert(idx, key)
            node.values.insert(idx, val)

            return

        if len(node.children[idx].keys) == (2 * self.t - 1):
            self._split_child(node, idx)

            if key == node.keys[idx]:
                node.values[idx] = val
                return

            elif key > node.keys[idx]:
                idx += 1

        self._insert_non_full(node.children[idx], key, val)


    def delete(self, key):
        """Delete the row associated with the supplied key from the tree."""
        self._delete(self.root, key)

        if len(self.root.keys) == 0:
            if not self.root.leaf and len(self.root.children) > 0:
                self.root = self.root.children[0]


    def _delete(self, node: BTreeNode, key):
        t = self.t
        idx = bisect.bisect_left(node.keys, key)

        if idx < len(node.keys) and node.keys[idx] == key:
            if node.leaf:
                node.keys.pop(idx)
                node.values.pop(idx)

            else:
                left_child = node.children[idx]
                right_child = node.children[idx + 1]

                if len(left_child.keys) >= t:
                    pred_k, pred_v = self._get_max(left_child)
                    node.keys[idx] = pred_k
                    node.values[idx] = pred_v
                    self._delete(left_child, pred_k)

                elif len(right_child.keys) >= t:
                    succ_k, succ_v = self._get_min(right_child)
                    node.keys[idx] = succ_k
                    node.values[idx] = succ_v
                    self._delete(right_child, succ_k)

                else:
                    self._merge(node, idx)
                    self._delete(left_child, key)

            return

        if node.leaf:
            return

        if len(node.children[idx].keys) < t:
            self._fill(node, idx)
            idx = bisect.bisect_left(node.keys, key)

        self._delete(node.children[idx], key)


    def _get_max(self, node: BTreeNode):
        curr = node

        while not curr.leaf:
            curr = curr.children[-1]

        return curr.keys[-1], curr.values[-1]


    def _get_min(self, node: BTreeNode):
        curr = node

        while not curr.leaf:
            curr = curr.children[0]

        return curr.keys[0], curr.values[0]

    def _fill(self, parent: BTreeNode, idx: int):
        t = self.t

        if idx > 0 and len(parent.children[idx - 1].keys) >= t:
            self._borrow_from_prev(parent, idx)
        elif idx < len(parent.children) - 1 and len(parent.children[idx + 1].keys) >= t:
            self._borrow_from_next(parent, idx)
        else:
            if idx < len(parent.children) - 1:
                self._merge(parent, idx)
            else:
                self._merge(parent, idx - 1)


    def _borrow_from_prev(self, parent: BTreeNode, idx: int):
        child = parent.children[idx]
        sibling = parent.children[idx - 1]

        child.keys.insert(0, parent.keys[idx - 1])
        child.values.insert(0, parent.values[idx - 1])
        parent.keys[idx - 1] = sibling.keys.pop()
        parent.values[idx - 1] = sibling.values.pop()

        if not sibling.leaf:
            child.children.insert(0, sibling.children.pop())


    def _borrow_from_next(self, parent: BTreeNode, idx: int):
        child = parent.children[idx]
        sibling = parent.children[idx + 1]

        child.keys.append(parent.keys[idx])
        child.values.append(parent.values[idx])
        parent.keys[idx] = sibling.keys.pop(0)
        parent.values[idx] = sibling.values.pop(0)

        if not sibling.leaf:
            child.children.append(sibling.children.pop(0))


    def _merge(self, parent: BTreeNode, idx: int):
        child = parent.children[idx]
        sibling = parent.children[idx + 1]

        child.keys.append(parent.keys.pop(idx))
        child.values.append(parent.values.pop(idx))
        parent.children.pop(idx + 1)

        child.keys.extend(sibling.keys)
        child.values.extend(sibling.values)

        if not sibling.leaf:
            child.children.extend(sibling.children)


    def update(self, key, new_val: dict) -> bool:
        """Replace the stored value for an existing key and return whether it existed."""
        return self._update(self.root, key, new_val)


    def _update(self, node: BTreeNode, key, new_val: dict) -> bool:
        idx = bisect.bisect_left(node.keys, key)

        if idx < len(node.keys) and node.keys[idx] == key:
            node.values[idx] = new_val
            return True

        if node.leaf:
            return False

        return self._update(node.children[idx], key, new_val)


    @staticmethod
    def _make_key(row: dict, key_fields: str | tuple[str, ...]):
        if isinstance(key_fields, str):
            return row[key_fields]
        return tuple(row[field] for field in key_fields)


    def insert_all_data(self, data: list[dict], key_fields: str | tuple[str, ...]) -> list[float]:
        """Benchmark insertion for every row in a dataset using the selected key fields."""
        if len(data) < 1:
            raise ValueError("data: Length must be greater than 0")

        times_in_micro_sec = []

        try:
            for row in data:
                key = self._make_key(row, key_fields)

                start_time = perf_counter()
                self.insert(key, row)
                end_time = perf_counter()

                times_in_micro_sec.append((end_time - start_time) * 1_000_000)

            return times_in_micro_sec

        except Exception as exc:
            raise RuntimeError(f"[{self.__class__.__name__}] insert_all_data: Inserting data failed") from exc


    def search_all(
        self,
        data: list[dict],
        key_fields: str | tuple[str, ...],
        operator_: Operator = Operator.EQUALS,
        compare_value=None,
        compare_keys: bool = True,
    ) -> list[float]:
        """Benchmark repeated tree lookups over the supplied dataset."""
        if not data:
            raise ValueError("data: Length must be greater than 0")

        if not isinstance(operator_, Operator):
            raise TypeError("operator_ must be an Operator")

        if not isinstance(compare_keys, bool):
            raise TypeError("compare_keys must be a bool")

        if operator_ is not Operator.EQUALS and compare_value is None:
            raise ValueError("compare_value is required for non-equality searches")

        times_in_micro_sec = []

        try:
            for row in data:
                current_compare_value = (self._make_key(row, key_fields) if compare_value is None else compare_value)

                start_time = perf_counter()

                if compare_keys:
                    self.search_operator(current_compare_value, operator_)
                else:
                    self._search_row_fields(
                        key_fields,
                        current_compare_value,
                        operator_,
                    )

                end_time = perf_counter()

                times_in_micro_sec.append((end_time - start_time) * 1_000_000)

            return times_in_micro_sec

        except Exception as exc:
            raise RuntimeError(f"[{self.__class__.__name__}] search_all: Searching data failed") from exc


    def delete_all(self, data: list[dict], key_fields: str | tuple[str, ...]) -> list[float]:
        """Benchmark deletion for every unique key in the dataset."""
        if len(data) < 1:
            raise ValueError("data: Length must be greater than 0")

        times_in_micro_sec = []
        keys_to_delete = list(dict.fromkeys(self._make_key(row, key_fields) for row in data))

        try:
            for key in keys_to_delete:
                start_time = perf_counter()
                self.delete(key)
                end_time = perf_counter()

                times_in_micro_sec.append(
                    (end_time - start_time) * 1_000_000
                )

            return times_in_micro_sec

        except Exception as exc:
            raise RuntimeError(f"[{self.__class__.__name__}] delete_all: Deleting data failed") from exc


    def update_all(self, data: list[dict], key_fields: str | tuple[str, ...], updates: dict) -> list[float]:
        """Benchmark replacement of existing rows with updated field values."""
        if len(data) < 1:
            raise ValueError("data: Length must be greater than 0")

        times_in_micro_sec = []

        try:
            for row in data:
                key = self._make_key(row, key_fields)
                updated_row = {**row, **updates}

                start_time = perf_counter()
                success = self.update(key, updated_row)
                end_time = perf_counter()

                if not success:
                    raise KeyError(key)

                times_in_micro_sec.append((end_time - start_time) * 1_000_000)

            return times_in_micro_sec

        except Exception as exc:
            raise RuntimeError(f"[{self.__class__.__name__}] update_all: Updating data failed") from exc
