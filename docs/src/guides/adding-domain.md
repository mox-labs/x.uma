# Adding a Domain

Create domain-specific matchers for HTTP, gRPC, CloudEvents, or your custom protocol.

A "domain" in x.uma is a context type with associated `DataInput` implementations. This guide shows how to add a domain in both Rust (rumi) and Python (puma).

## Concept: CloudEvent Matching

We'll build a matcher for [CloudEvents](https://cloudevents.io/) — a CNCF spec for event metadata.

```json
{
  "specversion": "1.0",
  "type": "com.example.user.created",
  "source": "api-server",
  "id": "abc-123",
  "subject": "user/42"
}
```

**Goal:** Match events by type, source, or subject.

## Python Implementation (puma)

### Step 1: Define the Context Type

```python
# my_events.py
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class CloudEvent:
    """CloudEvents v1.0 context."""
    type: str
    source: str
    id: str
    subject: str | None = None
```

### Step 2: Implement DataInput

```python
from puma import DataInput, MatchingValue

@dataclass(frozen=True, slots=True)
class EventTypeInput:
    """Extract event type."""
    def get(self, ctx: CloudEvent, /) -> MatchingValue:
        return ctx.type

@dataclass(frozen=True, slots=True)
class EventSourceInput:
    """Extract event source."""
    def get(self, ctx: CloudEvent, /) -> MatchingValue:
        return ctx.source

@dataclass(frozen=True, slots=True)
class EventSubjectInput:
    """Extract event subject (may be None)."""
    def get(self, ctx: CloudEvent, /) -> MatchingValue:
        return ctx.subject  # None triggers None → false invariant
```

### Step 3: Build Matchers

```python
from puma import (
    Matcher, FieldMatcher, SinglePredicate, Action,
    ExactMatcher, PrefixMatcher, And,
)

# Match user creation events from api-server
user_created_matcher = Matcher(
    matcher_list=(
        FieldMatcher(
            predicate=And((
                SinglePredicate(
                    EventTypeInput(),
                    PrefixMatcher("com.example.user.")
                ),
                SinglePredicate(
                    EventSourceInput(),
                    ExactMatcher("api-server")
                ),
            )),
            on_match=Action("handle_user_event"),
        ),
    ),
    on_no_match=Action("ignore"),
)

# Evaluate
event = CloudEvent(
    type="com.example.user.created",
    source="api-server",
    id="abc-123",
)
action = user_created_matcher.evaluate(event)
assert action == "handle_user_event"
```

### Step 4: Optional Compiler (Gateway API Style)

For ergonomic config-time APIs, add a compiler:

```python
from dataclasses import dataclass, field
from typing import Literal
from puma import Predicate, SinglePredicate, ExactMatcher, PrefixMatcher, Matcher, FieldMatcher, Action

@dataclass(frozen=True, slots=True)
class EventMatch:
    """Config-time event match specification."""
    type: str | None = None
    source: str | None = None
    subject: str | None = None

    def to_predicate(self) -> Predicate[CloudEvent]:
        """Compile to predicate tree."""
        predicates: list[SinglePredicate[CloudEvent]] = []

        if self.type is not None:
            predicates.append(
                SinglePredicate(EventTypeInput(), ExactMatcher(self.type))
            )
        if self.source is not None:
            predicates.append(
                SinglePredicate(EventSourceInput(), ExactMatcher(self.source))
            )
        if self.subject is not None:
            predicates.append(
                SinglePredicate(EventSubjectInput(), ExactMatcher(self.subject))
            )

        if not predicates:
            # Match everything
            return SinglePredicate(EventTypeInput(), PrefixMatcher(""))

        if len(predicates) == 1:
            return predicates[0]

        return And(tuple(predicates))

    def compile[A](self, action: A) -> Matcher[CloudEvent, A]:
        """Compile to matcher."""
        return Matcher(
            matcher_list=(FieldMatcher(self.to_predicate(), Action(action)),),
        )

# Usage
match_config = EventMatch(type="com.example.user.created", source="api-server")
matcher = match_config.compile("handle_user_event")
```

That's it. The same string matchers, predicates, and matcher tree logic work for CloudEvents.

## Rust Implementation (rumi)

### Step 1: Define Proto (Optional)

If using xDS proto extension mechanism:

```protobuf
// proto/xuma/events/v1/inputs.proto
syntax = "proto3";
package xuma.events.v1;

message EventTypeInput {}
message EventSourceInput {}
message EventSubjectInput {}
```

Generate Rust bindings:
```bash
just gen
```

### Step 2: Define the Context Type

```rust
// rumi/ext/events/src/lib.rs
use std::collections::HashMap;

#[derive(Debug, Clone)]
pub struct CloudEvent {
    pub event_type: String,
    pub source: String,
    pub id: String,
    pub subject: Option<String>,
}
```

### Step 3: Implement DataInput

```rust
use rumi::{DataInput, MatchingData};

#[derive(Debug)]
pub struct EventTypeInput;

impl DataInput<CloudEvent> for EventTypeInput {
    fn get(&self, ctx: &CloudEvent) -> MatchingData {
        MatchingData::String(ctx.event_type.clone())
    }
}

#[derive(Debug)]
pub struct EventSourceInput;

impl DataInput<CloudEvent> for EventSourceInput {
    fn get(&self, ctx: &CloudEvent) -> MatchingData {
        MatchingData::String(ctx.source.clone())
    }
}

#[derive(Debug)]
pub struct EventSubjectInput;

impl DataInput<CloudEvent> for EventSubjectInput {
    fn get(&self, ctx: &CloudEvent) -> MatchingData {
        ctx.subject
            .as_ref()
            .map(|s| MatchingData::String(s.clone()))
            .unwrap_or(MatchingData::None)
    }
}
```

