# Concepts

Core abstractions in x.uma. The same concepts apply across Rust and Python implementations.

## The Matching Pipeline

```text
Context → DataInput → MatchingValue → InputMatcher → bool
                                           ↓
                       Predicate (AND/OR/NOT composition)
                                           ↓
                               Matcher (first-match-wins)
                                           ↓
                                        Action
```

Each step is a port. Domain-specific adapters plug in at the edges. The core is domain-agnostic.

## Key Types

### MatchingValue (Type-Erased Data)

Matchers operate on type-erased data. This is what allows the same `ExactMatcher` to work for HTTP headers, event types, or custom domains.

**Rust:**

```rust,ignore
pub enum MatchingData {
    None,
    String(String),
    Int(i64),
    Bool(bool),
    Bytes(Vec<u8>),
    Custom(Arc<dyn CustomMatchData>),  // Extensible
}
```

**Python:**

```python
# Type alias — Python gets union types for free
MatchingValue = str | int | bool | bytes | None
```

Python's union type replaces Rust's enum. Both serve the same purpose: type erasure at the data level.

### DataInput (Extraction Port)

Extracts data from your domain context. Domain-specific and generic over the context type.

**Rust:**

```rust,ignore
pub trait DataInput<Ctx>: Send + Sync {
    fn get(&self, ctx: &Ctx) -> MatchingData;
}
```

**Python:**

```python
@runtime_checkable
class DataInput(Protocol[Ctx]):
    """Extract a value from a domain-specific context."""
    def get(self, ctx: Ctx, /) -> MatchingValue: ...
```

Python uses `Protocol` (structural typing) instead of Rust's trait. Both define the extraction port contract.

**Examples:**

| Domain | Rust | Python |
|--------|------|--------|
| HTTP path | `PathInput` (rumi-http) | `PathInput()` (puma.http) |
| HTTP header | `HeaderInput { name }` | `HeaderInput(name)` |
| Dict key | (custom) | `DictInput(key)` |
| Event type | (custom) | `EventTypeInput()` |

### InputMatcher (Matching Port)

Matches against the type-erased value. Domain-agnostic and non-generic.

**Rust:**

```rust,ignore
pub trait InputMatcher: Send + Sync {
    fn matches(&self, value: &MatchingData) -> bool;
}
```

**Python:**

```python
@runtime_checkable
class InputMatcher(Protocol):
    """Match against a type-erased value."""
    def matches(self, value: MatchingValue, /) -> bool: ...
```

**The key insight:** `InputMatcher` is non-generic. The same `ExactMatcher` works for any domain because it operates on `MatchingData` / `MatchingValue`, not the original context type.

Built-in matchers:

| Matcher | Matches | Rust | Python |
|---------|---------|------|--------|
| Exact | Exact equality | `ExactMatcher::new("foo")` | `ExactMatcher("foo")` |
| Prefix | String starts with | `PrefixMatcher::new("/api")` | `PrefixMatcher("/api")` |
| Suffix | String ends with | `SuffixMatcher::new(".json")` | `SuffixMatcher(".json")` |
| Contains | Substring present | `ContainsMatcher::new("world")` | `ContainsMatcher("world")` |
| Regex | Regex search | `RegexMatcher::new(r"\d+")` | `RegexMatcher(r"\d+")` |

All matchers (except `RegexMatcher`) support optional case-insensitive matching via `ignore_case`.

### Predicate (Boolean Composition)

Combines `DataInput` + `InputMatcher` with boolean logic.

**Rust:**

```rust,ignore
pub enum Predicate<Ctx> {
    Single(SinglePredicate<Ctx>),  // extract + match
    And(Vec<Predicate<Ctx>>),      // all must match
    Or(Vec<Predicate<Ctx>>),       // any must match
    Not(Box<Predicate<Ctx>>),      // negation
}

pub struct SinglePredicate<Ctx> {
    input: Box<dyn DataInput<Ctx>>,
    matcher: Box<dyn InputMatcher>,
}
```

**Python:**

