# Python API Reference

puma implements the xDS Unified Matcher API in pure Python. Zero dependencies. Python 3.12+.

**Package:** `puma` (from `puma/` directory)

**Installation:**
```bash
pip install puma
# or with uv
uv add puma
```

## Import Hierarchy

All public types exported flat from top level:

```python
from puma import (
    # Protocols
    DataInput, InputMatcher, MatchingData,
    # Predicates
    SinglePredicate, And, Or, Not, Predicate, predicate_depth,
    # Matcher
    Matcher, FieldMatcher, OnMatch, Action, NestedMatcher, MatcherError,
    # String matchers
    ExactMatcher, PrefixMatcher, SuffixMatcher, ContainsMatcher, RegexMatcher,
)

from puma.http import (
    # Context
    HttpRequest,
    # DataInputs
    PathInput, MethodInput, HeaderInput, QueryParamInput,
    # Gateway API types
    HttpPathMatch, HttpHeaderMatch, HttpQueryParamMatch, HttpRouteMatch,
    compile_route_matches,
)
```

## Type Hierarchy

```
┌─────────────────────────────────────┐
│          Matcher[Ctx, A]            │
│   Top-level tree, returns A|None    │
└───┬─────────────────────────────────┘
    │ contains
    ├──► FieldMatcher[Ctx, A]
    │       predicate + on_match
    │
    └──► OnMatch[Ctx, A]  (fallback)
         ├─ Action[A]
         └─ NestedMatcher[Ctx, A]

┌─────────────────────────────────────┐
│         Predicate[Ctx]              │
│      Boolean logic tree             │
└───┬─────────────────────────────────┘
    ├─ SinglePredicate[Ctx] → input + matcher
    ├─ And[Ctx] → all match
    ├─ Or[Ctx] → any match
    └─ Not[Ctx] → invert

┌─────────────────────────────────────┐
│    DataInput[Ctx] protocol          │
│   extract MatchingData from Ctx    │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│    InputMatcher protocol            │
│   match MatchingData → bool        │
└───┬─────────────────────────────────┘
    ├─ ExactMatcher
    ├─ PrefixMatcher
    ├─ SuffixMatcher
    ├─ ContainsMatcher
    └─ RegexMatcher
```

## Core Protocols

### MatchingData

```python
type MatchingData = str | int | bool | bytes | None
```

Type-erased value returned by `DataInput.get()`. Replaces Rust's `MatchingData` enum.

Returning `None` triggers the **None → false invariant**: predicate evaluates to `False` without consulting the matcher.

### DataInput[Ctx]

```python
class DataInput(Protocol[Ctx]):
    def get(self, ctx: Ctx, /) -> MatchingData: ...
```

Domain-specific extraction port. Implementations:
- `PathInput` extracts HTTP path
- `HeaderInput` extracts HTTP header by name
- Custom: implement this protocol for your domain

**Contravariant in Ctx** — accepts `Ctx` or any supertype.

### InputMatcher

```python
class InputMatcher(Protocol):
    def matches(self, value: MatchingData, /) -> bool: ...
```

Domain-agnostic matching port. Non-generic by design — same `ExactMatcher` works for HTTP, CloudEvent, or any custom domain.

## Predicates

### SinglePredicate[Ctx]

```python
@dataclass(frozen=True, slots=True)
class SinglePredicate[Ctx]:
    input: DataInput[Ctx]
    matcher: InputMatcher

    def evaluate(self, ctx: Any) -> bool: ...
```

Combines extraction + matching. Enforces the **None → false invariant**.

### And[Ctx]

```python
@dataclass(frozen=True, slots=True)
class And[Ctx]:
    predicates: tuple[Predicate[Ctx], ...]

    def evaluate(self, ctx: Any) -> bool: ...
```

All predicates must match. Short-circuits on first `False`. Empty tuple returns `True` (vacuous truth).

### Or[Ctx]

```python
@dataclass(frozen=True, slots=True)
class Or[Ctx]:
    predicates: tuple[Predicate[Ctx], ...]

    def evaluate(self, ctx: Any) -> bool: ...
```

Any predicate must match. Short-circuits on first `True`. Empty tuple returns `False`.

### Not[Ctx]

```python
@dataclass(frozen=True, slots=True)
class Not[Ctx]:
    predicate: Predicate[Ctx]

    def evaluate(self, ctx: Any) -> bool: ...
```

Inverts inner predicate result.