### Step 4: Build Matchers

```rust
use rumi::prelude::*;

// Match user creation events from api-server
let user_created_matcher = Matcher::new(
    vec![
        FieldMatcher::new(
            Predicate::And {
                predicates: vec![
                    Predicate::Single(SinglePredicate::new(
                        Box::new(EventTypeInput),
                        Box::new(PrefixMatcher::new("com.example.user.")),
                    )),
                    Predicate::Single(SinglePredicate::new(
                        Box::new(EventSourceInput),
                        Box::new(ExactMatcher::new("api-server")),
                    )),
                ],
            },
            OnMatch::Action("handle_user_event"),
        ),
    ],
    Some(OnMatch::Action("ignore")),
)?;

// Evaluate
let event = CloudEvent {
    event_type: "com.example.user.created".into(),
    source: "api-server".into(),
    id: "abc-123".into(),
    subject: None,
};

let action = user_created_matcher.evaluate(&event);
assert_eq!(action, Some("handle_user_event"));
```

### Step 5: Optional Compiler (Gateway API Style)

```rust
#[derive(Debug, Clone)]
pub struct EventMatch {
    pub event_type: Option<String>,
    pub source: Option<String>,
    pub subject: Option<String>,
}

impl EventMatch {
    pub fn compile<A>(self, action: A) -> Result<Matcher<CloudEvent, A>, MatcherError>
    where
        A: Clone,
    {
        let predicate = self.to_predicate();
        Matcher::new(
            vec![FieldMatcher::new(predicate, OnMatch::Action(action))],
            None,
        )
    }

    fn to_predicate(&self) -> Predicate<CloudEvent> {
        let mut predicates = Vec::new();

        if let Some(ref t) = self.event_type {
            predicates.push(Predicate::Single(SinglePredicate::new(
                Box::new(EventTypeInput),
                Box::new(ExactMatcher::new(t)),
            )));
        }
        if let Some(ref s) = self.source {
            predicates.push(Predicate::Single(SinglePredicate::new(
                Box::new(EventSourceInput),
                Box::new(ExactMatcher::new(s)),
            )));
        }
        if let Some(ref subj) = self.subject {
            predicates.push(Predicate::Single(SinglePredicate::new(
                Box::new(EventSubjectInput),
                Box::new(ExactMatcher::new(subj)),
            )));
        }

        if predicates.is_empty() {
            // Match everything
            Predicate::Single(SinglePredicate::new(
                Box::new(EventTypeInput),
                Box::new(PrefixMatcher::new("")),
            ))
        } else if predicates.len() == 1 {
            predicates.into_iter().next().unwrap()
        } else {
            Predicate::And { predicates }
        }
    }
}

// Usage
let match_config = EventMatch {
    event_type: Some("com.example.user.created".into()),
    source: Some("api-server".into()),
    subject: None,
};
let matcher = match_config.compile("handle_user_event")?;
```

## Add Conformance Tests

Both implementations should pass the same test fixtures.

```yaml
# spec/tests/events/type_exact.yaml
name: "CloudEvent type exact match"
context:
  type: "com.example.user.created"
  source: "api-server"
  id: "abc-123"
cases:
  - description: "matches event type"
    matcher:
      input: { event_type: {} }
      matcher: { exact: "com.example.user.created" }
    expected: { matches: true }

  - description: "rejects wrong type"
    matcher:
      input: { event_type: {} }
      matcher: { exact: "com.example.order.created" }
    expected: { matches: false }
```

**Test runners:**
- Rust: Parse YAML, construct `CloudEvent` and `Matcher<CloudEvent, _>`, assert
- Python: Parse YAML, construct `CloudEvent` and `Matcher[CloudEvent, _]`, assert

## Key Patterns

### None Handling

When a `DataInput` returns `None` (Rust) or `None` (Python), the predicate evaluates to `False` without consulting the matcher. This is the **None → false invariant**.

```python
# Python
@dataclass(frozen=True, slots=True)
class EventSubjectInput:
    def get(self, ctx: CloudEvent, /) -> MatchingValue:
        return ctx.subject  # May be None

# If subject is None, predicate returns False
```

```rust
// Rust
impl DataInput<CloudEvent> for EventSubjectInput {
    fn get(&self, ctx: &CloudEvent) -> MatchingData {
        ctx.subject
            .as_ref()
            .map(|s| MatchingData::String(s.clone()))
            .unwrap_or(MatchingData::None)  // Triggers None → false
    }
}
```

### Immutability

All context types should be immutable:

| Language | Pattern |
|----------|---------|
| Rust | Don't provide `&mut` access, clone when needed |
| Python | `@dataclass(frozen=True)` |
| TypeScript | `readonly` fields |

### Type Safety

The compiler ensures:
- `DataInput<CloudEvent>` can only be used with `Matcher<CloudEvent, A>`
- You can't accidentally mix HTTP and CloudEvent inputs in the same matcher
- `OnMatch` is exclusive — action XOR nested matcher, never both

## See Also

- [Python API Reference](../reference/python.md) — puma types
- [Rust API Reference](../reference/rust.md) — rumi types
- [HTTP Domain](../reference/http.md) — Real-world example
- [Architecture](../explain/architecture.md) — Type system deep dive
