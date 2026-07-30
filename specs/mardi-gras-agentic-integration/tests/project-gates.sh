#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

bash scripts/check.sh
python3 -m pytest tests/test_mardi_gras_bootstrap_registration.py -q
python3 -m pytest tests/test_mardi_gras_registration_migration.py -q -k "not provider_integration"

required_gates=(
  specs/mardi-gras-agentic-integration/tests/test_beads_authority_core.sh
  specs/mardi-gras-agentic-integration/tests/test_beads_authority_conditional.sh
  specs/mardi-gras-agentic-integration/tests/test_beads_authority_supersession.sh
  specs/mardi-gras-agentic-integration/tests/test_beads_authority_provider.sh
  specs/mardi-gras-agentic-integration/tests/test_mardi_gras_provider.sh
)

for gate in "${required_gates[@]}"; do
  if [[ ! -f "$gate" ]]; then
    printf 'project-gates: required gate is absent: %s\n' "$gate" >&2
    exit 2
  fi
  bash "$gate"
done
