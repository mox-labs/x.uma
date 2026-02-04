# Envoy ext_proc ProcessingRequest - Detailed Schema Research

## Overview

The Envoy external processing (ext_proc) service provides a bidirectional gRPC stream protocol allowing external services to examine and modify HTTP requests and responses.

## 1. ProcessingRequest Oneof Fields

```protobuf
oneof request {
  HttpHeaders request_headers = 2;      // Initial request headers
  HttpHeaders response_headers = 3;     // Upstream response headers
  HttpBody request_body = 4;            // Request body chunks
  HttpBody response_body = 5;           // Response body chunks
  HttpTrailers request_trailers = 6;    // Request trailers (if present)
  HttpTrailers response_trailers = 7;   // Response trailers (if present)
}
```

### Processing Flow

1. **request_headers** - First message sent for any HTTP request
2. **request_body** - Sent if body processing is configured (may be multiple chunks)
3. **request_trailers** - Sent if trailer mode is SEND and trailers exist
4. **response_headers** - Sent when upstream server responds
5. **response_body** - Sent if response body processing is configured
6. **response_trailers** - Sent if trailer mode is SEND and trailers exist

### Additional Fields

```protobuf
config.core.v3.Metadata metadata_context = 8;      // Dynamic metadata
map<string, google.protobuf.Struct> attributes = 9; // Selected attributes
bool observability_mode = 10;                       // Read-only if true
ProtocolConfiguration protocol_config = 11;        // First message only
```

## 2. HttpHeaders Structure

```protobuf
message HttpHeaders {
  config.core.v3.HeaderMap headers = 1;  // All keys are lowercase
  bool end_of_stream = 3;                 // True if no body
}

message HeaderMap {
  repeated HeaderValue headers = 1;
}

message HeaderValue {
  string key = 1;        // Lowercase
  string value = 2;      // String value
  bytes raw_value = 3;   // Raw bytes (prefer this)
}
```

### Pseudo-Headers (from HTTP/2)

| Header | Description |
|--------|-------------|
| `:method` | HTTP method (GET, POST, etc.) |
| `:path` | Request path with query string |
| `:authority` | Host/authority |
| `:scheme` | Protocol (http/https) |

## 3. HttpBody Structure

```protobuf
message HttpBody {
  bytes body = 1;                        // Body chunk
  bool end_of_stream = 2;                // Last chunk flag
  bool end_of_stream_without_message = 3; // GRPC mode
  bool grpc_message_compressed = 4;      // GRPC mode
}
```

### Body Send Modes

- `NONE` - Body not sent (default)
- `STREAMED` - Chunks streamed as received
- `BUFFERED` - Complete body in one message
- `FULL_DUPLEX_STREAMED` - Bidirectional streaming
- `GRPC` - Individual gRPC messages

## 4. Extracting Common HTTP Data

### From request_headers

```
ProcessingRequest.request_headers.headers.headers[]
├─ key: ":path"      → "/api/users?page=1"
├─ key: ":method"    → "GET"
├─ key: ":authority" → "example.com"
├─ key: ":scheme"    → "https"
└─ key: "x-custom"   → "value"
```

### From Attributes Map

```
attributes["request.path"]      → "/api/users"
attributes["request.method"]    → "GET"
attributes["request.query"]     → "page=1"
attributes["connection.src_ip"] → "192.168.1.1"
```

### Query Parameters

Query params are in `:path` after `?` - must parse manually or use `request.query` attribute.

## 5. Processing Stages Summary

| Stage | Message | Data Available |
|-------|---------|----------------|
| Request Headers | `request_headers` | Method, path, all headers |
| Request Body | `request_body` | Body chunks |
| Request Trailers | `request_trailers` | Trailer headers |
| Response Headers | `response_headers` | Status, headers |
| Response Body | `response_body` | Body chunks |
| Response Trailers | `response_trailers` | Trailer headers |

## 6. Key Implementation Notes

1. **All header keys are lowercase** - case-insensitive normalization
2. **Use `raw_value` not `value`** - for proper byte handling
3. **Headers are repeated array** - must iterate to find
4. **`:path` contains query string** - parse if needed
5. **Attributes may not be set** - depends on config

## 7. Rust DataInput Mapping

```rust
// Path extraction
fn get_path(req: &ProcessingRequest) -> Option<&str> {
    req.request_headers?.headers?.headers
        .iter()
        .find(|h| h.key == ":path")
        .map(|h| &h.raw_value)
}

// Method extraction
fn get_method(req: &ProcessingRequest) -> Option<&str> {
    req.request_headers?.headers?.headers
        .iter()
        .find(|h| h.key == ":method")
        .map(|h| &h.raw_value)
}

// Header extraction
fn get_header(req: &ProcessingRequest, name: &str) -> Option<&str> {
    req.request_headers?.headers?.headers
        .iter()
        .find(|h| h.key == name.to_lowercase())
        .map(|h| &h.raw_value)
}
```
