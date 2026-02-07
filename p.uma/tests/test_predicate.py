"""Tests for predicate composition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from puma import (
    And,
    ExactMatcher,
    Not,
    Or,
    SinglePredicate,
    predicate_depth,
)

if TYPE_CHECKING:
    from puma._types import MatchingValue


@dataclass(frozen=True)
class ValueInput:
    """Test DataInput that extracts a named key from a dict."""

    key: str

    def get(self, ctx: dict[str, str], /) -> MatchingValue:
        return ctx.get(self.key)


class TestSinglePredicate:
    def test_match(self) -> None:
        p = SinglePredicate(ValueInput("name"), ExactMatcher("alice"))
        assert p.evaluate({"name": "alice"}) is True

    def test_no_match(self) -> None:
        p = SinglePredicate(ValueInput("name"), ExactMatcher("alice"))
        assert p.evaluate({"name": "bob"}) is False

    def test_none_returns_false(self) -> None:
        p = SinglePredicate(ValueInput("missing"), ExactMatcher("alice"))
        assert p.evaluate({"name": "alice"}) is False


class TestAnd:
    def test_all_true(self) -> None:
        p = And(
            (
                SinglePredicate(ValueInput("a"), ExactMatcher("1")),
                SinglePredicate(ValueInput("b"), ExactMatcher("2")),
            )
        )
        assert p.evaluate({"a": "1", "b": "2"}) is True

    def test_one_false(self) -> None:
        p = And(
            (
                SinglePredicate(ValueInput("a"), ExactMatcher("1")),
                SinglePredicate(ValueInput("b"), ExactMatcher("wrong")),
            )
        )
        assert p.evaluate({"a": "1", "b": "2"}) is False

    def test_empty_and_returns_true(self) -> None:
        p: And[dict[str, str]] = And(())
        assert p.evaluate({}) is True


class TestOr:
    def test_one_true(self) -> None:
        p = Or(
            (
                SinglePredicate(ValueInput("a"), ExactMatcher("wrong")),
                SinglePredicate(ValueInput("a"), ExactMatcher("1")),
            )
        )
        assert p.evaluate({"a": "1"}) is True

    def test_all_false(self) -> None:
        p = Or(
            (
                SinglePredicate(ValueInput("a"), ExactMatcher("x")),
                SinglePredicate(ValueInput("a"), ExactMatcher("y")),
            )
        )
        assert p.evaluate({"a": "1"}) is False

    def test_empty_or_returns_false(self) -> None:
        p: Or[dict[str, str]] = Or(())
        assert p.evaluate({}) is False


class TestNot:
    def test_inverts_true(self) -> None:
        p = Not(SinglePredicate(ValueInput("a"), ExactMatcher("1")))
        assert p.evaluate({"a": "1"}) is False

    def test_inverts_false(self) -> None:
        p = Not(SinglePredicate(ValueInput("a"), ExactMatcher("wrong")))
        assert p.evaluate({"a": "1"}) is True


class TestPredicateDepth:
    def test_single_depth(self) -> None:
        p = SinglePredicate(ValueInput("a"), ExactMatcher("1"))
        assert predicate_depth(p) == 1

    def test_and_depth(self) -> None:
        p = And((SinglePredicate(ValueInput("a"), ExactMatcher("1")),))
        assert predicate_depth(p) == 2

    def test_nested_depth(self) -> None:
        p = Not(And((SinglePredicate(ValueInput("a"), ExactMatcher("1")),)))
        assert predicate_depth(p) == 3
