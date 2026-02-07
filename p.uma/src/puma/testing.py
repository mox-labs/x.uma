"""Test utilities for puma.

Provides convenience DataInput implementations for use in tests and examples.
These are NOT domain adapters — they exist to reduce boilerplate when
exploring puma with dict-shaped contexts.

For real domains, implement DataInput for your own context type.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from puma._types import MatchingValue


@dataclass(frozen=True, slots=True)
class DictInput:
    """Extract a value by key from a dict context.

    The simplest possible DataInput — useful for tests, examples, and
    quick exploration without defining a custom context type.

    >>> from puma import SinglePredicate, ExactMatcher
    >>> from puma.testing import DictInput
    >>> p = SinglePredicate(DictInput("name"), ExactMatcher("alice"))
    >>> p.evaluate({"name": "alice"})
    True
    """

    key: str

    def get(self, ctx: dict[str, str], /) -> MatchingValue:
        return ctx.get(self.key)
