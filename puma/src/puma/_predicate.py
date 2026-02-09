"""Predicate composition — Boolean logic over data extraction + matching.

SinglePredicate combines a DataInput (extract) with an InputMatcher (match).
And, Or, Not compose predicates with short-circuit evaluation.

The Predicate union type is pattern-matchable via match/case.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from puma._types import DataInput, InputMatcher


@dataclass(frozen=True, slots=True)
class SinglePredicate[Ctx]:
    """A single predicate: extract data, then match.

    Enforces the None -> false invariant: if the DataInput returns None,
    the predicate evaluates to False without consulting the matcher.
    """

    input: DataInput[Ctx]
    matcher: InputMatcher

    def evaluate(self, ctx: Any) -> bool:
        value = self.input.get(ctx)
        if value is None:
            return False  # INV: None -> false (Dijkstra)
        return self.matcher.matches(value)


@dataclass(frozen=True, slots=True)
class And[Ctx]:
    """All predicates must match (logical AND).

    Short-circuits on the first False. Empty And returns True (vacuous truth).
    """

    predicates: tuple[Predicate[Ctx], ...]

    def evaluate(self, ctx: Any) -> bool:
        return all(p.evaluate(ctx) for p in self.predicates)


@dataclass(frozen=True, slots=True)
class Or[Ctx]:
    """Any predicate must match (logical OR).

    Short-circuits on the first True. Empty Or returns False.
    """

    predicates: tuple[Predicate[Ctx], ...]

    def evaluate(self, ctx: Any) -> bool:
        return any(p.evaluate(ctx) for p in self.predicates)


@dataclass(frozen=True, slots=True)
class Not[Ctx]:
    """Inverts the result of the inner predicate (logical NOT)."""

    predicate: Predicate[Ctx]

    def evaluate(self, ctx: Any) -> bool:
        return not self.predicate.evaluate(ctx)


# Union type — the Pythonic way to express Rust's Predicate<Ctx> enum.
type Predicate[Ctx] = SinglePredicate[Ctx] | And[Ctx] | Or[Ctx] | Not[Ctx]


def predicate_depth(p: Predicate[Any]) -> int:
    """Calculate the nesting depth of a predicate tree."""
    match p:
        case SinglePredicate():
            return 1
        case And(predicates=ps) | Or(predicates=ps):
            return 1 + max((predicate_depth(sub) for sub in ps), default=0)
        case Not(predicate=inner):
            return 1 + predicate_depth(inner)
        case _:  # pragma: no cover
            return 0
