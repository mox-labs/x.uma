# Quick Start

Get x.uma running in your project. Both Rust and Python follow the same pattern: define your context, implement DataInput to extract values, build a matcher tree, evaluate.

## Rust

### Install

Add to your `Cargo.toml`:

```toml
[dependencies]
rumi = "0.1"
```

### Basic Example: Match a Dict-like Struct

Start with the simplest case — extract a value from a struct and match it.

```rust,ignore
use rumi::prelude::*;

// 1. Define your context
#[derive(Debug)]
struct User {
    name: String,
}

// 2. Implement DataInput to extract data
#[derive(Debug)]
struct NameInput;

impl DataInput<User> for NameInput {
    fn get(&self, ctx: &User) -> MatchingData {
        MatchingData::String(ctx.name.clone())
    }
}

// 3. Build a matcher
let matcher: Matcher<User, &str> = Matcher::new(
    vec![
        FieldMatcher::new(
            Predicate::Single(SinglePredicate::new(
                Box::new(NameInput),
                Box::new(ExactMatcher::new("alice")),
            )),
            OnMatch::Action("admin"),
        ),
        FieldMatcher::new(
            Predicate::Single(SinglePredicate::new(
                Box::new(NameInput),
                Box::new(ExactMatcher::new("bob")),
            )),
            OnMatch::Action("user"),
        ),
    ],
    Some(OnMatch::Action("guest")),
);

// 4. Evaluate
let user = User { name: "alice".into() };
assert_eq!(matcher.evaluate(&user), Some("admin"));

let user = User { name: "eve".into() };
assert_eq!(matcher.evaluate(&user), Some("guest"));
```

**What happened:**
- `NameInput` extracts the name field (DataInput port)
- `ExactMatcher` checks if the name matches (InputMatcher port)
- `SinglePredicate` combines extraction + matching
- `Matcher` evaluates predicates in order, returns the first match
- `on_no_match` provides a fallback when nothing matches

### HTTP Matching

Now apply the same pattern to HTTP requests.

```rust,ignore
use rumi::prelude::*;
use rumi_http::{HttpMessage, PathInput, PrefixMatcher};

let matcher = Matcher::new(
    vec![
        FieldMatcher::new(
            Predicate::Single(SinglePredicate::new(
                Box::new(PathInput),
                Box::new(PrefixMatcher::new("/api")),
            )),
            OnMatch::Action("api_handler"),
        ),
        FieldMatcher::new(
            Predicate::Single(SinglePredicate::new(
                Box::new(PathInput),
                Box::new(PrefixMatcher::new("/admin")),
            )),
            OnMatch::Action("admin_handler"),
        ),
    ],
    Some(OnMatch::Action("default")),
);

// HttpMessage is the indexed view over ext_proc ProcessingRequest
// It provides O(1) header/query lookups
let action = matcher.evaluate(&http_message);
```

Under the hood, `PathInput` implements `DataInput<HttpMessage>` and extracts the request path. The same `PrefixMatcher` works here because `InputMatcher` is domain-agnostic.

## Python

### Install

```bash
pip install puma
# or with uv
uv add puma
```

Requires Python 3.12+ (uses PEP 695 type parameter syntax).

### Basic Example: Match a Dictionary

Start with the simplest case — extract a value from a dict and match it.

```python
from puma import Matcher, FieldMatcher, SinglePredicate, ExactMatcher, Action
from dataclasses import dataclass

# 1. Define a data input (extraction port)
@dataclass(frozen=True, slots=True)
class DictInput:
    key: str

    def get(self, ctx: dict[str, str], /) -> str | None:
        return ctx.get(self.key)

# 2. Build a matcher tree
matcher = Matcher(
    matcher_list=(
        FieldMatcher(
            predicate=SinglePredicate(
                input=DictInput("name"),
                matcher=ExactMatcher("alice")
            ),
            on_match=Action("admin")
        ),
        FieldMatcher(
            predicate=SinglePredicate(
                input=DictInput("name"),
                matcher=ExactMatcher("bob")
            ),
            on_match=Action("user")
        ),
    ),
    on_no_match=Action("guest")
)

# 3. Evaluate
matcher.evaluate({"name": "alice"})  # "admin"
matcher.evaluate({"name": "bob"})    # "user"
matcher.evaluate({"name": "eve"})    # "guest"
matcher.evaluate({})                 # "guest"
```

**What happened:**
- `DictInput` extracts a value from the dict (DataInput protocol)
- `ExactMatcher` checks if that value matches (InputMatcher protocol)
- `SinglePredicate` combines extraction + matching
- `Matcher` evaluates predicates in order, returns the first match
- `on_no_match` provides a fallback when nothing matches

This is the core pattern. Everything else builds on it.

### HTTP Matching

Now the same pattern applied to HTTP — match requests against route rules.

```python
from puma.http import HttpRequest, HttpPathMatch, HttpRouteMatch, compile_route_matches

# Define route rules (Gateway API style)
api_route = HttpRouteMatch(
    path=HttpPathMatch(type="PathPrefix", value="/api"),
    method="GET"
)

admin_route = HttpRouteMatch(
    path=HttpPathMatch(type="PathPrefix", value="/admin"),
)

# Compile to a matcher
matcher = compile_route_matches(
    matches=[api_route, admin_route],
    action="matched",
    on_no_match="404"
)

# Evaluate requests
req1 = HttpRequest(method="GET", raw_path="/api/users")
matcher.evaluate(req1)  # "matched" (api_route)

req2 = HttpRequest(method="POST", raw_path="/api/users")
matcher.evaluate(req2)  # "404" (wrong method)

req3 = HttpRequest(raw_path="/admin/settings")
matcher.evaluate(req3)  # "matched" (admin_route)
```

Under the hood, `compile_route_matches` builds the same `Matcher` tree you saw in the basic example, using `PathInput`, `MethodInput`, `HeaderInput`, and `QueryParamInput`. These implement `DataInput[HttpRequest]` and extract the relevant fields.

## Next Steps

- [Concepts](concepts.md) — understand the core abstractions
- [Adding a Domain](../guides/adding-domain.md) — create domain-specific matchers
- [Python API Reference](../reference/python.md) — full puma API
- [Rust API Reference](../reference/rust.md) — full rumi API
