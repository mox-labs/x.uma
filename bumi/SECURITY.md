# Security -- bumi

## Regex Engine: ReDoS Risk

bumi uses JavaScript's `RegExp` for `RegexMatcher`. The V8/JSC regex engine employs a **backtracking NFA** that is vulnerable to catastrophic backtracking (ReDoS) on pathological patterns.

The Rust reference implementation (rumi) uses the `regex` crate, which provides **linear-time matching guarantees** via Thompson NFA construction -- making ReDoS impossible by design.

### What This Means

- **Trusted input**: bumi is safe when regex patterns come from trusted configuration (your own route definitions, known fixtures).
- **Adversarial input**: If regex patterns originate from untrusted sources (user-submitted config, external APIs), an attacker can craft pathological patterns like `(a+)+$` that cause exponential CPU consumption.

### Mitigation

For environments processing adversarial input, use **crusty-bumi** -- the Rust-backed WASM package that provides the same API with linear-time regex via wasm-bindgen bindings to rumi's `regex` crate.

| Package | Regex Engine | ReDoS Safe | Dependencies |
|---------|-------------|------------|--------------|
| bumi | JS `RegExp` (backtracking) | No | Zero |
| crusty-bumi | Rust `regex` (linear-time) | Yes | WASM binary |

### Invalid Regex Patterns

`RegexMatcher` validates patterns at construction time. Invalid regex patterns (e.g., `[unclosed`) are rejected with `MatcherError` rather than propagating a raw `SyntaxError`. This ensures callers only need to handle a single error type from the bumi API.

### Depth Limits

Matcher trees are validated at construction time. Trees exceeding `MAX_DEPTH` (32 levels) are rejected with `MatcherError`. This prevents stack overflow from deeply nested matcher evaluation.

### Prototype Safety

HTTP request parsing uses null-prototype objects (`Object.create(null)`) for header and query parameter storage. This prevents prototype pollution attacks where user-supplied keys like `__proto__` or `constructor` could collide with inherited `Object.prototype` properties.
