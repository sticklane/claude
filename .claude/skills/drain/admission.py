#!/usr/bin/env python3
"""admission — drain's cross-spec spec-lease claim and two-level admission cap.

Authoritative, live-invoked module (invoked by path like
`.claude/skills/prioritize/prioritize_scan.py`, per
specs/drain-multi-spec-swarm R15) for the two checks drain now owns across
specs:

  * R1 — greedy spec-lease claim eligibility: claim up to 3
    simultaneously-held spec leases whose dispatchable-task Touch footprints
    are pairwise disjoint from each other and from every already-claimed
    spec, using the Priority-then-path tie-break applied spec-by-spec.
  * R2 — the two-level admission cap: a single claimed spec's own tasks are
    bounded by its own `W` (hard-capped at 5), while all claimed specs'
    dispatchable tasks compete for one shared global window capped at <= 10
    total live workers across every claimed spec combined.

It composes with `drain_frontier.py` rather than duplicating it (R14):
`drain_frontier.py` computes each spec's per-spec dispatchable/admissible/
blocked sets and their ordering, which this module CONSUMES (via
`load_frontier`) and never re-derives. It does NOT source Touch-footprint data
from that JSON (the scanner's schema carries no per-task `Touch:` sets);
instead it reads each candidate spec's dispatchable-task `Touch:` headers
directly from disk via the shared `_shared/touch_disjoint.py` helper.

It also expresses reference.md's DRAIN-OWNER.md git-CAS lease-claim protocol
(absent -> claim; FRESH -> refuse unless baton lineage; ALL STALE -> reclaim;
read-check-write-commit-push-reread-confirm) as callable code, mechanically
unchanged. The genuine multi-process race test of that protocol lives in
`test_admission_concurrency.py` (task 05); this module's own
`test_admission.py` covers the deterministic logic.

Read-only against the queue except for the lease-claim commit. Stdlib only.
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

# Bootstrap the shared Touch-disjointness helper the drain_frontier.py way:
# put _shared/ on sys.path, then a regular import.
_SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(_SCRIPT.parent.parent / "_shared"))
from touch_disjoint import entries_disjoint, footprint  # noqa: E402

_STALE_WINDOW_SECONDS = 900  # 15-min grace window (reference.md, overridable)
_REQUIRED_FRONTIER_KEYS = ("dispatchable", "admissible", "blocked")


class AdmissionError(Exception):
    """Raised on malformed frontier input or a broken lease invariant. A wrong
    admission decision is worse than none, so callers map it to a non-zero
    exit rather than silently falling back to a duplicate re-derivation."""


# --------------------------------------------------------------------------- #
# R14: consume drain_frontier.py's JSON; never re-derive it.
# --------------------------------------------------------------------------- #
def spec_of(task_path):
    """The spec dir owning a task file: `specs/<slug>/tasks/NN.md` ->
    `specs/<slug>`."""
    return str(Path(task_path).parent.parent)


def load_frontier(obj):
    """Validate a `drain_frontier.py`-shaped frontier dict and return it.

    Raises AdmissionError when a required list field is absent or not a list —
    R14's negative constraint: admission fails loudly rather than silently
    re-deriving per-spec dependency/window logic itself."""
    if not isinstance(obj, dict):
        raise AdmissionError(
            f"frontier must be a JSON object, got {type(obj).__name__}"
        )
    for key in _REQUIRED_FRONTIER_KEYS:
        if key not in obj:
            raise AdmissionError(f"frontier missing required field {key!r}")
        if not isinstance(obj[key], list):
            raise AdmissionError(
                f"frontier field {key!r} must be a list, got {type(obj[key]).__name__}"
            )
    return obj


# --------------------------------------------------------------------------- #
# R1: greedy spec-lease claim eligibility.
# --------------------------------------------------------------------------- #
def claim_specs(candidates, already_claimed_footprints=(), cap=3):
    """Greedily claim up to `cap` spec leases whose dispatchable-task Touch
    footprints are pairwise disjoint from each other and from every
    already-claimed spec's footprint.

    `candidates` is the spec-claim order (Priority-then-path applied at spec
    granularity); each is a dict with `spec` (dir) and `task_files` (its
    dispatchable task file paths). Footprints are read from those files on
    disk (R14). Returns the claimed subset as dicts with `spec` and computed
    `footprint`, in claim order — mirroring how task-level admission compares
    each candidate against the claimed set as it is built up, never the whole
    queue."""
    claimed = []
    footprints = list(already_claimed_footprints)
    for cand in candidates:
        if len(claimed) >= cap:
            break
        fp = footprint(cand["task_files"])
        if all(entries_disjoint(fp, other) for other in footprints):
            claimed.append({"spec": cand["spec"], "footprint": fp})
            footprints.append(fp)
    return claimed


# --------------------------------------------------------------------------- #
# R2: two-level admission cap (per-spec W<=5 + shared global <=10).
# --------------------------------------------------------------------------- #
def admit_tasks(admissible, in_flight=None, w=5, global_cap=10):
    """Admit tasks under the two-level cap.

    `admissible` is the union of every claimed spec's per-spec admissible set
    (from `drain_frontier.py`'s `admissible` field — already Touch-disjoint
    and `Group:`-co-admissible WITHIN each spec, assuming an empty window).
    This function layers the cross-spec rules on top:

      * each claimed spec contributes at most its own `W` (hard-capped at 5)
        MINUS that spec's already-in-flight task count — the per-spec live
        window, scoped per-spec so a different spec's in-flight tasks never
        close it;
      * the surviving pool competes for one shared global window of
        `global_cap` (default 10) via the Priority-then-path tie-break,
        already accounting for the globally in-flight total.

    Cross-spec Touch-disjointness needs no re-check here: `claim_specs` only
    admits specs with pairwise-disjoint footprints, so any two tasks from
    different claimed specs are disjoint by construction. `in_flight` maps a
    spec dir to its current in-flight task count."""
    in_flight = in_flight or {}
    per_spec_ceiling = min(w, 5)

    by_spec = {}
    order = []
    for entry in admissible:
        spec = spec_of(entry["path"])
        if spec not in by_spec:
            by_spec[spec] = []
            order.append(spec)
        by_spec[spec].append(entry)

    pool = []
    for spec in order:
        room = per_spec_ceiling - in_flight.get(spec, 0)
        if room > 0:
            pool.extend(by_spec[spec][:room])

    pool.sort(key=lambda e: (_prio_num(e["priority"]), e["path"]))
    remaining_global = global_cap - sum(in_flight.values())
    return pool[: max(remaining_global, 0)]


def _prio_num(priority):
    return int(str(priority).lstrip("Pp") or 2)


# --------------------------------------------------------------------------- #
# Step 6: DRAIN-OWNER.md git-CAS lease-claim protocol (reference.md, unchanged).
# --------------------------------------------------------------------------- #
_OWNER_FIELDS = ("run_token", "host", "started", "generation", "spec")
_OWNER_LABELS = {
    "run_token": "Run-token",
    "host": "Host",
    "started": "Started",
    "generation": "Generation",
    "spec": "Spec",
}


def format_owner(run_token, host, started, generation, spec):
    """Render a DRAIN-OWNER.md body (format unchanged from reference.md)."""
    return (
        f"Run-token: {run_token}\n"
        f"Host: {host}\n"
        f"Started: {started}\n"
        f"Generation: {generation}\n"
        f"Spec: {spec}\n"
    )


def parse_owner(text):
    """Parse a DRAIN-OWNER.md body into its fields (`run_token`, `host`,
    `started`, `generation`, `spec`). Missing labels map to None."""
    values = {k: None for k in _OWNER_FIELDS}
    label_to_key = {v: k for k, v in _OWNER_LABELS.items()}
    for line in text.splitlines():
        if ":" not in line:
            continue
        label, _, rest = line.partition(":")
        key = label_to_key.get(label.strip())
        if key:
            values[key] = rest.strip()
    return values


def claim_decision(present, liveness, baton_token=None, owner_token=None):
    """The pure lease-claim decision, matching reference.md exactly:

    * owner absent            -> "claim"
    * owner FRESH             -> "claim" iff the baton's Run-token matches the
                                 owner's (baton lineage), else "refuse"
    * owner ALL STALE         -> "reclaim"
    """
    if not present:
        return "claim"
    if liveness == "FRESH":
        if baton_token is not None and baton_token == owner_token:
            return "claim"
        return "refuse"
    if liveness == "ALL_STALE":
        return "reclaim"
    raise AdmissionError(f"unknown liveness {liveness!r}")


def owner_path(spec_dir):
    return Path(spec_dir) / "DRAIN-OWNER.md"


def read_owner(spec_dir):
    """The DRAIN-OWNER.md body for a spec, or None if absent."""
    p = owner_path(spec_dir)
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return None


def owner_liveness(spec_dir, window_seconds=_STALE_WINDOW_SECONDS, now=None):
    """FRESH vs ALL_STALE for a spec's owner, from the committer timestamp of
    the last commit touching the spec dir (reference.md's primary liveness
    signal): FRESH if younger than the grace window, ALL_STALE otherwise (or
    when there is no such commit)."""
    ts = _last_commit_epoch(spec_dir)
    if ts is None:
        return "ALL_STALE"
    now = time.time() if now is None else now
    return "FRESH" if (now - ts) < window_seconds else "ALL_STALE"


def git_cas_claim(spec_dir, owner_text, run_token, remote="origin"):
    """Write DRAIN-OWNER.md, commit, push (when a remote is configured), then
    re-read at HEAD and confirm our Run-token is the one present — the
    read-check-write-commit-push-reread-confirm CAS from reference.md.

    Returns True iff our token wins the lease. A rejected push (a competitor
    committed first) resyncs to the remote tip and re-reads, so the loser sees
    the winner's token and returns False rather than proceeding as if it had
    won. Genuine multi-process races against this are proven in
    test_admission_concurrency.py (task 05)."""
    spec_dir = Path(spec_dir)
    op = owner_path(spec_dir)
    op.write_text(owner_text, encoding="utf-8")
    _git(spec_dir, "add", str(op))
    _git(spec_dir, "commit", "-q", "-m", f"drain: claim lease {spec_dir.name}")
    if _has_remote(spec_dir, remote):
        pushed = _git_ok(spec_dir, "push", "-q", remote, "HEAD")
        if not pushed:
            _git_ok(spec_dir, "fetch", "-q", remote)
            _git_ok(spec_dir, "reset", "-q", "--hard", f"{remote}/HEAD")
    present = read_owner(spec_dir)
    return present is not None and parse_owner(present).get("run_token") == run_token


def _git(spec_dir, *args):
    subprocess.run(["git", "-C", str(spec_dir), *args], check=True)


def _git_ok(spec_dir, *args):
    return (
        subprocess.run(
            ["git", "-C", str(spec_dir), *args],
            capture_output=True,
        ).returncode
        == 0
    )


def _has_remote(spec_dir, remote):
    return _git_ok(spec_dir, "remote", "get-url", remote)


def _last_commit_epoch(spec_dir):
    spec_dir = Path(spec_dir)
    res = subprocess.run(
        ["git", "-C", str(spec_dir), "log", "-1", "--format=%ct", "--", str(spec_dir)],
        capture_output=True,
        text=True,
    )
    out = res.stdout.strip()
    if res.returncode != 0 or not out:
        return None
    try:
        return int(out)
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
# CLI: consume a frontier JSON file, emit the admission decision.
# --------------------------------------------------------------------------- #
def _candidates_from_frontier(frontier):
    """Spec-claim candidates in the frontier's dispatchable (Priority-then-path)
    order: each spec in first-appearance order, with its dispatchable task
    file paths for footprint computation."""
    by_spec = {}
    order = []
    for entry in frontier["dispatchable"]:
        spec = spec_of(entry["path"])
        if spec not in by_spec:
            by_spec[spec] = {
                "spec": spec,
                "task_files": [],
                "priority": entry.get("priority", "P2"),
            }
            order.append(spec)
        by_spec[spec]["task_files"].append(entry["path"])
    return [by_spec[s] for s in order]


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Drain cross-spec lease-claim and two-level admission cap."
    )
    parser.add_argument(
        "--frontier",
        required=True,
        help="path to a drain_frontier.py JSON report (- for stdin)",
    )
    parser.add_argument("--spec-cap", type=int, default=3)
    parser.add_argument("--window", type=int, default=5, help="per-spec W (<=5)")
    parser.add_argument("--global-cap", type=int, default=10)
    args = parser.parse_args(argv)

    raw = (
        sys.stdin.read()
        if args.frontier == "-"
        else Path(args.frontier).read_text(encoding="utf-8")
    )
    try:
        frontier = load_frontier(json.loads(raw))
    except (AdmissionError, json.JSONDecodeError, OSError) as exc:
        print(f"admission: malformed frontier: {exc}", file=sys.stderr)
        return 2

    claimed = claim_specs(_candidates_from_frontier(frontier), cap=args.spec_cap)
    claimed_specs = {c["spec"] for c in claimed}
    admissible = [
        e for e in frontier["admissible"] if spec_of(e["path"]) in claimed_specs
    ]
    admitted = admit_tasks(admissible, w=args.window, global_cap=args.global_cap)

    json.dump(
        {
            "claimed_specs": [c["spec"] for c in claimed],
            "admitted_tasks": [e["path"] for e in admitted],
        },
        sys.stdout,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
