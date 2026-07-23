# Writing examples — bad prose → approved rewrite

Consumed by /prose-review and anti-ai-slop-writing as calibration
examples. Approved entries only; cap 10 (curation rule in SKILL.md).

### E01 — negative-parallelism-importance-inflation (2026-07-23, session: skills-beads-tracking-gaps) — Status: approved

**Bad:**

```text
This isn't just a bug fix — it's a fundamental rethinking of how the
pipeline handles state. The change plays a crucial role in ensuring
robust, reliable workflows across the entire ecosystem.
```

**Better:**

```text
The fix moves queue state from per-session markdown into bd, so a worker
crash no longer loses the claim record. Two incident reports
(2026-07-11, 2026-07-19) trace to that loss.
```

**Why:** Negative parallelism plus importance asserted by adjective
("crucial", "robust") instead of consequences — grounding's Rule 3 and
/prose-review's rubric; the rewrite states the concrete change and the
evidence.