```python
@dataclass(frozen=True, slots=True)
class SinglePredicate[Ctx]:
    input: DataInput[Ctx]
    matcher: InputMatcher

@dataclass(frozen=True, slots=True)
class And[Ctx]:
    predicates: tuple[Predicate[Ctx], ...]

@dataclass(frozen=True, slots=True)
class Or[Ctx]:
    predicates: tuple[Predicate[Ctx], ...]

@dataclass(frozen=True, slots=True)
class Not[Ctx]:
    predicate: Predicate[Ctx]

# Union type (replaces Rust's enum)
type Predicate[Ctx] = SinglePredicate[Ctx] | And[Ctx] | Or[Ctx] | Not[Ctx]
```

Python uses a type alias union instead of an enum. Both are pattern-matchable in their respective languages.

**Short-circuit evaluation:**
- `And` returns `False` on the first non-matching predicate
- `Or` returns `True` on the first matching predicate

### OnMatch (Action or Nested Matcher)

What happens when a predicate matches. Exclusive: action XOR nested matcher, never both.

**Rust:**

```rust,ignore
pub enum OnMatch<Ctx, A> {
    Action(A),              // Terminal: return this action
    Matcher(Box<Matcher>),  // Nested: evaluate another matcher
}
```

**Python:**

```python
@dataclass(frozen=True, slots=True)
class Action[A]:
    value: A

@dataclass(frozen=True, slots=True)
class NestedMatcher[Ctx, A]:
    matcher: Matcher[Ctx, A]

# Type alias (replaces Rust's enum)
type OnMatch[Ctx, A] = Action[A] | NestedMatcher[Ctx, A]
```

The exclusivity is enforced by the type system — illegal states are unrepresentable.

### Matcher (First-Match-Wins)

Top-level container. Evaluates field matchers in order and returns the action from the first match.

**Rust:**

```rust,ignore
pub struct Matcher<Ctx, A> {
    matcher_list: Vec<FieldMatcher<Ctx, A>>,
    on_no_match: Option<OnMatch<Ctx, A>>,
}

pub struct FieldMatcher<Ctx, A> {
    predicate: Predicate<Ctx>,
    on_match: OnMatch<Ctx, A>,
}
```

**Python:**

```python
@dataclass(frozen=True, slots=True)
class Matcher[Ctx, A]:
    matcher_list: tuple[FieldMatcher[Ctx, A], ...]
    on_no_match: OnMatch[Ctx, A] | None = None

@dataclass(frozen=True, slots=True)
class FieldMatcher[Ctx, A]:
    predicate: Predicate[Ctx]
    on_match: OnMatch[Ctx, A]
```

**Evaluation semantics (xDS):**

1. **First-match-wins** — Evaluate field matchers in order. Return the action from the first matching predicate. Later matches are never consulted.

2. **OnMatch exclusivity** — Each `OnMatch` is either an `Action` (terminal) or a nested `Matcher`, never both.

3. **Nested matcher failure propagates** — If a nested matcher returns `None`, evaluation continues to the next field matcher (no implicit fallback).

4. **on_no_match fallback** — If no predicate matches, `on_no_match` is consulted. If absent, the matcher returns `None`.

5. **None → false invariant** — If a `DataInput` returns `None`, the predicate evaluates to `False` without consulting the matcher.

6. **Depth validation** — Matcher trees exceeding `MAX_DEPTH` (32 levels) are rejected at construction.

## Type Comparison

| Concept | Rust Type | Python Type |
|---------|-----------|-------------|
| Type-erased data | `enum MatchingData` | `type MatchingValue = str \| int \| bool \| bytes \| None` |
| Extraction port | `trait DataInput<Ctx>` | `Protocol[Ctx]` with `get()` |
| Matching port | `trait InputMatcher` | `Protocol` with `matches()` |
| Boolean logic | `enum Predicate<Ctx>` | `type Predicate = Single \| And \| Or \| Not` |
| Action/nested | `enum OnMatch<Ctx, A>` | `type OnMatch = Action \| NestedMatcher` |
| Top-level | `struct Matcher<Ctx, A>` | `@dataclass Matcher[Ctx, A]` |

Same concepts, idiomatic types for each language.

## Next Steps

- [Architecture](../explain/architecture.md) — why this design
- [Adding a Domain](../guides/adding-domain.md) — create custom matchers
- [HTTP Domain Reference](../reference/http.md) — HTTP-specific types
