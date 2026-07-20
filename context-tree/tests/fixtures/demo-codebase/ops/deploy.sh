#!/usr/bin/env bash
# Deploy the taskflow stack (demo fixture).
set -euo pipefail

build_server() {
  (cd pyserver && python -m compileall taskflow)
}

build_worker() {
  (cd goworker && go build ./...)
}

build_server
build_worker
echo "deployed"
