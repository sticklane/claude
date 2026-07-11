#!/usr/bin/env python3
"""Orchestrator-share audit for /breakdown, /build, /idea (spec R1/R2/R4).

Reads the frozen snapshot `samples-2026-07-04-to-11.jsonl.gz` (sibling of this
file) directly via gzip -- no gunzipped copy, no other inputs -- and prints the
headline numbers backing docs/orchestrator-share-findings.md:

  * main-line cost split by token category (input/output/cache_read/cache_write)
  * the rewrite subset (cache_write > max(cache_read, 50k)) and its cost
  * main-line tool:Read frame counts per (session, turn)

Cost-per-category is derived from the snapshot itself: model call cost is a
linear function of the four token counts, so per-model USD/Mtok rates are
recovered by least squares over every model-call sample of that model. Haiku
recovers exactly ($1/$5/$0.10/$1.25, R2=1.0), validating the method; the
frontier models fit R2~0.95 because Anthropic's >200k long-context premium is a
second rate tier a single-rate fit cannot separate -- so category dollars carry
~5% model error (the derived per-skill total is printed next to the exact
measured total as a fit check). Token COUNTS and tool:Read COUNTS are exact.

Run: python3 analyze.py    (no arguments; self-contained against the .gz)
Regression (R4): AUDIT_SNAPSHOT=<fresh-week.jsonl.gz> python3 analyze.py
"""
import gzip
import json
import os
from collections import Counter, defaultdict

import numpy as np

SNAPSHOT = os.environ.get(
    "AUDIT_SNAPSHOT",
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "samples-2026-07-04-to-11.jsonl.gz"
    ),
)
TARGETS = {"breakdown", "build", "idea"}
CATS = ["input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens"]


def is_mainline(stack):
    """Main-line == no agent:/wf: frame in the stack (no delegation)."""
    return not any(f.startswith("agent:") or f.startswith("wf:") for f in stack)


def skill_of(stack):
    for f in stack:
        if f.startswith("skill:"):
            s = f.split(":", 1)[1]
            if s in TARGETS:
                return s
    return None


def model_of(stack):
    for f in stack:
        if f.startswith("claude-"):
            return f
    return None


def load():
    """Single pass: collect regression rows, per-skill main-line tokens/cost,
    rewrite subset, and main-line tool:Read counts per (session, turn)."""
    reg_x = defaultdict(list)
    reg_y = defaultdict(list)
    tok = defaultdict(lambda: defaultdict(lambda: np.zeros(4)))  # skill->model->tokens
    cost = defaultdict(float)
    rewrite_cost = defaultdict(float)
    rewrite_n = defaultdict(int)
    reads = defaultdict(Counter)  # skill -> (session8, turn) -> count
    with gzip.open(SNAPSHOT, "rt") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            stack = obj["stack"]
            sk = skill_of(stack)
            mainline = is_mainline(stack)
            if "values" in obj and "cost_microusd" in obj["values"]:
                v = obj["values"]
                m = model_of(stack)
                if m:
                    vec = [v.get(c, 0) for c in CATS]
                    reg_x[m].append(vec)
                    reg_y[m].append(v["cost_microusd"])
                    if sk and mainline:
                        tok[sk][m] += np.array(vec, float)
                        cost[sk] += v["cost_microusd"]
                        cr, cw = v.get("cache_read_tokens", 0), v.get("cache_write_tokens", 0)
                        if cw > max(cr, 50000):
                            rewrite_cost[sk] += v["cost_microusd"]
                            rewrite_n[sk] += 1
            # tool:Read frames (resolved leaf frames carry duration only, no cost)
            if sk and mainline and "tool:Read" in stack:
                lbl = obj["labels"]
                reads[sk][(lbl["session"][:8], lbl["turn"])] += 1
    return reg_x, reg_y, tok, cost, rewrite_cost, rewrite_n, reads


def fit_rates(reg_x, reg_y):
    rates = {}
    for m in reg_x:
        A = np.array(reg_x[m], float)
        y = np.array(reg_y[m], float)
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        rates[m] = np.clip(coef, 0, None)
    return rates


def main():
    reg_x, reg_y, tok, cost, rewrite_cost, rewrite_n, reads = load()
    rates = fit_rates(reg_x, reg_y)
    print("Orchestrator-share audit -- frozen snapshot", os.path.basename(SNAPSHOT))
    print("=" * 70)
    for sk in ["breakdown", "build", "idea"]:
        catcost = np.zeros(4)
        for m, t in tok[sk].items():
            catcost += t * rates[m]
        derived = catcost.sum()
        actual = cost[sk]
        print(f"\n## /{sk}  main-line ${actual/1e6:.2f}"
              f"  (derived ${derived/1e6:.2f}, fit delta {100*(derived-actual)/actual:+.1f}%)")
        for i, c in enumerate(CATS):
            print(f"   {c:20s} ${catcost[i]/1e6:7.2f}  ({100*catcost[i]/derived:5.1f}%)")
        ocw = 100 * (catcost[1] + catcost[3]) / derived
        print(f"   output+cache_write share: {ocw:.1f}%   "
              f"(cache_read share: {100*catcost[2]/derived:.1f}%)")
        print(f"   rewrite subset (cw>max(cr,50k)): n={rewrite_n[sk]} "
              f"${rewrite_cost[sk]/1e6:.2f} ({100*rewrite_cost[sk]/actual:.0f}% of main-line)")
        r = reads[sk]
        total = sum(r.values())
        print(f"   main-line tool:Read frames: {total} over {len(r)} turn(s): "
              f"{dict(r)}")
    print("\n" + "=" * 70)
    print("Derived USD/Mtok rates (least squares over the snapshot):")
    for m in sorted(rates):
        c = rates[m]
        print(f"   {m:28s} in={c[0]:.3f} out={c[1]:.3f} "
              f"cread={c[2]:.4f} cwrite={c[3]:.3f}")


if __name__ == "__main__":
    main()
