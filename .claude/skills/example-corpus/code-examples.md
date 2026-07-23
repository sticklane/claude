# Code examples — bad → approved fix

Consumed by /build's simplification pass and quality-discipline.md's
self-documenting-code section. Approved entries only; cap 10 (curation
rule in SKILL.md).

### E01 — comment-smell-private-helper (2026-07-23, session: skills-beads-tracking-gaps) — Status: approved

**Bad:**

```python
def process(self, rows):
    # Filter out rows that were already synced in a previous run
    # by checking the high-water mark timestamp stored in state.
    result = []
    for r in rows:
        if r["ts"] > self.state.get("hwm", 0):
            result.append(r)
    return result
```

**Better:**

```python
def unsynced_rows(self, rows):
    high_water_mark = self.state.get("hwm", 0)
    return [r for r in rows if r["ts"] > high_water_mark]
```

**Why:** A private helper needed two comment lines to explain itself —
the self-documenting-code rule (quality-discipline.md): the name and a
named variable carry the meaning; comments belong on public surface area
only.
