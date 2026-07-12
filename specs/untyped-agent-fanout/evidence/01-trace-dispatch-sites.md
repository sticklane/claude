# Verification: task 01 — trace-dispatch-sites

Verdict: PASS

## Criterion 1 — EVIDENCE.md exists

Command:
```
test -f specs/untyped-agent-fanout/EVIDENCE.md && echo EXISTS
```
Output: `EXISTS`. PASS.

## Criterion 2 — dispatch-site grep + every chain row carries a site or `unresolved`

Command:
```
grep -c 'dispatch site\|Dispatch site' specs/untyped-agent-fanout/EVIDENCE.md
```
Output: `4` (≥1). PASS.

Per-chain table inspection: the table (lines 136–274) has 137 data rows
(139 total `|`-prefixed lines minus header + separator). Checked column 8
(`dispatch site`) for every row:

```
awk 'NR>=138' EVIDENCE.md | grep '^|' | awk -F'|' '{gsub(/^ +| +$/,"",$8); if ($8=="") print}' | wc -l
→ 0   (no empty dispatch-site cells)

awk 'NR>=138' EVIDENCE.md | grep '^|' | awk -F'|' '{print $8}' | sed 's/:.*//' | sort | uniq -c
→ 129 drain-self-relaunch
→   8 freehand-gp
```
129 + 8 = 137 — every row carries a resolved site (`drain-self-relaunch` or
`freehand-gp`); 0 rows say `unresolved` and 0 rows are empty. The file's own
"Dispatch sites" section states "0 unresolved" and the arithmetic
(129 + 8 = 137) checks out. PASS.

## Criterion 3 — chain count reconciled against pinned samples

EVIDENCE.md states 137 chains, and gives the exact `gunzip -k` + Python
script used to derive it (lines 26–52 of the file). Independently
re-ran it:

```sh
cd specs/untyped-agent-fanout
gunzip -k evidence-samples-2026-07-11.jsonl.gz     # 5728 lines
python3 - <<'PY'
import json,collections
U={'agent:claude','agent:agentic:claude','agent:general-purpose','agent:agentic:general-purpose'}
ia=lambda f:f.startswith('agent:')
def has(st):
    cur=[]
    for f in st:
        if ia(f):
            if f in U: cur.append(f)
            else:
                if len(cur)>=2 and 'agent:claude' in cur: return True
                cur=[]
    return len(cur)>=2 and 'agent:claude' in cur
ck=set()
for l in open('evidence-samples-2026-07-11.jsonl'):
    r=json.loads(l)
    if has(r['stack']): ck.add((r['labels']['session'],r['labels'].get('agent_id')))
print(len(ck))
PY
rm -f evidence-samples-2026-07-11.jsonl   # cleanup, was never gitignored
```
Output: `137` — matches EVIDENCE.md's claimed count exactly. PASS.
Gunzipped `.jsonl` was deleted after the check; `git status --short` is
clean (nothing left behind, nothing was ever staged).

## Pinned-evidence hygiene (agentprof/README.md denylist)

```
grep -n '/Users/' specs/untyped-agent-fanout/EVIDENCE.md   → (no matches)
grep -noE '[A-Za-z0-9]{24,}' specs/untyped-agent-fanout/EVIDENCE.md → (no matches)
```
No home-path strings, no 24+-char mixed-case hex/token runs. Full session
UUIDs appear only in the intro prose (lines 12–13) — UUIDs are explicitly
allowed by the denylist rule. Agent-id strings in the table (e.g.
`a8b44e7f4f5bef017`, 17 chars) are under the 24-char threshold. PASS.

## Append-only task-file check

```
git diff ec5318c6f33c76959336ae131c0c53ef568c562d -- 'specs/untyped-agent-fanout/tasks/*.md'
→ (empty — no diff)
```
The task file itself is byte-identical to the base commit; no edits at all
(status line was already `in-progress` at the pinned base). Nothing to
flag.

## Scope-creep check

```
git diff ec5318c6f33c76959336ae131c0c53ef568c562d --stat
→ specs/untyped-agent-fanout/EVIDENCE.md | 274 +++++++++++++++++++++++++++++++++
→ 1 file changed, 274 insertions(+)
```
Only `specs/untyped-agent-fanout/EVIDENCE.md` was touched, matching the
task's `Touch:` line exactly (`Touch: specs/untyped-agent-fanout/EVIDENCE.md`).
No scope creep. `git status --short` is clean.

## Summary

All three acceptance criteria PASS, independently exercised (not just read).
No scope creep, no task-file drift, pinned-evidence hygiene clean, cleanup
of the gunzipped working file confirmed.
