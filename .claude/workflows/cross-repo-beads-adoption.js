// cross-repo-beads-adoption — install/adopt bd (beads) in the repos the
// 2026-07-22 pivot's rollout audit (docs/cross-repo-rollout-2026-07-22.md
// in ~/claude) flagged as still using markdown docs/TASKS.md or carrying
// contradictory tracker docs. Each repo is a fully independent git tree —
// no Touch collision between repos — so this pipelines them concurrently.
//
// Scope (per the audit + maintainer go-ahead, 2026-07-23): automation,
// fooszone (reconcile contradictory docs), interview-prep,
// portfolio-tracker, ynab-mcp-new (also closes beads-daily-skill's CUJ-5).
// hub/budget_analysis/specs/vaults-life are OUT of scope — the audit
// classified them "no action" (not real drain/agentic candidates or not
// code repos) and this workflow does not touch them.

export const meta = {
  name: "cross-repo-beads-adoption",
  description:
    "Install bd + convert existing task state to bd issues in the 5 repos the rollout audit flagged",
  phases: [{ title: "Adopt" }, { title: "Verify" }],
};

const REPOS = [
  { name: "automation", path: "/Users/sjaconette/automation" },
  { name: "fooszone", path: "/Users/sjaconette/fooszone" },
  { name: "interview-prep", path: "/Users/sjaconette/interview-prep" },
  { name: "portfolio-tracker", path: "/Users/sjaconette/portfolio-tracker" },
  { name: "ynab-mcp-server", path: "/Users/sjaconette/ynab-mcp-new" },
];

const RESULT_SCHEMA = {
  type: "object",
  properties: {
    status: { enum: ["DONE", "BLOCKED", "DEFERRED"] },
    summary: { type: "string" },
    bd_ready_output: { type: "string" },
    issues_created: { type: "number" },
    commits: { type: "array", items: { type: "string" } },
    pushed: { type: "boolean" },
    deferred_questions: { type: "array", items: { type: "string" } },
  },
  required: ["status", "summary"],
};

function adoptPrompt(repo) {
  return `You are doing a COMPLETE beads (bd) cutover in an EXISTING repo: ${repo.path}
This is a DIFFERENT repo from ~/claude — every command must operate against ${repo.path}, never the wrong cwd. Chain "cd ${repo.path} && ..." in every Bash call (subagent shell cwd resets between calls), or use absolute paths / git -C ${repo.path} / bd -C ${repo.path} throughout.

Maintainer directive (2026-07-23): specs for every repo get FULLY converted to bd; after this, agents working in this repo must not reference or use the markdown specs/ pipeline or docs/TASKS.md as a live tracker anywhere — bd is the sole source of truth going forward. This must be a SMOOTH, COMPLETE cutover WITHOUT LOSING DATA: every existing task/issue's content and status must survive into bd before you say anything is done; the old markdown files are kept on disk as inert historical record (never deleted), but CLAUDE.md must stop telling agents to read or write them for live task state.

Context: ~/claude's own 2026-07-22 pivot did exactly this to itself (specs/agentic-core-redesign task 05 shadow-synced its markdown queue into bd, task 09 cut bd over as source of truth). Read ~/claude/specs/beads-daily-skill/SPEC.md's "Installation in other repos" section for the per-repo install steps (cite it, don't re-derive). Read ~/claude/CLAUDE.md's "Beads issue tracker" section for the exact "record discovered work in bd immediately" wording/command examples to adapt into this repo's own CLAUDE.md.

Do, in order:
1. Read this repo's current CLAUDE.md and AGENTS.md (if either exists) in full. Note its existing task-tracking convention and any stale bd-related text (e.g. "tracker decommissioned", a CLAUDE.md/AGENTS.md contradiction, or a leftover auto-generated "Beads Issue Tracker" block from a bd install that was later removed).
2. \`bd\` (1.1.0, pinned) and the \`agentic\` CLI are already on PATH machine-wide — do not reinstall either. Run: cd ${repo.path} && agentic init
   If that fails (e.g. a committed .beads/config.yaml with an unreachable remote, or bd says the workspace is already initialized), fall back to: bd init --non-interactive --remote "" --skip-agents (avoids bd's own destructive auto-commit-into-CLAUDE.md side effect — never run bare "bd init" with no flags).
3. FULL conversion — this is the actual deliverable, not an empty bd install:
   a. If this repo has specs/*/tasks/*.md files (check: test -d ${repo.path}/specs), run the exact shadow-sync tool ~/claude used on itself, pointed at THIS repo instead:
      cd ${repo.path} && PYTHONPATH=/Users/sjaconette/claude python3 -m agentic.shadow
      This deterministically imports every task file (Status, Depends on, Priority, Touch, Rigor headers) as a bd issue with correct status and dependency edges — read ~/claude/agentic/shadow.py's module docstring if you want to understand exactly what it does before running it. Run it, then confirm with \`bd list --json\` that the imported count matches the number of specs/*/tasks/*.md files on disk (do not eyeball this — count both and compare).
   b. If this repo has docs/TASKS.md checkboxes, convert every line into a bd issue: unchecked items open (\`bd create "<title>"\`), already-checked items created and immediately closed (\`bd close <id> --reason "already done (pre-bd)"\`) so completed history is preserved in bd too, not silently dropped. Count every checkbox line first (grep -c '^- \\[' docs/TASKS.md) and confirm your created+closed count matches it exactly — this repo's maintainer explicitly does not want data lost in this conversion.
   c. Record the total issues_created (open + closed) in your structured return.
4. Rewrite CLAUDE.md (and AGENTS.md if it has a stale/contradictory tracker section) so it plainly states: bd is this repo's sole task tracker; \`bd ready\`/\`bd prime\` is how to find work; the old specs/*/tasks/*.md and docs/TASKS.md files are historical record only, not a live queue agents should read/write going forward. Add the discovered-work-in-bd convention with the bd create/dep add example commands (adapt ~/claude/CLAUDE.md's wording; add a "Beads issue tracker" heading if this repo doesn't have one). If AGENTS.md has a stale auto-generated bd block contradicting the real state, correct it.
5. If the repo already has a \`/gate\`-installed Stop hook (check .claude/settings.json, hooks/, scripts/check.sh), verify or add the bd-compliance check per beads-daily-skill's install steps; if there's no gate at all, don't invent one from scratch — note it deferred.
6. Verify: \`bd ready\` runs without error; re-run the counting checks from step 3 one more time as a final sanity check before committing.
7. Run this repo's own test/check command if one exists (scripts/check.sh, a package.json test script, etc.) to confirm your doc edits didn't break a mechanical check (e.g. a doc-link test). Skip if none exists.
8. Commit in THIS repo (small, focused commits; conventional "<type>: <subject>"; keep the Co-Authored-By trailer) and push: git -C ${repo.path} push. If push fails (no upstream, auth, diverged), do not force anything — report it in deferred_questions, set pushed:false.

Do NOT touch ~/claude or any repo besides ${repo.path}. Do NOT force-push. Do NOT delete docs/TASKS.md or specs/ content — they stay on disk as historical record; only their role as a LIVE, agent-consulted tracker is retired, in favor of bd.
Return status DONE only if: bd is initialized, EVERY existing task/checkbox is verifiably accounted for in bd (counts matched, not estimated), CLAUDE.md/AGENTS.md now say bd is sole source of truth (not just "also has bd"), and everything is committed. Return BLOCKED with the exact error if something structural prevents this. Return DEFERRED with deferred_questions for anything deliberately skipped (e.g. no gate to extend).`;
}

