# Mirror verification

Some artifacts in this repo have a counterpart maintained for a second
runtime — the same skill or convention re-expressed for another agent
harness. A structural gate (an existence check, a content diff) can confirm
the two files stayed in lockstep; it cannot confirm the copy still *works*
where it lives. This rule states the discipline for the gap the gate leaves
open.

## Structural gates prove conformance, not correctness

An existence-or-content-diff gate proves structural conformance only: that
the mirror exists and its text tracks the source. It says nothing about
whether the mirror's cross-references still resolve — a link, path, tool
name, or command valid in the source runtime can point at nothing under the
target runtime. So a change touching a path that has a mirrored counterpart
in another runtime must verify that the mirror's cross-references actually
resolve under that runtime, not merely that the diff is clean (the
content-parity gate this complements is spec
`codequality-antigravity-content-parity`; the broken-reference class a diff
gate misses was fixed under `antigravity-mirror-broken-refs`).

## Live-test-sweep cadence: closure-triggered, not calendar

The primary trigger for a live cross-reference sweep is closure: closing any
spec or task that touches a mirrored artifact runs the sweep over the
affected mirror as part of that closure, so the check rides the same commit
as the change that could break it. An optional periodic broader sweep across
all mirrors is reasonable as belt-and-suspenders secondary coverage. A
calendar cadence — "sweep every N days" — is explicitly rejected as the
primary mechanism: it decouples the check from the change, leaving a broken
mirror latent until the next scheduled run instead of caught at the commit
that introduced it (parity-gate rationale: `antigravity-parity-gate`).

## Manual-pending escape for unattended workers

Resolving a cross-reference under a target runtime can require exercising
that runtime interactively, and some runtimes expose no scriptable,
non-interactive harness to do it from (e.g. `runtimes/antigravity.md`
records no headless command template — its agents are human-launched). An
unattended or drained worker therefore cannot always complete this step. In
that case the worker marks the criterion manual-pending with the reason
stated — rather than deferring or guessing — and the orchestrator or a human
runs the live check post-merge (unattended workers lack the tools for
interactive and gated steps: `docs/memory/unattended-worker-tool-limits.md`).
