"""Core conformance tests — fixtures 01-04.

Runs all YAML fixtures from spec/tests/01_string_matchers through
spec/tests/04_invariants against the puma matching engine.
"""

from __future__ import annotations

import pytest

from tests.conftest import FixtureCase, load_core_fixtures

_CORE_FIXTURES = load_core_fixtures()


@pytest.mark.parametrize(
    "fixture",
    _CORE_FIXTURES,
    ids=lambda f: f"{f.fixture_name}::{f.case_name}",
)
def test_core_conformance(fixture: FixtureCase) -> None:
    """Each fixture case must produce the expected action (or None)."""
    result = fixture.matcher.evaluate(fixture.context)
    assert result == fixture.expect, (
        f"Fixture '{fixture.fixture_name}', case '{fixture.case_name}': "
        f"expected {fixture.expect!r}, got {result!r}"
    )
