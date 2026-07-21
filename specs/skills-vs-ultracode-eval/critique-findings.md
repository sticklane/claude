# Critique findings — NOT READY (2026-07-21, /critique, two rounds)

SPEC.md sha256: 1fd310e33167d939e4c6f9447ac70c92222e130094f73d0bb5e88eef9985b0e9

Critic verdict: NOT READY. Two judgment findings gate; both await a
maintainer decision. Ranked findings (most damaging first):

1. **Arm-S scope overclaim** (confidence 75). Arm S runs headless via
   /evals, but the execution stages (/build, /drain, /prioritize) are
   launch-gated on live-user authorization and brief text is untrusted
   data — so arm S's multi-agent orchestration cannot fire, while arm
   U's ultracode mode is exactly what's opted in. As written the
   finding will read as "toolkit vs ultracode multi-agent" when it
   measures the toolkit's ambient (auto-triggering) tier only.
   Smallest fix: scope the claim in "The question" ("skills'
   auto-triggering surface; launch-gated orchestration out of frame"),
   or specify a sanctioned headless path to the gated tier.
   Recommendation: scope the claim — do not weaken the launch gates to
   win a benchmark.

2. **Verdict rule under-specified at n=3** (confidence 72). Statement
   7 breaks pass-count ties by median cost with no variance band — a
   cent-level median gap on 3 seeds declares a winner on noise — and
   "reported in aggregate; no blended scalar" defines no roll-up for
   the top-line question (a 2–1 task split has no stated meaning).
   Smallest fix: task winner requires a pass-count gap ≥2; otherwise
   "no distinguishable difference," costs reported descriptively;
   overall winner claimed only if one arm wins ≥2 tasks and loses
   none, else "mixed."

Resolved during this critique (mechanical, applied and re-verified by
a second critic pass): judge blinding moved to the assembled input
with a canonical keyword-stripped brief; cost defined as root+spawned
sessions summed identically for both arms, with a spawn-summing
behavioral check; calibration criterion (each hidden script red on
the untouched snapshot, green on the committed reference solution);
crash-as-fail criterion with partial-cost row; hidden-script AND
reference-solution paths asserted outside both arms' mounts; CLI
version + plugin commit pinned in the config dump; over-broad
template grep replaced.
