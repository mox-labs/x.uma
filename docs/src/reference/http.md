# HTTP Domain Reference

HTTP request matching across rumi (Rust) and puma (Python).

## Overview

Both implementations provide the same HTTP matching capabilities with Gateway API-style config and DataInput implementations for HTTP contexts.

**For Python users:** See [Python API Reference](python.md) for the `puma.http` module.

**This page focuses on Rust (rumi-http).**

## Architecture (rumi-http)

```
Gateway API HttpRouteMatch (config)
        ↓ compile()
rumi Matcher<HttpMessage, A>
        ↓ evaluate()
ext_proc ProcessingRequest (runtime)
```

**Two layers:**
- **User API**: Gateway API `HttpRouteMatch` — human-friendly config
- **Data Plane API**: Envoy `ProcessingRequest` — wire protocol (indexed as `HttpMessage`)

## Quick Start

```rust
use rumi_http::prelude::*;

// Config time: compile Gateway API match to rumi matcher
let route_match = HttpRouteMatch {
    path: Some(HttpPathMatch::PathPrefix { value: "/api".into() }),
    method: Some("GET".into()),
    ..Default::default()
};
let matcher = route_match.compile("api_backend");

// Runtime: evaluate against HttpMessage (indexed view over ProcessingRequest)
let result = matcher.evaluate(&http_message);
assert_eq!(result, Some("api_backend"));
```

## DataInputs for HttpMessage

| Input | Extracts | Example |
|-------|----------|---------|
| `PathInput` | `:path` pseudo-header (without query) | `/api/users` |
| `MethodInput` | `:method` pseudo-header | `GET` |
| `HeaderInput::new("x-api-key")` | Named header | `Bearer ...` |
| `QueryParamInput::new("page")` | Query parameter | `1` |
| `SchemeInput` | `:scheme` pseudo-header | `https` |
| `AuthorityInput` | `:authority` pseudo-header | `api.example.com` |

## Gateway API Match Types

### Path Matching

```rust
// Exact match
HttpPathMatch::Exact { value: "/api/v1/users".into() }

// Prefix match
HttpPathMatch::PathPrefix { value: "/api".into() }

// Regex match
HttpPathMatch::RegularExpression { value: r"^/api/v\d+/.*".into() }
```

### Header Matching

```rust
// Exact header value
HttpHeaderMatch::Exact {
    name: "content-type".into(),
    value: "application/json".into()
}

// Regex header value
HttpHeaderMatch::RegularExpression {
    name: "authorization".into(),
    value: r"^Bearer .+".into()
}
```

### Query Parameter Matching

```rust
// Exact param value
HttpQueryParamMatch::Exact {
    name: "version".into(),
    value: "2".into()
}

// Regex param value
HttpQueryParamMatch::RegularExpression {
    name: "id".into(),
    value: r"^\d+$".into()
}
```

## Match Semantics

Per Gateway API spec:
- **Within a match**: All conditions are ANDed
- **Multiple matches**: ORed together

```rust
// This matches: GET /api/* with x-version header
let route_match = HttpRouteMatch {
    path: Some(HttpPathMatch::PathPrefix { value: "/api".into() }),
    method: Some("GET".into()),
    headers: Some(vec![
        HttpHeaderMatch::Exact {
            name: "x-version".into(),
            value: "2".into()
        }
    ]),
    ..Default::default()
};
```

## Compiling Multiple Matches

```rust
use rumi_http::compile_route_matches;

let matches = vec![
    HttpRouteMatch {
        path: Some(HttpPathMatch::PathPrefix { value: "/api".into() }),
        ..Default::default()
    },
    HttpRouteMatch {
        path: Some(HttpPathMatch::PathPrefix { value: "/health".into() }),
        ..Default::default()
    },
];

// Multiple matches are ORed
let matcher = compile_route_matches(&matches, "backend", None);
```

## Python Equivalent

See [Python API Reference](python.md) for the Python implementation.

Quick comparison:

**Rust (rumi-http):**
```rust
use rumi_http::{HttpRouteMatch, HttpPathMatch, compile_route_matches};

let route = HttpRouteMatch {
    path: Some(HttpPathMatch::PathPrefix { value: "/api".into() }),
    method: Some("GET".into()),
    ..Default::default()
};
let matcher = route.compile("api_backend");
```

**Python (puma.http):**
```python
from puma.http import HttpRouteMatch, HttpPathMatch, compile_route_matches

route = HttpRouteMatch(
    path=HttpPathMatch(type="PathPrefix", value="/api"),
    method="GET",
)
matcher = route.compile("api_backend")
```

Both produce functionally identical matchers that pass the same conformance tests.

## Dependencies (Rust)

| Crate | Purpose |
|-------|---------|
| `k8s-gateway-api` | Gateway API types |
| `envoy-grpc-ext-proc` | ext_proc ProcessingRequest types |

## See Also

- [Python API Reference](python.md) — puma.http module
- [Gateway API HTTPRoute Spec](https://gateway-api.sigs.k8s.io/reference/spec/#gateway.networking.k8s.io/v1.HTTPRouteMatch)
- [Envoy ext_proc Documentation](https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/ext_proc_filter)
