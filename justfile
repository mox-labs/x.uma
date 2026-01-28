# x.uma Justfile
# Task orchestration for the matcher ecosystem

# Default recipe
default:
    @just --list

# ═══════════════════════════════════════════════════════════════════════════════
# Proto Generation
# ═══════════════════════════════════════════════════════════════════════════════

# Generate proto code
gen:
    buf generate

# Lint proto files
lint-proto:
    buf lint

# Check proto breaking changes
breaking:
    buf breaking --against '.git#branch=main'

# ═══════════════════════════════════════════════════════════════════════════════
# Rust (r.umi)
# ═══════════════════════════════════════════════════════════════════════════════

# Build all Rust crates
build:
    cargo build --manifest-path r.umi/Cargo.toml --workspace

# Build with all features
build-full:
    cargo build --manifest-path r.umi/Cargo.toml --workspace --all-features

# Run tests
test:
    cargo test --manifest-path r.umi/Cargo.toml --workspace

# Run tests with all features
test-full:
    cargo test --manifest-path r.umi/Cargo.toml --workspace --all-features

# Run clippy lints
lint:
    cargo clippy --manifest-path r.umi/Cargo.toml --workspace -- -W clippy::pedantic

# Format code
fmt:
    cargo fmt --manifest-path r.umi/Cargo.toml --all

# Check formatting
fmt-check:
    cargo fmt --manifest-path r.umi/Cargo.toml --all -- --check

# Run all checks (lint + fmt-check + test)
check: lint fmt-check test

# Build documentation
doc:
    cargo doc --manifest-path r.umi/Cargo.toml --workspace --no-deps --open

# Run benchmarks
bench:
    cargo bench --manifest-path r.umi/Cargo.toml

# Verify no_std compatibility
check-no-std:
    cargo build --manifest-path r.umi/Cargo.toml -p rumi-core --no-default-features --features alloc

# ═══════════════════════════════════════════════════════════════════════════════
# Conformance Testing
# ═══════════════════════════════════════════════════════════════════════════════

# Run conformance fixtures
test-fixtures:
    @echo "Conformance fixture runner not yet implemented"

# ═══════════════════════════════════════════════════════════════════════════════
# Development
# ═══════════════════════════════════════════════════════════════════════════════

# Watch and rebuild on changes
watch:
    cargo watch --manifest-path r.umi/Cargo.toml -x build

# Clean build artifacts
clean:
    cargo clean --manifest-path r.umi/Cargo.toml
    rm -rf spike/target

# ═══════════════════════════════════════════════════════════════════════════════
# Release
# ═══════════════════════════════════════════════════════════════════════════════

# Dry-run publish
publish-dry:
    cargo publish --manifest-path r.umi/rumi-core/Cargo.toml --dry-run
    cargo publish --manifest-path r.umi/rumi-proto/Cargo.toml --dry-run
    cargo publish --manifest-path r.umi/rumi-domains/Cargo.toml --dry-run
    cargo publish --manifest-path r.umi/rumi/Cargo.toml --dry-run

# Security audit
audit:
    cargo audit
