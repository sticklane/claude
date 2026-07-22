#!/usr/bin/env bash
# Hidden acceptance script for the T2 `notes-api` fixture.
#
# Held OUT of both arms' mounts (a sibling of repo/, per tasks.manifest). Grades
# a produced worktree black-box: it never imports the solution, it drives the
# running HTTP server over a socket. Usage:
#
#   assert.sh <target-repo-dir>   REQUIRED — refuses argless invocation
#
# Exits 0 only when the full suite is green AND the black-box HTTP behaviour
# (paginated + tag-filtered GET /notes, 400s in the standard error shape,
# offset-past-end empty page with metadata) holds AND API.md names both
# parameters. Fails (non-zero) against the untouched snapshot; passes against
# the committed reference solution.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:?usage: assert.sh <target-repo-dir> — argless invocation refused so a missing arg can never silently grade the pristine snapshot}"
TARGET="$(cd "$TARGET" && pwd)"

fail() {
  echo "assert.sh FAIL: $*" >&2
  exit 1
}

# 1) full suite green in the produced worktree ---------------------------------
if ! ( cd "$TARGET" && python3 -m pytest -q ) >/tmp/notes_api_pytest.$$ 2>&1; then
  echo "--- pytest output ---" >&2
  cat /tmp/notes_api_pytest.$$ >&2
  rm -f /tmp/notes_api_pytest.$$
  fail "test suite is not green"
fi
rm -f /tmp/notes_api_pytest.$$

# 2) black-box HTTP behaviour --------------------------------------------------
python3 - "$TARGET" <<'PY' || fail "black-box HTTP checks failed"
import json, socket, subprocess, sys, time, urllib.error, urllib.request

target = sys.argv[1]


def free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


port = free_port()
proc = subprocess.Popen(
    [sys.executable, "router.py", str(port)],
    cwd=target,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
base = "http://127.0.0.1:%d" % port


def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(base + path, data=data, method=method)
    if data is not None:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=3) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)


ready = False
for _ in range(100):
    try:
        req("GET", "/notes")
        ready = True
        break
    except Exception:
        time.sleep(0.05)

try:
    if not ready:
        failures.append("server never became ready")
    else:
        for i in range(25):
            tags = ["work"] if i % 2 == 0 else ["home"]
            st, _ = req("POST", "/notes", {"text": "note %d" % i, "tags": tags})
            check(st == 201, "seed POST returned %s" % st)

        # page math on the seeded store
        _, p1 = req("GET", "/notes?limit=10&offset=0")
        check(len(p1.get("notes", [])) == 10, "page1 expected 10, got %r" % p1.get("notes"))
        check(p1.get("total") == 25, "page1 total expected 25, got %r" % p1.get("total"))
        check(p1.get("limit") == 10 and p1.get("offset") == 0, "page1 metadata: %r" % p1)
        _, p2 = req("GET", "/notes?limit=10&offset=10")
        check(len(p2.get("notes", [])) == 10, "page2 expected 10")
        _, p3 = req("GET", "/notes?limit=10&offset=20")
        check(len(p3.get("notes", [])) == 5, "page3 expected 5 (remainder)")
        ids = sorted(n["id"] for pg in (p1, p2, p3) for n in pg.get("notes", []))
        check(ids == list(range(1, 26)), "pages did not cover every id once: %r" % ids)

        # offset past the end -> empty page WITH metadata
        _, pe = req("GET", "/notes?limit=10&offset=1000")
        check(pe.get("notes") == [], "offset past end should be empty, got %r" % pe.get("notes"))
        check(pe.get("total") == 25, "offset past end should still report total=25, got %r" % pe.get("total"))

        # tag filter alone
        _, tw = req("GET", "/notes?tag=work")
        check(tw.get("total") == 13, "tag=work total expected 13, got %r" % tw.get("total"))
        check(all("work" in n["tags"] for n in tw.get("notes", [])), "tag=work returned a non-work note")

        # tag filter combined with paging
        _, tc = req("GET", "/notes?tag=work&limit=5&offset=10")
        check(tc.get("total") == 13, "combined total expected 13, got %r" % tc.get("total"))
        check(len(tc.get("notes", [])) == 3, "combined page expected 3, got %r" % tc.get("notes"))
        check(all("work" in n["tags"] for n in tc.get("notes", [])), "combined returned a non-work note")

        # bad values -> 400 in the standard error shape
        for q in ("limit=0", "limit=-1", "limit=abc", "offset=-1", "offset=abc"):
            st, be = req("GET", "/notes?" + q)
            ok = (
                st == 400
                and isinstance(be.get("error"), dict)
                and {"code", "message"} <= set(be["error"])
            )
            check(ok, "expected 400 in standard shape for %s, got %s %r" % (q, st, be))
finally:
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except Exception:
        proc.kill()

if failures:
    print("BLACKBOX FAIL:", file=sys.stderr)
    for f in failures:
        print("  - " + f, file=sys.stderr)
    sys.exit(1)
print("BLACKBOX OK")
PY

# 3) API.md documents both parameters ------------------------------------------
API="$TARGET/API.md"
[ -f "$API" ] || fail "API.md missing"
grep -qiw "limit" "$API" || fail "API.md does not name the 'limit' parameter"
grep -qiw "offset" "$API" || fail "API.md does not name the 'offset' parameter"

echo "assert.sh PASS: notes-api ($TARGET)"
