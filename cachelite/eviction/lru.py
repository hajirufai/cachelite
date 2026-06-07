"""LRU eviction — doubly-linked list + hash map for O(1) everything."""

from __future__ import annotations

from ..errors import CacheEmptyError
from .base import EvictionPolicy


class _Node:
    """A doubly-linked list node holding a key."""

    __slots__ = ("key", "prev", "next")

    def __init__(self, key: str):
        self.key = key
        self.prev: "_Node | None" = None
        self.next: "_Node | None" = None


class LRUPolicy(EvictionPolicy):
    """Least Recently Used.

    Layout (MRU on the left, LRU on the right)::

        head <-> n1 <-> n2 <-> ... <-> nk <-> tail
        (sentinel)  most-recent     least-recent  (sentinel)

    Sentinel head/tail nodes mean insert/remove never have to special-case
    the empty list or the ends — no null checks in the hot path.
    """

    def __init__(self) -> None:
        self._head = _Node("\x00head")
        self._tail = _Node("\x00tail")
        self._head.next = self._tail
        self._tail.prev = self._head
        self._nodes: dict[str, _Node] = {}

    def _remove_node(self, node: _Node) -> None:
        node.prev.next = node.next
        node.next.prev = node.prev
        node.prev = node.next = None

    def _add_to_head(self, node: _Node) -> None:
        node.prev = self._head
        node.next = self._head.next
        self._head.next.prev = node
        self._head.next = node

    def on_insert(self, key: str) -> None:
        if key in self._nodes:
            # Re-set of an existing key: just promote it.
            self.on_access(key)
            return
        node = _Node(key)
        self._nodes[key] = node
        self._add_to_head(node)

    def on_access(self, key: str) -> None:
        node = self._nodes.get(key)
        if node is None:
            return
        self._remove_node(node)
        self._add_to_head(node)

    def on_remove(self, key: str) -> None:
        node = self._nodes.pop(key, None)
        if node is not None:
            self._remove_node(node)

    def evict(self) -> str:
        victim = self._tail.prev
        if victim is self._head:
            raise CacheEmptyError("nothing to evict")
        self._remove_node(victim)
        del self._nodes[victim.key]
        return victim.key

    def clear(self) -> None:
        self._head.next = self._tail
        self._tail.prev = self._head
        self._nodes.clear()

    def __len__(self) -> int:
        return len(self._nodes)

    def __contains__(self, key: str) -> bool:
        return key in self._nodes
