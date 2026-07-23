// full-cutover-and-health-check — three independent tracks, run concurrently:
//  A) bd cutover (same procedure as cross-repo-beads-adoption.js) for the
//     remaining repos not covered by that already-launched run.
//  B) retire list-specs/prioritize in ~/claude (bd issue agentic-0nz) —
//     never re-pointed onto bd per core task 09's own stated goal; the
//     pivot's "what goes away" table already called for their retirement.
//  C) a functional health check of the skill set: the deterministic
//     ultra-gate lint, a live eval smoke test of the two most-changed
//     skills (work, drain), and a static sweep of every SKILL.md's
//     description for the authoring conventions (trigger phrases present
//     unless disable-model-invocation:true).

export const meta = {
  name: "full-cutover-and-health-check",
  description:
    "bd-cutover the remaining repos, retire list-specs/prioritize, and health-check the skill set",
  phases: [
    { title: "Repo cutover" },
    { title: "Repo verify" },
    { title: "Retire skills" },
    { title: "Skill health" },
  ],
};

const REPOS = [
  { name: "hub", path: "/Users/sjaconette/hub" },
  { name: "budget_analysis", path: "/Users/sjaconette/budget_analysis" },
  { name: "specs", path: "/Users/sjaconette/specs" },
  { name: "life-vault", path: "/Users/sjaconette/vaults/life" },
];

const RESULT_SCHEMA = {
  type: "object",
  properties: {
    status: { enum: ["DONE", "BLOCKED", "DEFERRED"] },
    summary: { type: "string" },
    issues_created: { type: "number" },
    commits: { type: "array", items: { type: "string" } },
    pushed: { type: "boolean" },
    deferred_questions: { type: "array", items: { type: "string" } },
  },
  required: ["status", "summary"],
};
const VERIFY_SCHEMA = {
  type: "object",
  properties: {
    pass: { type: "boolean" },
    failures: { type: "array", items: { type: "string" } },
  },
  required: ["pass"],
};

function adoptPrompt(repo) {
  return `You are doing a COMPLETE beads (bd) cutover in an EXISTING repo: ${repo.path}
This is a DIFFERENT repo from ~/claude — every command must operate against ${repo.path}. Chain "cd ${repo.path} && ..." in every Bash call (subagent shell cwd resets between calls), or use absolute paths / git -C ${repo.path} / bd -C ${repo.path} throughout.

Maintainer directive (2026-07-23): ALL repos on this machine get a full bd cutover — not just the "obvious" candidates. This repo may be small, non-standard, or not a typical code project (it could be a data/analysis repo, an aggregation repo, or even an Obsidian notes vault) — adapt accordingly rather than forcing a code-repo shape onto it. The cutover must be smooth and COMPLETE WITHOUT LOSING DATA: every existing tracked task/todo/checkbox must survive into bd before you say done; old files stay on disk as historical record, never deleted, but CLAUDE.md (or this repo's equivalent orientation file) must stop presenting them as a live tracker.

Read ~/claude/specs/beads-daily-skill/SPEC.md's "Installation in other repos" section (per-repo install steps) and ~/claude/CLAUDE.md's "Beads issue tracker" section (wording/command examples to adapt) before starting.

Do, in order:
1. Look at what actually exists here: CLAUDE.md/AGENTS.md if present, docs/TASKS.md, specs/*/tasks/*.md, or anything else that reads as a task/todo list (for a notes vault, this might be a planning/ or inbox.md file with open items instead — use judgment on what counts as "task state" here, but do not invent structure that doesn't exist; if there is genuinely no open task/todo content anywhere in this repo, that is a valid finding — report issues_created: 0 and move on to bd init + doc updates only).
2. \`bd\` (1.1.0, pinned) and the \`agentic\` CLI are already on PATH machine-wide. Run: cd ${repo.path} && agentic init
   Fallback on failure: bd init --non-interactive --remote "" --skip-agents (never bare "bd init").
3. Full conversion, verifiably not lossy:
   a. If specs/*/tasks/*.md exists: cd ${repo.path} && PYTHONPATH=/Users/sjaconette/claude python3 -m agentic.shadow — then confirm the bd count matches the file count (find ... | wc -l vs bd list --json).
   b. If docs/TASKS.md (or an equivalent checklist file) exists: one bd issue per checkbox line, closed if already checked, open if not; count checkboxes first and confirm your created+closed count matches exactly.
   c. Record the total in issues_created.
4. Update CLAUDE.md (or this repo's primary orientation doc — AGENTS.md, README.md, whatever exists) so it plainly states bd is the sole/primary tracker going forward, points at \`bd ready\`/\`bd prime\`, retires any markdown file's role as a live queue, and includes the discovered-work-in-bd convention with runnable \`bd create\`/\`bd dep add\` example commands.
5. If a \`/gate\` Stop hook already exists, verify/add the bd-compliance check; if none exists, don't invent one — defer it.
6. Verify \`bd ready\` runs; re-check the counts from step 3.
7. Run this repo's own test/check command if one exists; skip if none.
8. Commit (conventional "<type>: <subject>", Co-Authored-By trailer kept) and push: git -C ${repo.path} push. Report pushed:true/false honestly; never force-push.

Do NOT touch ~/claude or any repo besides ${repo.path}. Do NOT delete existing markdown files.
Return DONE only if bd is initialized, every existing task/checkbox is verifiably in bd (or you confirmed there was none), the orientation doc is updated, and everything is committed. BLOCKED for structural failures. DEFERRED with deferred_questions for anything skipped.`;
}

