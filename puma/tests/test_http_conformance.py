"""HTTP conformance tests — fixtures 05.

Runs all YAML fixtures from spec/tests/05_http against the puma.http
matching engine (HttpRequest + Gateway API compiler).
"""

from __future__ import annotations

import pytest

from tests.conftest import HttpFixtureCase, load_http_fixtures

_HTTP_FIXTURES = load_http_fixtures()


@pytest.mark.parametrize(
    "fixture",
    _HTTP_FIXTURES,
    ids=lambda f: f"{f.fixture_name}::{f.case_name}",
)
def test_http_conformance(fixture: HttpFixtureCase) -> None:
    """Each HTTP fixture case must produce the expected action (or None)."""
    result = fixture.matcher.evaluate(fixture.request)
    assert result == fixture.expect, (
        f"Fixture '{fixture.fixture_name}', case '{fixture.case_name}': "
        f"expected {fixture.expect!r}, got {result!r}"
    )
