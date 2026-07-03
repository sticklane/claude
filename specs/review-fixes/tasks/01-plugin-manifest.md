# Task 01: Plugin manifest validates — agents array, marketplace description, CLAUDE.md caveat

Status: done
Depends on: none
Budget: 16 turns
Spec: ../SPEC.md (cluster 01)

## Goal

`claude plugin validate .` exits 0. The `agents` field in plugin.json is an
array of .md paths (the directory-string form fails validation), the
marketplace manifest gains the top-level `description` the validator warns
about, and CLAUDE.md's "adding a skill or agent needs no manifest edit"
bullet gains the caveat that agents ARE enumerated by schema requirement.
Do NOT bump `version` — task 99 owns the single batch bump.

## Touch

- `.claude-plugin/plugin.json` (`agents` field only — not `version`)
- `.claude-plugin/marketplace.json` (top-level `description`)
- `CLAUDE.md` (the `.claude-plugin/` bullet)

## Steps

1. In `.claude-plugin/plugin.json`, replace
   `"agents": "./.claude/agents"` with
   `"agents": ["./.claude/agents/scout.md", "./.claude/agents/critic.md", "./.claude/agents/verifier.md"]`.
2. In `.claude-plugin/marketplace.json`, add a top-level `description`
   string (the validator warns when it is missing; keep it
   non-enumerating per CLAUDE.md).
3. In CLAUDE.md's `.claude-plugin/` bullet, amend "adding a skill or agent
   needs no manifest edit" with the caveat that agents ARE enumerated in
   plugin.json by schema requirement — new agents DO need a manifest edit;
   only skills stay manifest-free.
4. Run `claude plugin validate .` and fix anything else it reports.

## Acceptance

- [x] `claude plugin validate .` → exit 0
  Evidence: exit 0, "Validation passed" — evidence/01-plugin-manifest.md
- [x] `python3 -c "import json; a=json.load(open('.claude-plugin/plugin.json'))['agents']; assert isinstance(a, list) and set(a)=={'./.claude/agents/scout.md','./.claude/agents/critic.md','./.claude/agents/verifier.md'}"` → exit 0
  Evidence: exit 0; array matches the three real agent files — evidence/01-plugin-manifest.md
- [x] `python3 -c "import json; m=json.load(open('.claude-plugin/marketplace.json')); assert isinstance(m.get('description'), str) and m['description']"` → exit 0
  Evidence: exit 0; description non-enumerating — evidence/01-plugin-manifest.md
- [x] `python3 -c "import json; assert json.load(open('.claude-plugin/plugin.json'))['version']=='0.3.0'"` → exit 0 (version untouched — 99 owns the bump)
  Evidence: pin stale (intervening bumps landed; current 0.6.0). Intent verified instead: git diff shows the version line untouched, per task 99 step 2's stale-pin adjustment rule — evidence/01-plugin-manifest.md
- [x] `grep -q "enumerated" CLAUDE.md` → exit 0 (caveat present in the manifest bullet)
  Evidence: exit 0; caveat coherent — evidence/01-plugin-manifest.md
