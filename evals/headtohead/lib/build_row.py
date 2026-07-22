#!/usr/bin/env python3
"""Assemble and validate one headtohead results row from a run's transcripts.

Sums usd/tokens across the root session AND every spawned child transcript in
the directory (single-transcript accounting would undercount whichever arm
spawns more — SPEC.md statement 6). Builds the row, validates it against
result.schema.json, and prints it as a single JSON line. Exits non-zero if the
assembled row does not validate, so run.sh can abort rather than append a bad
row.

A crashed/capped run still has whatever transcripts it wrote before dying, so
the sums are non-null partials rather than dropped fields (SPEC.md controls:
"a run that crashes or hits the session cap records as fail with its partial
cost").
"""

import argparse
import glob
import json
import os
import sys


def load_transcripts(d):
    root = None
    children = []
    for p in sorted(glob.glob(os.path.join(d, "*.json"))):
        with open(p) as f:
            t = json.load(f)
        role = t.get("role")
        if role == "root":
            root = t
        elif role == "child":
            children.append(t)
    return root, children


def _type_ok(v, t):
    if t == "null":
        return v is None
    if t == "string":
        return isinstance(v, str)
    if t == "boolean":
        return isinstance(v, bool)
    if t == "integer":
        return isinstance(v, int) and not isinstance(v, bool)
    if t == "number":
        return isinstance(v, (int, float)) and not isinstance(v, bool)
    if t == "object":
        return isinstance(v, dict)
    return False


def _fallback_validate(row, schema):
    """Draft-07 subset validator covering exactly what result.schema.json uses:
    required, additionalProperties:false, type (incl. nullable unions), enum,
    minimum/maximum, minLength. Used only when the jsonschema package is
    absent, so the runner stays self-contained in a bare container."""
    props = schema.get("properties", {})
    if schema.get("additionalProperties") is False:
        for k in row:
            if k not in props:
                raise ValueError(f"additional property not allowed: {k}")
    for k in schema.get("required", []):
        if k not in row:
            raise ValueError(f"missing required property: {k}")
    for k, v in row.items():
        spec = props.get(k, {})
        types = spec.get("type")
        if types is not None:
            if isinstance(types, str):
                types = [types]
            if not any(_type_ok(v, t) for t in types):
                raise ValueError(f"{k}: value {v!r} not of type {types}")
        if "enum" in spec and v not in spec["enum"]:
            raise ValueError(f"{k}: {v!r} not in enum {spec['enum']}")
        if v is not None and isinstance(v, (int, float)) and not isinstance(v, bool):
            if "minimum" in spec and v < spec["minimum"]:
                raise ValueError(f"{k}: {v} below minimum {spec['minimum']}")
            if "maximum" in spec and v > spec["maximum"]:
                raise ValueError(f"{k}: {v} above maximum {spec['maximum']}")
        if isinstance(v, str) and "minLength" in spec and len(v) < spec["minLength"]:
            raise ValueError(f"{k}: shorter than minLength {spec['minLength']}")


def validate(row, schema):
    try:
        import jsonschema
    except ImportError:
        _fallback_validate(row, schema)
        return
    jsonschema.validate(row, schema)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", required=True)
    ap.add_argument("--transcripts", required=True)
    ap.add_argument("--task", required=True)
    ap.add_argument("--arm", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--pass", dest="passed", type=int, required=True)
    ap.add_argument("--wall-s", dest="wall_s", type=float, required=True)
    ap.add_argument("--diff-lines", dest="diff_lines", type=int, required=True)
    args = ap.parse_args()

    root, children = load_transcripts(args.transcripts)

    if root is None and not children:
        # Cost tracking never started (no transcript at all) — null per schema.
        usd = None
        tokens = None
    else:
        usd = round(
            sum(float(t.get("usd", 0)) for t in ([root] if root else []) + children), 6
        )
        tokens = sum(
            int(t.get("tokens", 0)) for t in ([root] if root else []) + children
        )

    turns = int(root.get("turns", 0)) if root is not None else None
    spawn_count = len(children)

    wall_s = args.wall_s if args.wall_s >= 0 else 0.0

    row = {
        "task": args.task,
        "arm": args.arm,
        "seed": args.seed,
        "pass": bool(args.passed),
        "usd": usd,
        "tokens": tokens,
        "turns": turns,
        "wall_s": round(wall_s, 3),
        "spawn_count": spawn_count,
        "diff_lines": args.diff_lines,
        "judge_score": None,
    }

    with open(args.schema) as f:
        schema = json.load(f)
    try:
        validate(row, schema)
    except Exception as e:  # noqa: BLE001 — surface any validator's message
        sys.stderr.write(f"build_row: row failed schema validation: {e}\n")
        sys.stderr.write(json.dumps(row) + "\n")
        sys.exit(1)

    sys.stdout.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    main()
