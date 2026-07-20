#!/usr/bin/env python3
"""Tests for admission.py — R1 spec-lease claim eligibility, R2 two-level
cross-spec admission cap, R14 JSON-schema boundary, and the DRAIN-OWNER.md
git-CAS lease-claim protocol (step 6).

Self-running: `python3 test_admission.py` runs every case, prints one line per
fixture case (`case a` .. `case e`) plus the supporting cases, and exits
non-zero on the first failure. There is no central pytest runner in this repo;
the task's acceptance invokes this file directly and greps its stdout for the
five distinct fixture cases. See
specs/drain-multi-spec-swarm/tasks/04-admission-module.md (Steps 7-11) and
../SPEC.md (R1, R2, R4, R5, R6, R14).
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from admission import (
    AdmissionError,
    admit_tasks,
    claim_decision,
    claim_specs,
    format_owner,
    git_cas_claim,
    load_frontier,
    owner_liveness,
    parse_owner,
    read_owner,
    spec_of,
)


def _write_task(tasks_dir, name, touch):
    tasks_dir.mkdir(parents=True, exist_ok=True)
    tf = tasks_dir / name
    tf.write_text(f"# {name}\n\nStatus: pending\nTouch: {touch}\n", encoding="utf-8")
    return str(tf)


def _spec(root, slug, touch):
    """A fixture spec dir with one dispatchable task carrying `touch`. Returns
    a candidate dict for claim_specs (spec dir + its dispatchable task files)."""
    spec_dir = Path(root) / "specs" / slug
    tf = _write_task(spec_dir / "tasks", "01-x.md", touch)
    return {"spec": str(spec_dir), "task_files": [tf], "priority": "P1"}


def _entry(spec_dir, name, priority="P1"):
    return {"path": str(Path(spec_dir) / "tasks" / name), "priority": priority}


# ---- case (a): 3 mutually-disjoint specs all claim (R1/R4) ----
def case_a_three_disjoint_specs_all_claim():
    with tempfile.TemporaryDirectory() as d:
        a = _spec(d, "alpha", "src/alpha/")
        b = _spec(d, "beta", "src/beta/")
        c = _spec(d, "gamma", "docs/gamma.md")
        claimed = claim_specs([a, b, c], cap=3)
        specs = {c["spec"] for c in claimed}
        assert specs == {a["spec"], b["spec"], c["spec"]}, specs
        assert len(claimed) == 3


# ---- case (b): 4th overlapping spec excluded from concurrent claim (R5) ----
def case_b_overlapping_spec_excluded():
    with tempfile.TemporaryDirectory() as d:
        a = _spec(d, "alpha", "src/alpha/mod.py")
        b = _spec(d, "beta", "src/beta/")
        # dd overlaps alpha (shares the src/alpha/ prefix), disjoint from beta.
        dd = _spec(d, "delta", "src/alpha/")
        claimed = claim_specs([a, b, dd], cap=3)
        specs = {c["spec"] for c in claimed}
        # only ONE of the colliding pair (alpha, delta) is admitted; cap=3 is
        # not the limiter here (only 3 candidates), so exclusion is by overlap.
        assert a["spec"] in specs
        assert dd["spec"] not in specs
        assert b["spec"] in specs
        assert len(claimed) == 2


# ---- case (c): cross-spec disjoint tasks co-admit (R2) ----
def case_c_cross_spec_disjoint_tasks_coadmit():
    a_admissible = [_entry("specs/alpha", "01-x.md")]
    b_admissible = [_entry("specs/beta", "01-y.md")]
    admitted = admit_tasks(a_admissible + b_admissible)
    paths = {e["path"] for e in admitted}
    assert paths == {a_admissible[0]["path"], b_admissible[0]["path"]}, paths


# ---- case (d): "window empty" is per-spec, not global ----
def case_d_window_empty_is_per_spec():
    a1 = _entry("specs/alpha", "01-x.md")
    a2 = _entry("specs/alpha", "02-y.md")
    # frontier already dropped the ungrouped 2nd task; admit honors that set,
    # never re-adding a2 from dispatchable.
    admitted = admit_tasks([a1])
    assert {e["path"] for e in admitted} == {a1["path"]}
    assert a2["path"] not in {e["path"] for e in admitted}
    # an in-flight task in a DIFFERENT spec does not close alpha's window
    admitted = admit_tasks([a1], in_flight={"specs/beta": 1}, w=1)
    assert a1["path"] in {e["path"] for e in admitted}
    # an in-flight task in alpha's OWN spec does close its window (W=1)
    admitted = admit_tasks([a1], in_flight={"specs/alpha": 1}, w=1)
    assert a1["path"] not in {e["path"] for e in admitted}


# ---- case (e): two-level cap throttles 15 candidates to 10 (per-spec W<=5) ----
def case_e_two_level_cap_throttle():
    admissible = []
    for slug in ("alpha", "beta", "gamma"):
        for i in range(5):
            admissible.append(_entry(f"specs/{slug}", f"0{i}-t.md"))
    admitted = admit_tasks(admissible, w=5, global_cap=10)
    assert len(admitted) == 10, len(admitted)
    per_spec = {}
    for e in admitted:
        per_spec[spec_of(e["path"])] = per_spec.get(spec_of(e["path"]), 0) + 1
    assert max(per_spec.values()) <= 5, per_spec


# ---- supporting: R14 negative — malformed frontier JSON errors loudly ----
def support_load_frontier_rejects_malformed():
    for bad in (
        {"admissible": [], "blocked": []},  # missing dispatchable
        {"dispatchable": "nope", "admissible": [], "blocked": []},  # wrong type
        {"dispatchable": [], "admissible": {}, "blocked": []},  # wrong type
    ):
        try:
            load_frontier(bad)
        except AdmissionError:
            continue
        raise AssertionError(f"expected AdmissionError for {bad!r}")
    # a well-formed frontier loads cleanly
    load_frontier(
        {"dispatchable": [], "admissible": [], "blocked": [], "diagnostics": []}
    )


def support_cli_exits_nonzero_on_malformed_frontier():
    with tempfile.TemporaryDirectory() as d:
        bad = Path(d) / "frontier.json"
        bad.write_text('{"admissible": []}', encoding="utf-8")
        script = str(Path(__file__).with_name("admission.py"))
        rc = subprocess.run(
            [sys.executable, script, "--frontier", str(bad)],
            capture_output=True,
        ).returncode
        assert rc != 0, rc


# ---- supporting: DRAIN-OWNER.md git-CAS lease-claim protocol (step 6) ----
def support_claim_decision_matches_reference():
    # absent -> claim
    assert claim_decision(present=False, liveness=None) == "claim"
    # FRESH -> refuse unless the baton's run-token matches the owner's
    assert (
        claim_decision(
            present=True, liveness="FRESH", baton_token=None, owner_token="abc"
        )
        == "refuse"
    )
    assert (
        claim_decision(
            present=True, liveness="FRESH", baton_token="abc", owner_token="abc"
        )
        == "claim"
    )
    assert (
        claim_decision(
            present=True, liveness="FRESH", baton_token="xyz", owner_token="abc"
        )
        == "refuse"
    )
    # ALL STALE -> reclaim
    assert claim_decision(present=True, liveness="ALL_STALE") == "reclaim"


def support_owner_roundtrip():
    text = format_owner(
        run_token="ab12ef",
        host="host1",
        started="2026-07-20T00:00:00Z",
        generation=1,
        spec="specs/alpha",
    )
    d = parse_owner(text)
    assert d["run_token"] == "ab12ef"
    assert d["generation"] == "1"
    assert d["spec"] == "specs/alpha"


def support_git_cas_claim_happy_path():
    with tempfile.TemporaryDirectory() as d:
        spec_dir = Path(d) / "specs" / "alpha"
        spec_dir.mkdir(parents=True)
        for args in (
            ["init", "-q"],
            ["config", "user.email", "t@t"],
            ["config", "user.name", "t"],
        ):
            subprocess.run(["git", "-C", d, *args], check=True)
        (Path(d) / "seed").write_text("x", encoding="utf-8")
        subprocess.run(["git", "-C", d, "add", "-A"], check=True)
        subprocess.run(["git", "-C", d, "commit", "-qm", "seed"], check=True)
        owner = format_owner(
            run_token="win123",
            host="h",
            started="2026-07-20T00:00:00Z",
            generation=1,
            spec=str(spec_dir),
        )
        won = git_cas_claim(str(spec_dir), owner, "win123")
        assert won is True
        back = parse_owner(read_owner(str(spec_dir)))
        assert back["run_token"] == "win123"


def _git_init(root, email, name):
    for args in (
        ["init", "-q"],
        ["config", "user.email", email],
        ["config", "user.name", name],
    ):
        subprocess.run(["git", "-C", str(root), *args], check=True)


def support_owner_liveness_fresh_after_recent_commit():
    # A commit touching the spec dir moments ago must read as FRESH within a
    # generous window (regression: a double-nested `-C dir` + relative-dir
    # pathspec logged nothing, so liveness fell through to ALL_STALE always,
    # defeating FRESH-lease protection).
    with tempfile.TemporaryDirectory() as d:
        spec_dir = Path(d) / "specs" / "alpha"
        spec_dir.mkdir(parents=True)
        _git_init(d, "t@t", "t")
        (spec_dir / "SPEC.md").write_text("# a\n", encoding="utf-8")
        subprocess.run(["git", "-C", d, "add", "-A"], check=True)
        subprocess.run(["git", "-C", d, "commit", "-qm", "seed"], check=True)
        # Production calls owner_liveness with a RELATIVE spec dir (spec_of
        # returns specs/<slug>); exercise that path — a double-nested pathspec
        # regression only bites relative dirs, so an absolute-path fixture would
        # mask it.
        prev = os.getcwd()
        try:
            os.chdir(d)
            assert owner_liveness("specs/alpha", window_seconds=3600) == "FRESH"
            assert owner_liveness("specs/alpha", window_seconds=0) == "ALL_STALE"
        finally:
            os.chdir(prev)


def support_git_cas_claim_loser_reports_false():
    # Behavioral guard: a racer whose push is rejected must resync to the
    # pushed branch, re-read at the new HEAD, and report False (never a
    # double-win) — and end up seeing the winner's token. The resync targets
    # the actual pushed branch via FETCH_HEAD rather than the frequently-unset
    # `origin/HEAD` symref. NOTE: this is not a discriminating regression test
    # for that symref bug specifically — on a default-branch fixture `git fetch`
    # can restore `origin/HEAD`, masking it; the genuine multi-process /
    # non-default-branch race is task 05's (test_admission_concurrency.py). It
    # still asserts the correct lost-race behavior end to end.
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        bare = td / "origin.git"
        subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
        c1 = td / "c1"
        subprocess.run(["git", "clone", "-q", str(bare), str(c1)], check=True)
        for args in (["config", "user.email", "a@a"], ["config", "user.name", "a"]):
            subprocess.run(["git", "-C", str(c1), *args], check=True)
        (c1 / "specs" / "alpha").mkdir(parents=True)
        (c1 / "seed").write_text("x", encoding="utf-8")
        subprocess.run(["git", "-C", str(c1), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(c1), "commit", "-qm", "seed"], check=True)
        subprocess.run(
            ["git", "-C", str(c1), "push", "-q", "origin", "HEAD"], check=True
        )
        # Loser clones the seed base, then unsets origin/HEAD so the resync
        # cannot lean on that symref.
        c2 = td / "c2"
        subprocess.run(["git", "clone", "-q", str(bare), str(c2)], check=True)
        for args in (["config", "user.email", "b@b"], ["config", "user.name", "b"]):
            subprocess.run(["git", "-C", str(c2), *args], check=True)
        subprocess.run(["git", "-C", str(c2), "remote", "set-head", "origin", "-d"])
        # confirm origin/HEAD is unset at this point — the fixed resync fetches
        # the pushed branch and resets to FETCH_HEAD, so it must not depend on
        # origin/HEAD to reach the winner's tip.
        assert (
            subprocess.run(
                ["git", "-C", str(c2), "rev-parse", "--verify", "-q", "origin/HEAD"],
                capture_output=True,
            ).returncode
            != 0
        )
        (c2 / "specs" / "alpha").mkdir(parents=True)
        spec1, spec2 = c1 / "specs" / "alpha", c2 / "specs" / "alpha"
        win = format_owner("winner", "a", "t", 1, str(spec1))
        assert git_cas_claim(str(spec1), win, "winner") is True
        lose = format_owner("loser", "b", "t", 1, str(spec2))
        assert git_cas_claim(str(spec2), lose, "loser") is False
        assert parse_owner(read_owner(str(spec2)))["run_token"] == "winner"


_CASES = [
    (
        "case a: 3 mutually-disjoint specs all claim (R1/R4)",
        case_a_three_disjoint_specs_all_claim,
    ),
    (
        "case b: 4th overlapping spec excluded from concurrent claim (R5)",
        case_b_overlapping_spec_excluded,
    ),
    (
        "case c: cross-spec disjoint tasks co-admit (R2)",
        case_c_cross_spec_disjoint_tasks_coadmit,
    ),
    (
        "case d: window-empty is per-spec, not global (R2)",
        case_d_window_empty_is_per_spec,
    ),
    (
        "case e: two-level cap throttles 15 candidates to 10 (per-spec W<=5)",
        case_e_two_level_cap_throttle,
    ),
    (
        "R14 negative: malformed frontier JSON errors loudly",
        support_load_frontier_rejects_malformed,
    ),
    (
        "R14 negative: CLI exits non-zero on malformed frontier",
        support_cli_exits_nonzero_on_malformed_frontier,
    ),
    (
        "lease claim_decision matches reference.md (absent/FRESH/ALL STALE)",
        support_claim_decision_matches_reference,
    ),
    ("DRAIN-OWNER.md parse/format round-trip", support_owner_roundtrip),
    ("git-CAS lease claim happy path", support_git_cas_claim_happy_path),
    (
        "owner liveness reads FRESH after a recent spec-dir commit",
        support_owner_liveness_fresh_after_recent_commit,
    ),
    (
        "git-CAS lease loser reports False, never a double-win",
        support_git_cas_claim_loser_reports_false,
    ),
]


def _run():
    for name, fn in _CASES:
        try:
            fn()
        except AssertionError as exc:
            print(f"FAIL: {name}: {exc}", file=sys.stderr)
            return 1
        print(f"ok: {name}")
    print(f"all {len(_CASES)} admission tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(_run())
