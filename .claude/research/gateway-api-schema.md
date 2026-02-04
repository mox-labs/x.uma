# Gateway API HTTPRouteMatch Schema Research

## Key Finding: No Protobuf

Gateway API is defined as **Go structs + Kubernetes CRD YAML**, not protobuf.

**Sources:**
- Go source: `github.com/kubernetes-sigs/gateway-api/apis/v1/httproute_types.go`
- CRD YAML: `config/crd/experimental/gateway.networking.k8s.io_httproutes.yaml`

## HTTPRouteMatch Structure

```go
type HTTPRouteMatch struct {
    Path        *HTTPPathMatch         // Path matching
    Headers     []HTTPHeaderMatch      // Header matching (AND within, OR across)
    QueryParams []HTTPQueryParamMatch  // Query param matching
    Method      *HTTPMethod            // HTTP method
}
```

## HTTPPathMatch

```go
type HTTPPathMatch struct {
    Type  PathMatchType  // "Exact" | "PathPrefix" | "RegularExpression"
    Value *string
}
```

| Type | Example | Matches |
|------|---------|---------|
| `Exact` | `/coffee` | Only `/coffee` |
| `PathPrefix` | `/api` | `/api`, `/api/`, `/api/v1` |
| `RegularExpression` | `/api/v[0-9]+` | `/api/v1`, `/api/v2` |

## HTTPHeaderMatch

```go
type HTTPHeaderMatch struct {
    Type  HeaderMatchType  // "Exact" | "RegularExpression"
    Name  HTTPHeaderName   // Header name (case-insensitive)
    Value string           // Value to match
}
```

## HTTPQueryParamMatch

```go
type HTTPQueryParamMatch struct {
    Type  QueryParamMatchType  // "Exact" | "RegularExpression"
    Name  string               // Query param name
    Value string               // Value to match
}
```

## HTTPMethod

```go
type HTTPMethod string
// Values: GET, HEAD, POST, PUT, DELETE, CONNECT, OPTIONS, TRACE, PATCH
```

## Match Logic: AND/OR

**Within ONE HTTPRouteMatch:**
- All conditions are **ANDed**
- path AND headers AND method must ALL match

**Across multiple HTTPRouteMatch entries:**
- Entries are **ORed**
- Request matches if ANY entry matches

```yaml
rules:
- matches:
  # Match 1: (path=/api AND method=GET)
  - path: { type: Exact, value: /api }
    method: GET
  # OR Match 2: (path=/health)
  - path: { type: Exact, value: /health }
```

## YAML Example

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: example-route
spec:
  parentRefs:
  - name: example-gateway
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /api/v2
      headers:
      - type: Exact
        name: x-api-version
        value: "2"
      method: GET
    backendRefs:
    - name: api-v2-service
      port: 8080
```

## Implications for x.uma

Since there's no protobuf, options are:

1. **Mirror the schema in Rust** - define equivalent structs
2. **Use JSON Schema** - extract from CRD openAPIV3Schema
3. **Generate from Go** - use go2rust or manual translation

Recommendation: **Mirror in Rust** with serde for YAML/JSON parsing:

```rust
#[derive(Deserialize)]
pub struct HTTPRouteMatch {
    pub path: Option<HTTPPathMatch>,
    pub headers: Option<Vec<HTTPHeaderMatch>>,
    pub query_params: Option<Vec<HTTPQueryParamMatch>>,
    pub method: Option<HTTPMethod>,
}

#[derive(Deserialize)]
pub struct HTTPPathMatch {
    #[serde(rename = "type")]
    pub match_type: PathMatchType,
    pub value: Option<String>,
}

#[derive(Deserialize)]
pub enum PathMatchType {
    Exact,
    PathPrefix,
    RegularExpression,
}
```