### Predicate[Ctx]

```python
type Predicate[Ctx] = SinglePredicate[Ctx] | And[Ctx] | Or[Ctx] | Not[Ctx]
```

Union type for pattern matching via `match`/`case`.

### predicate_depth()

```python
def predicate_depth(p: Predicate[Any]) -> int: ...
```

Calculate nesting depth of predicate tree. Used by `Matcher.validate()` for depth limit enforcement.

## Matcher Tree

### Matcher[Ctx, A]

```python
@dataclass(frozen=True, slots=True)
class Matcher[Ctx, A]:
    matcher_list: tuple[FieldMatcher[Ctx, A], ...]
    on_no_match: OnMatch[Ctx, A] | None = None

    def evaluate(self, ctx: Any) -> A | None: ...
    def validate(self) -> None: ...
    def depth(self) -> int: ...
```

Top-level matcher tree. Evaluates `matcher_list` in order (first-match-wins). Returns action `A` or `None`.

**Auto-validation:** `validate()` is called in `__post_init__`. Trees exceeding `MAX_DEPTH` (32) raise `MatcherError`.

**Methods:**
- `evaluate(ctx)` — Returns first matching action or `None`
- `validate()` — Checks depth limit (called automatically)
- `depth()` — Returns total tree depth

### FieldMatcher[Ctx, A]

```python
@dataclass(frozen=True, slots=True)
class FieldMatcher[Ctx, A]:
    predicate: Predicate[Ctx]
    on_match: OnMatch[Ctx, A]
```

Pairs a predicate with an outcome (action or nested matcher).

### OnMatch[Ctx, A]

```python
type OnMatch[Ctx, A] = Action[A] | NestedMatcher[Ctx, A]
```

xDS exclusivity — action XOR nested matcher, never both.

### Action[A]

```python
@dataclass(frozen=True, slots=True)
class Action[A]:
    value: A
```

Terminal outcome. Returns `value` when matched.

### NestedMatcher[Ctx, A]

```python
@dataclass(frozen=True, slots=True)
class NestedMatcher[Ctx, A]:
    matcher: Matcher[Ctx, A]
```

Continue evaluation into nested matcher. If nested matcher returns `None`, evaluation continues to next `FieldMatcher` (xDS nested matcher failure propagation).

### MatcherError

```python
class MatcherError(Exception): ...
```

Raised when `validate()` detects depth exceeding `MAX_DEPTH`.

### MAX_DEPTH

```python
MAX_DEPTH: int = 32
```

Maximum allowed matcher tree depth. Enforced at construction time.

## String Matchers

All matchers are frozen dataclasses implementing `InputMatcher` protocol. Return `False` for non-string or `None` input.

### ExactMatcher

```python
@dataclass(frozen=True, slots=True)
class ExactMatcher:
    value: str
    ignore_case: bool = False

    def matches(self, value: MatchingData, /) -> bool: ...
```

Exact string equality. When `ignore_case=True`, comparison uses `.casefold()`.

**Optimization:** Pattern is pre-lowercased at construction time (`_cmp_value` field).

### PrefixMatcher

```python
@dataclass(frozen=True, slots=True)
class PrefixMatcher:
    prefix: str
    ignore_case: bool = False

    def matches(self, value: MatchingData, /) -> bool: ...
```

String starts with prefix. Pre-lowercased at construction when `ignore_case=True`.

### SuffixMatcher

```python
@dataclass(frozen=True, slots=True)
class SuffixMatcher:
    suffix: str
    ignore_case: bool = False

    def matches(self, value: MatchingData, /) -> bool: ...
```

String ends with suffix. Pre-lowercased at construction when `ignore_case=True`.

### ContainsMatcher

```python
@dataclass(frozen=True, slots=True)
class ContainsMatcher:
    substring: str
    ignore_case: bool = False

    def matches(self, value: MatchingData, /) -> bool: ...
```

Substring search. Pre-lowercased at construction when `ignore_case=True` (Knuth optimization: avoid repeated pattern lowercasing).

### RegexMatcher

```python
@dataclass(frozen=True, slots=True)
class RegexMatcher:
    pattern: str

    def matches(self, value: MatchingData, /) -> bool: ...
```

Regular expression search (not fullmatch). Pattern compiled at construction time.

**Security:** Uses Python `re` module (backtracking NFA, ReDoS-vulnerable). See `SECURITY.md` in the puma package for details. For adversarial input, use `puma-crusty` (Phase 7).

