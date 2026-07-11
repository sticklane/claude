# Task 05 — agent-console cost panel `main`-key special-casing check (R4)

**Verdict: GENERIC-ITERATION — no panel fix needed.**

The agent-console workboard cost panel renders every `by_*` grouping (including
`by_model`) through one generic helper, `_cost_rows`, in
`agent-console/agent-console.py` (~lines 1925–1938; called for `by_model` at
~line 1950):

```python
def _cost_rows(dim):
    top = sorted(
        (dim or {}).items(),
        key=lambda kv: (kv[1] or {}).get("cost_microusd", 0),
        reverse=True,
    )[:5]
    return (
        "".join(
            f'<div class="line"><span class="trunc">{esc(name)}</span>'
            f'<span class="meta">{_usd((v or {}).get("cost_microusd", 0))}</span></div>'
            for name, v in top
        )
        or '<div class="zero">None.</div>'
    )
```

It iterates `(dim or {}).items()` and renders each key generically via
`for name, v in top` — there is no branch keyed on the literal string `"main"`
(or `"(tools)"` / `"(synthetic)"`). A grep across the agent-console directory
finds `"main"` only in unrelated git-branch test fixtures, and `(tools)` /
`(synthetic)` appear nowhere.

Because the panel already iterates keys generically, the new `(tools)` and
`<synthetic>` by_model keys render with no code change — and no `main` key is
produced for it to have special-cased. **No edit made to agent-console** (also
outside this task's Touch).
