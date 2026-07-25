"""Legacy module compatibility is diagnostic-only and never mutates files."""

from argparse import Namespace

from agentic import shadow


def test_shadow_run_is_the_exact_non_mutating_retirement_diagnostic(
    tmp_path, capsys, monkeypatch
):
    task = tmp_path / "specs" / "demo" / "tasks" / "01-task.md"
    task.parent.mkdir(parents=True)
    task.write_text("Status: pending\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert shadow.run(Namespace()) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        "agentic shadow-sync: retired; task state lives in bd; "
        "use register-spec only for new tasks\n"
    )
    assert task.read_text(encoding="utf-8") == "Status: pending\n"
    assert not (tmp_path / ".beads").exists()
