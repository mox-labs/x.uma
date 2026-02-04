# Gateway API Translation Patterns Research

## 1. Two-Stage Compilation Pattern

Both Envoy Gateway and Istio use this pattern:

```
Gateway API (HTTPRoute, etc.)
        ↓ Stage 1
Intermediate Representation (IR)
        ↓ Stage 2
xDS Configuration (Envoy)
```

## 2. HTTPRouteMatch → xDS Mapping

| Gateway API | Envoy xDS |
|-------------|-----------|
| Path (Exact) | StringMatcher.exact |
| Path (PathPrefix) | StringMatcher.prefix or path_separated_prefix |
| Path (RegularExpression) | StringMatcher.safe_regex |
| Headers | HeaderMatcher with StringMatcher |
| QueryParams | QueryParameterMatcher with StringMatcher |
| Method | MethodMatcher |

## 3. StringMatcher (xDS Core Primitive)

```protobuf
// Exactly ONE of:
message StringMatcher {
  oneof match_pattern {
    string exact = 1;
    string prefix = 2;
    string suffix = 3;
    string contains = 7;
    RegexMatcher safe_regex = 5;
  }
  bool ignore_case = 6;  // ASCII only, not for regex
}
```

## 4. Unified Matcher API: Two Patterns

### MatcherList (Linear, First-Match-Wins)
- List of FieldMatchers evaluated in order
- First match determines result
- O(n) evaluation

### MatcherTree (Map-Based, Sublinear)
- Extract key via TypedExtensionConfig input
- Lookup in map:
  - **ExactMatchMap**: HashMap, O(1)
  - **PrefixMatchMap**: Radix tree, longest-prefix-wins
- Much faster for many routes

## 5. Match Semantics

| Rule | Behavior |
|------|----------|
| Within HTTPRouteMatch | All conditions **ANDed** |
| Across HTTPRouteMatch entries | Entries **ORed** |
| MatcherList | First-match-wins (order matters) |
| PrefixMatchMap | Longest-prefix-wins |
| Short-circuit | AND: stop on first false, OR: stop on first true |

## 6. Common Gotchas

| Issue | Problem | Solution |
|-------|---------|----------|
| Empty prefix/suffix | Invalid in xDS | Use safe_regex |
| Partial regex match | Fails (must match full path) | Anchor regex properly |
| Route ordering | Wrong route matches | Specific before generic |
| Trailing slash | Semantics vary | Document clearly |
| Case-insensitive regex | Not supported | Handle differently |

## 7. TypedExtensionConfig Seam

```protobuf
message TypedExtensionConfig {
  string name = 1;                       // Identifier
  google.protobuf.Any typed_config = 2;  // Domain config
}
```

Extension namespaces:
- `envoy.matching.common_inputs.*`
- `envoy.matching.matchers.*`
- `xuma.*` (x.uma extensions)

## 8. x.uma vs Traditional Approach

| Aspect | Traditional | x.uma |
|--------|-------------|-------|
| Matchers | Per-protocol (HTTP, gRPC) | Domain-agnostic core |
| Type system | Varies by domain | `MatchingData` erasure |
| Extensions | Proto additions | `TypedExtensionConfig` |
| Reuse | Limited | Same `ExactMatcher` everywhere |

## 9. Universal Pattern

```
User Config (Gateway API, policy)
        ↓ Compiler
Intermediate Representation
        ↓ Generator
xDS Protocol (Matcher, Route)
        ↓ Runtime
DataInput → Predicate → Action
```

**Key insight:** Match translation = mapping high-level conditions to composable predicates + data extractors. This is exactly what x.uma abstracts.

## 10. Implications for x.uma HTTP Domain

1. **Mirror Gateway API structs** in Rust (no protobuf available)
2. **Use ext_proc proto** for runtime context (protobuf available)
3. **Compile** HTTPRouteMatch → Matcher<ProcessingRequest, A>
4. **Support both** MatcherList (linear) and MatcherTree (map-based)
5. **StringMatcher already implemented** as unified matcher

## Sources

- Envoy Gateway Translator Design
- Envoy Unified Matcher API proto
- Envoy StringMatcher proto
- Envoy Route Components proto
- Kubernetes Gateway API HTTPRoute spec
- Istio Gateway API Integration docs
