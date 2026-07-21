#!/usr/bin/env bash
# Builds the fixture in $EVAL_DIR (an empty directory the runner provides):
# a tiny node git repo whose canonical check (`npm run check`) is GREEN
# (exit 0), so /gate installs the two-layer quality gates against a
# passing repo. The toolkit's install-gates + its templates/ are copied
# into the fixture so the provisioned gate skill's `<toolkit>/bin/install-gates`
# resolves to ./bin/install-gates (dirname($0)/.. -> the fixture root).
# assert.sh grades the produced settings/hook artifacts, not a live run.
# bash 3.2 compatible (macOS system bash): no `declare -A` or bash-4 syntax.
set -eu

# Resolve the toolkit root from this scenario file's own location
# (evals/gate/01-happy-path/setup.sh -> up three -> repo root).
SCENARIO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLKIT_ROOT="$(cd "$SCENARIO_DIR/../../.." && pwd)"

cd "$EVAL_DIR"
git init -q

mkdir -p bin
cp "$TOOLKIT_ROOT/bin/install-gates" bin/install-gates
chmod 755 bin/install-gates
cp -r "$TOOLKIT_ROOT/templates" templates

# package.json makes this a node repo with a canonical `check` script the
# installer delegates to; `exit 0` is a green check.
cat > package.json <<'EOF'
{
  "name": "gate-happy-fixture",
  "version": "0.0.0",
  "scripts": {
    "check": "exit 0"
  }
}
EOF

git add -A
git -c user.name=eval -c user.email=eval@example.com commit -qm "fixture: green-checks node repo + install-gates"