function verifyPrompt(repo, implResult) {
  return `Fresh-eyes verification of a bd CUTOVER (not just an install) in ${repo.path} (a repo OTHER than ~/claude — operate only against this path).
The prior worker reported: ${JSON.stringify(implResult)}
Check, from ${repo.path}:
1. \`.beads/\` exists and \`bd ready\` (or \`bd -C ${repo.path} ready\`) runs without error.
2. NO DATA LOST: independently recount the source material and compare to bd's issue count yourself — do not trust the worker's claimed count.
   - If specs/*/tasks/*.md exists: \`find ${repo.path}/specs -path '*/tasks/*.md' | wc -l\` vs \`bd -C ${repo.path} list --json --all\` count of issues with a metadata field tying them to a task path (or however shadow-sync tagged them) — every task file must have a corresponding bd issue.
   - If docs/TASKS.md exists: \`grep -c '^- \\[' ${repo.path}/docs/TASKS.md\` vs the worker's created+closed count — must match exactly.
   Fail this check with the exact numbers if they don't match.
3. CLAUDE.md states bd is the SOLE/primary tracker (not merely "also available") and explicitly retires specs/docs/TASKS.md as a live reference; it also includes a "record discovered work in bd" convention with runnable bd command examples, not just prose.
4. git log shows a recent commit in this repo matching the claimed work, and \`git -C ${repo.path} status --porcelain\` is clean (or only has files outside this task's scope).
5. If the worker claimed pushed:true, confirm \`git -C ${repo.path} log origin/<branch>..HEAD\` is empty (nothing unpushed).
Report pass:true only if all five hold. List concrete failures (with the actual numbers from check 2) otherwise — do not fix anything yourself.`;
}

const VERIFY_SCHEMA = {
  type: "object",
  properties: {
    pass: { type: "boolean" },
    failures: { type: "array", items: { type: "string" } },
  },
  required: ["pass"],
};

const results = await pipeline(
  REPOS,
  (repo) =>
    agent(adoptPrompt(repo), {
      label: `adopt:${repo.name}`,
      phase: "Adopt",
      agentType: "implementation-worker",
      schema: RESULT_SCHEMA,
    }),
  (implResult, repo) =>
    agent(verifyPrompt(repo, implResult), {
      label: `verify:${repo.name}`,
      phase: "Verify",
      agentType: "verifier",
      schema: VERIFY_SCHEMA,
    }).then((verify) => ({ repo: repo.name, implResult, verify })),
);

return {
  summary: results.map((r) => ({
    repo: r?.repo,
    status: r?.implResult?.status,
    issues_created: r?.implResult?.issues_created,
    pushed: r?.implResult?.pushed,
    verified: r?.verify?.pass,
    failures: r?.verify?.failures || [],
  })),
  detail: results,
};
