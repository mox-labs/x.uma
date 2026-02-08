# Security — puma

## Regex Engine: ReDoS Risk

puma uses Python's `re` module for `RegexMatcher`. The `re` module employs a **backtracking NFA engine** that is vulnerable to catastrophic backtracking (ReDoS) on pathological patterns.

The Rust reference implementation (rumi) uses the `regex` crate, which provides **linear-time matching guarantees** via Thompson NFA construction — making ReDoS impossible by design.

### What This Means

- **Trusted input**: puma is safe when regex patterns come from trusted configuration (your own route definitions, known fixtures).
- **Adversarial input**: If regex patterns originate from untrusted sources (user-submitted config, external APIs), an attacker can craft pathological patterns like `(a+)+$` that cause exponential CPU consumption.

### Mitigation

For environments processing adversarial input, use **puma-crusty** — the Rust-backed Python package that provides the same API with linear-time regex via uniffi bindings to rumi's `regex` crate.

| Package | Regex Engine | ReDoS Safe | Dependencies |
|---------|-------------|------------|--------------|
| puma | Python `re` (backtracking) | No | Zero |
| puma-crusty | Rust `regex` (linear-time) | Yes | uniffi + Rust binary |

### Depth Limits

Matcher trees are validated at construction time. Trees exceeding `MAX_DEPTH` (32 levels) are rejected with `MatcherError`. This prevents stack overflow from deeply nested matcher evaluation.