function verifyPrompt(repo, implResult) {
  return `Fresh-eyes verification of a bd cutover in ${repo.path} (operate only against this path).
Worker reported: ${JSON.stringify(implResult)}
Check: (1) bd ready runs clean; (2) independently recount any source task/checkbox material yourself and compare to bd's count — do not trust the worker's number, flag any mismatch with exact numbers; (3) the orientation doc states bd as sole/primary tracker with a discovered-work convention and runnable command examples; (4) git status is clean and a matching commit exists; (5) if pushed:true was claimed, confirm nothing remains unpushed (git log origin/<branch>..HEAD empty).
pass:true only if all five hold (an honest "there was no source material to convert" counts as satisfying #2). List concrete failures otherwise.`;
}

const CRITIC_PROMPT = `Read docs/memory/skill-retirement-checklist.md in this repo (~/claude) FIRST — it exists precisely because clean greps and green gates have missed real gaps before (five gaps survived a clean sweep on 2026-07-04's /parallel retirement).

Task: retire the /list-specs and /prioritize skills. bd issue agentic-0nz (read it: bd show agentic-0nz) documents why — core task 09's own Goal named .claude/skills/list-specs/list_specs.py and .claude/skills/prioritize/prioritize_scan.py as readers to "re-point onto bd... or retire," alongside drain_frontier.py/status.sh, but task 09's actual implementation only touched status.sh. The 2026-07-22 pivot's own "what goes away" table already called for retiring list-specs/prioritize as standalone scanners — this finishes that.

Do, following the checklist:
1. Confirm bd list --json / bd ready already supersede what these two skills did (they do — status.sh already re-points onto bd per task 09; /work is the new "what's next" entry point).
2. Delete .claude/skills/list-specs/ and .claude/skills/prioritize/ entirely (SKILL.md, list_specs.py, prioritize_scan.py, their tests).
3. Grep the BARE name case-insensitive across the whole repo (grep -ri "list-specs\\|list_specs\\|prioritize" — not just slash/path forms) and manually review every hit: AGENTS.md's Map/Commands, README.md's pipeline table, CLAUDE.md, other skills' SKILL.md/reference.md that might mention "/list-specs" or "/prioritize" as the next pipeline step, evals/ (delete or update any list-specs/prioritize eval scenarios), .claude-plugin/plugin.json (skills are directory-scanned, no manifest edit needed — confirm this stays true), tests/ (any test asserting these skills exist).
4. Port behaviors, don't just delete references: if any OTHER skill's "self-chain" logic named /list-specs or /prioritize as its next stage, repoint that reference at /work or bd ready as appropriate — don't leave a dangling next-stage pointer.
5. Bump .claude-plugin/plugin.json's version (skill-set change).
6. Run bash scripts/check.sh — must be green (minus the pre-existing documented quarantine).
7. Close bd issue agentic-0nz with a reason citing what you did, after everything else is committed.

Commit your work, then STOP without self-reviewing — an independent critic reviews your diff next per the checklist's own step 5 ("then run the critic on the diff even with all gates green").
Return status DONE with a summary and commit list, or BLOCKED with the exact reason.`;

