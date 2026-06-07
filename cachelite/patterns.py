"""Glob-based key pattern matching for bulk invalidation.

We deliberately use :func:`fnmatch.fnmatchcase` rather than rolling our own
matcher. One gotcha: ``fnmatch`` treats ``*`` as matching *any* character
including separators like ``:`` or ``/``, so ``user:*`` matches
``user:42:profile`` too. That's the behaviour Redis users expect from
``KEYS user:*`` so we keep it.
"""

from __future__ import annotations

import fnmatch
import re
from typing import Iterable, Iterator


def matches(key: str, pattern: str) -> bool:
    """True if ``key`` matches the glob ``pattern`` (case-sensitive)."""
    return fnmatch.fnmatchcase(key, pattern)


def filter_keys(keys: Iterable[str], pattern: str) -> Iterator[str]:
    """Yield keys matching the glob pattern."""
    regex = re.compile(fnmatch.translate(pattern))
    for key in keys:
        if regex.match(key):
            yield key


def compile_pattern(pattern: str) -> "re.Pattern[str]":
    """Pre-compile a glob into a regex for repeated matching."""
    return re.compile(fnmatch.translate(pattern))
