"""Eviction policies for CacheLite."""

from ..errors import UnknownPolicyError
from ..types import EvictionPolicy as PolicyName
from .base import EvictionPolicy
from .fifo import FIFOPolicy
from .lfu import LFUPolicy
from .lru import LRUPolicy
from .random_evict import RandomPolicy

_REGISTRY = {
    PolicyName.LRU: LRUPolicy,
    PolicyName.LFU: LFUPolicy,
    PolicyName.FIFO: FIFOPolicy,
    PolicyName.RANDOM: RandomPolicy,
}


def make_policy(name) -> EvictionPolicy:
    """Instantiate a policy by name or enum."""
    if isinstance(name, str):
        try:
            name = PolicyName.from_string(name)
        except ValueError as exc:
            raise UnknownPolicyError(str(exc)) from exc
    cls = _REGISTRY.get(name)
    if cls is None:
        raise UnknownPolicyError(f"no policy registered for {name!r}")
    return cls()


__all__ = [
    "EvictionPolicy",
    "LRUPolicy",
    "LFUPolicy",
    "FIFOPolicy",
    "RandomPolicy",
    "make_policy",
]