function healthCheckPrompt() {
  return `Health-check this repo's (~/claude) own skill set — two checks, all read-mostly:

1. Live smoke test: run "bash evals/run.sh work" and "bash evals/run.sh drain" (the two skills most rewritten by the 2026-07-22/23 pivot session) and report each scenario's pass/fail line and the summary. If either command errors out structurally (missing fixture, script crash) rather than reporting a graded pass/fail, say so plainly rather than guessing at a result.
2. Static sweep: for every .claude/skills/*/SKILL.md, read its frontmatter description. Flag any skill whose description lacks concrete trigger phrases UNLESS its frontmatter sets "disable-model-invocation: true" (per CLAUDE.md's authoring-conventions bullet — those skills are exempt). Also flag any skill description that still names a skill CLAUDE.md/the pivot retired (list-specs, prioritize, or anything else no longer present as a directory) as a next-stage pointer.
Do not fix anything — this is a report. Return a structured summary: work_eval_result, drain_eval_result, skills_missing_trigger_phrases (list), stale_next_stage_pointers (list).`;
}

const HEALTH_SCHEMA = {
  type: "object",
  properties: {
    ultra_gate_result: { type: "string" },
    work_eval_result: { type: "string" },
    drain_eval_result: { type: "string" },
    skills_missing_trigger_phrases: {
      type: "array",
      items: { type: "string" },
    },
    stale_next_stage_pointers: { type: "array", items: { type: "string" } },
  },
  required: ["ultra_gate_result"],
};

const [repoResults, retireResult, healthResult] = await parallel([
  () =>
    pipeline(
      REPOS,
      (repo) =>
        agent(adoptPrompt(repo), {
          label: `adopt:${repo.name}`,
          phase: "Repo cutover",
          agentType: "implementation-worker",
          schema: RESULT_SCHEMA,
        }),
      (implResult, repo) =>
        agent(verifyPrompt(repo, implResult), {
          label: `verify:${repo.name}`,
          phase: "Repo verify",
          agentType: "verifier",
          schema: VERIFY_SCHEMA,
        }).then((verify) => ({ repo: repo.name, implResult, verify })),
    ),
  () =>
    agent(CRITIC_PROMPT, {
      label: "retire:list-specs+prioritize",
      phase: "Retire skills",
      agentType: "implementation-worker",
      schema: RESULT_SCHEMA,
    }).then(async (implResult) => {
      if (!implResult || implResult.status !== "DONE")
        return { implResult, critic: null };
      const critic = await agent(
        `Review the just-committed diff retiring /list-specs and /prioritize in this repo (~/claude). Check the retirement checklist's five failure classes (docs/memory/skill-retirement-checklist.md): bare-name mentions missed, behaviors not ported, dispatch paths not all updated, absorbed text not reconciled with the host's invariants, and anything else a clean grep + green gate would miss. Report findings ranked by severity.`,
        {
          label: "critic:list-specs-prioritize-retirement",
          phase: "Retire skills",
          agentType: "critic",
        },
      );
      return { implResult, critic };
    }),
  () =>
    agent(healthCheckPrompt(), {
      label: "skill-health-check",
      phase: "Skill health",
      schema: HEALTH_SCHEMA,
    }),
]);

return { repoResults, retireResult, healthResult };
