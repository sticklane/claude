#!/usr/bin/env bash
# Canonical check for the context-tree component: format, lint, test.
# Run green before calling work done (R17's documented check command).
set -euo pipefail

# Resolve to the crate root (this script's parent's parent) so it runs from any cwd.
crate_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$crate_dir"

cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
