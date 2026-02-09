"""puma-crusty: Python bindings for rumi (Rust matcher engine).

Linear-time regex, zero-copy evaluation, type-safe config.
"""

from puma_crusty.puma_crusty import HookMatcher, PyHookMatch as HookMatch, PyStringMatch as StringMatch

__all__ = ["HookMatcher", "HookMatch", "StringMatch"]
