# Critique findings — READY WITH NITS (2026-07-19)

Spec-hash: sha256:b561f85cc04408e4cf2e55842284c5344b8aa881c3de24f805ec05891c1fa4e4
Critic verdict: READY WITH NITS (round 3; empty-window-assumption nit
applied). `Breakdown-ready: true` written.

## 2026-07-19 — round 3 (settled)

1. NIT (conf 62, applied): who applies the "window empty" gate for
   ungrouped tasks was under-assigned given the no-slot-arithmetic
   rule. Added: scanner computes structure from an empty-window
   assumption; drain applies the live-window gate (emptiness and
   co-admissibility with live workers) as it owns the admit count.

## 2026-07-19 — round 2 (all applied)

1. BLOCKING: slot accounting — --claimed mixes zombies (no slot) with
   live workers (slot), so scanner slot arithmetic is structurally
   impossible → scanner does NO live-slot arithmetic; pinned R2 test
   min(N, candidates), never N - len(claimed).
2. SPEC: codex seed phrase pinned to runtime-neutral bare token
   drain_frontier; codex invocability classified via
   mirror-verification live check; fallback keeps a non-invoking codex
   correct.

## 2026-07-19 — round 1 (all applied)

1. HIGH: golden-fixture path would have polluted the live queue under
   specs/ → fixture pinned to .claude/skills/drain/fixtures/, specs/
   forbidden.
2. MED: manifest-seed obligation unverified → seeded codex line +
   coverage-gate-green criterion added.
3. MED: step-2 tie-break rewrite unverifiable → mandated verbatim
   sentence anchor.
4. SPEC: dispatchable/admissible split + window semantics pinned.
5. NIT: co-admissibility restated per reference.md's structure.
6. NIT: per-spec invocation scoping (non-zero blast radius bounded).
