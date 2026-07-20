#!/usr/bin/env bash
# Post one task and poll it back through the API (demo fixture).
set -euo pipefail

submit_task() {
  python - <<'PY'
from taskflow.api import Api
api = Api()
print(api.submit("smoke", {"kind": "ping"}).id)
PY
}

submit_task
