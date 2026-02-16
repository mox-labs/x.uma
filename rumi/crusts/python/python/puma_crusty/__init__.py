"""puma-crusty: Python bindings for rumi (Rust matcher engine).

Linear-time regex, zero-copy evaluation, type-safe config.
"""

from puma_crusty.puma_crusty import (
    HookMatcher,
    HttpMatcher,
    PyHookMatch as HookMatch,
    PyStringMatch as StringMatch,
    TestMatcher,
)

__all__ = ["HookMatcher", "HookMatch", "HttpMatcher", "StringMatch", "TestMatcher"]