## HTTP Domain

### HttpRequest

```python
@dataclass(frozen=True, slots=True)
class HttpRequest:
    method: str = "GET"
    raw_path: str = "/"
    headers: dict[str, str] = field(default_factory=dict)

    @property
    def path(self) -> str: ...
    @property
    def query_params(self) -> dict[str, str]: ...
    def header(self, name: str) -> str | None: ...
    def query_param(self, name: str) -> str | None: ...
```

HTTP request context for matching.

**Parsing:** Query string automatically parsed from `raw_path`. Headers stored lowercased for case-insensitive lookup.

**Properties:**
- `path` — path without query string
- `query_params` — parsed query parameters

**Methods:**
- `header(name)` — Case-insensitive header lookup
- `query_param(name)` — Query parameter lookup

### DataInputs

#### PathInput

```python
@dataclass(frozen=True, slots=True)
class PathInput:
    def get(self, ctx: HttpRequest, /) -> MatchingData: ...
```

Extracts `ctx.path` (without query string).

#### MethodInput

```python
@dataclass(frozen=True, slots=True)
class MethodInput:
    def get(self, ctx: HttpRequest, /) -> MatchingData: ...
```

Extracts HTTP method (case-sensitive).

#### HeaderInput

```python
@dataclass(frozen=True, slots=True)
class HeaderInput:
    name: str

    def get(self, ctx: HttpRequest, /) -> MatchingData: ...
```

Extracts header value by name (case-insensitive lookup). Returns `None` if header not present.

#### QueryParamInput

```python
@dataclass(frozen=True, slots=True)
class QueryParamInput:
    name: str

    def get(self, ctx: HttpRequest, /) -> MatchingData: ...
```

Extracts query parameter value by name. Returns `None` if parameter not present.

### Gateway API Types

Pure Python types mirroring Gateway API spec (no Kubernetes dependency).

#### HttpPathMatch

```python
@dataclass(frozen=True, slots=True)
class HttpPathMatch:
    type: Literal["Exact", "PathPrefix", "RegularExpression"]
    value: str
```

Path match specification.

#### HttpHeaderMatch

```python
@dataclass(frozen=True, slots=True)
class HttpHeaderMatch:
    type: Literal["Exact", "RegularExpression"]
    name: str
    value: str
```

Header match specification.

#### HttpQueryParamMatch

```python
@dataclass(frozen=True, slots=True)
class HttpQueryParamMatch:
    type: Literal["Exact", "RegularExpression"]
    name: str
    value: str
```

Query parameter match specification.

#### HttpRouteMatch

```python
@dataclass(frozen=True, slots=True)
class HttpRouteMatch:
    path: HttpPathMatch | None = None
    method: str | None = None
    headers: list[HttpHeaderMatch] = field(default_factory=list)
    query_params: list[HttpQueryParamMatch] = field(default_factory=list)

    def compile[A](self, action: A) -> Matcher[HttpRequest, A]: ...
    def to_predicate(self) -> Predicate[HttpRequest]: ...
```

Gateway API route match config. All conditions within a single `HttpRouteMatch` are ANDed.

**Methods:**
- `compile(action)` — Build a `Matcher` with this match → action
- `to_predicate()` — Convert to predicate tree (used by compiler)

### compile_route_matches()

```python
def compile_route_matches[A](
    matches: list[HttpRouteMatch],
    action: A,
    on_no_match: A | None = None,
) -> Matcher[HttpRequest, A]: ...
```

Compile multiple `HttpRouteMatch` entries into a single `Matcher`. Multiple matches are ORed per Gateway API semantics.

**Example:**
```python
matcher = compile_route_matches(
    matches=[api_route, admin_route],
    action="matched",
    on_no_match="404",
)
```

## Requirements

- **Python 3.12+** — uses PEP 695 type parameter syntax (`class Foo[T]:`)
- **Zero dependencies** — pure Python stdlib only
- **py.typed** — PEP 561 marker included, downstream type checkers (mypy, pyright) recognize puma as typed

## Security

See `SECURITY.md` in the puma package for ReDoS risk and mitigation.

**Summary:**
- `RegexMatcher` uses Python `re` (backtracking, ReDoS-vulnerable)
- Safe for trusted patterns (your route config, known fixtures)
- For adversarial input, use `puma-crusty` (Rust-backed, linear-time regex)
- Depth validation automatic at construction (max 32 levels)
