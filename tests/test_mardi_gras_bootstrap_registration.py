from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import uuid
from argparse import Namespace
from datetime import datetime, timezone
from pathlib import Path

import pytest


REPOSITORY = Path(__file__).resolve().parents[1]
SCRIPT = (
    REPOSITORY
    / "specs"
    / "mardi-gras-agentic-integration"
    / "bootstrap-registration.py"
)


def load_controller():
    spec = importlib.util.spec_from_file_location("mardi_bootstrap", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run(argv, cwd, env=None):
    return subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )


FAKE_TOOL = r"""#!/usr/bin/env python3
import hashlib,json,os,shutil,subprocess,sys
from pathlib import Path

state_path=Path(os.environ["FAKE_BOOTSTRAP_STATE"])
def canonical(v):
    return json.dumps(v,ensure_ascii=True,sort_keys=True,separators=(",",":")).encode()
def sha(v):
    return hashlib.sha256(canonical(v) if not isinstance(v,(bytes,bytearray)) else v).hexdigest()
def schema(label):
    return hashlib.sha256(("schema:"+label).encode()).hexdigest()
def load():
    return json.loads(state_path.read_text()) if state_path.exists() else {"issues":{},"profiles":[],"schema_fingerprint":schema("base"),"calls":[],"install_receipts":[],"mutation_receipts":[],"history_counter":0}
def save(s):
    state_path.write_text(json.dumps(s,sort_keys=True,separators=(",",":")))
def flag(a,name,default=None):
    return a[a.index(name)+1] if name in a else default
def emit(v,code=0):
    print(json.dumps(v,sort_keys=True,separators=(",",":"))); raise SystemExit(code)
def bump(issue):
    old=issue.get("authority_revision","r0"); issue["authority_revision"]="r"+str(int(old[1:])+1)
def history_cursor(s):
    s["history_counter"]+=1; return "h"+str(s["history_counter"])
def mutation_response(s,request,operation,issue,before):
    request_sha=sha(request); existing=[r for r in s["mutation_receipts"] if r["request_sha256"]==request_sha]
    if existing:
        receipt=existing[0]
    else:
        cursor=history_cursor(s); after=issue["authority_revision"]
        receipt={"schema_version":"agentic.bd-authority-mutation-receipt/v1","request_sha256":request_sha,"operation":operation,"actor":request["actor"],"reason":request["reason"],"issue_id":issue["id"],"before_revision":before,"after_revision":after,"history_cursor":cursor}
        if os.environ.get("FAKE_BOOTSTRAP_BAD_RESPONSE")=="mutation_bad_before": receipt["before_revision"]="forged"
        if os.environ.get("FAKE_BOOTSTRAP_BAD_RESPONSE")=="mutation_bad_cursor": receipt["history_cursor"]="forged"
        s["mutation_receipts"].append(receipt)
        bad_history=os.environ.get("FAKE_BOOTSTRAP_BAD_HISTORY")
        if bad_history!="missing":
            event_actor="foreign" if bad_history=="foreign" else request["actor"]
            issue["history"].append({"action":operation,"actor":event_actor,"reason":request["reason"],"request_sha256":request_sha,"before_revision":before,"after_revision":after,"history_cursor":cursor})
    schemas={"bootstrap_finalize":"agentic.bd-bootstrap-finalize-result/v1","guarded_create":"agentic.bd-guarded-create-result/v1","conditional_close":"agentic.bd-authority-transaction-result/v1"}
    returned=dict(receipt)
    if os.environ.get("FAKE_BOOTSTRAP_BAD_RESPONSE")=="mutation_action_fork": returned["history_cursor"]="forked"
    return {"schema_version":schemas[operation],"ok":True,"operation":operation,"receipt":returned}

role=os.environ.get("AGENTIC_BOOTSTRAP_ROLE")
if role:
    envelope=json.loads(Path(os.environ["AGENTIC_BOOTSTRAP_ENVELOPE"]).read_text())
    result_path=Path(os.environ["AGENTIC_BOOTSTRAP_RESULT"])
    if role=="worker":
        touch={"00A":"specs/mardi-gras-agentic-integration/upstream/beads-authority-core.patch","00B":"specs/mardi-gras-agentic-integration/upstream/beads-authority-conditional.patch","00C":"specs/mardi-gras-agentic-integration/upstream/beads-authority-supersession.patch","00D":"agentic/authority.py"}[envelope["bootstrap_id"]]
        target=Path(touch); target.parent.mkdir(parents=True,exist_ok=True); target.write_text(envelope["bootstrap_id"]+"\n")
        subprocess.run(["git","add","--",touch],check=True,capture_output=True,text=True)
        subprocess.run(["git","commit","-m",envelope["bootstrap_id"]],check=True,capture_output=True,text=True)
        commit=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
        provider=None
        if envelope["bootstrap_id"]!="00D":
            root=result_path.parents[1]
            output=root/"outputs"/envelope["bootstrap_id"].lower()/"bd"
            (root/"outputs").mkdir(parents=True,exist_ok=True); (root/"outputs").chmod(0o700)
            output.parent.mkdir(parents=True,exist_ok=True); output.parent.chmod(0o700)
            shutil.copy2(Path(__file__),output); output.chmod(0o700)
            provider={"path":str(output),"sha256":hashlib.sha256(output.read_bytes()).hexdigest(),"source_commit":commit}
        value={"schema_version":"agentic.registration-bootstrap-worker-result/v1","ok":True,"intent":envelope["intent"],"run_id":envelope["run_id"],"bootstrap_id":envelope["bootstrap_id"],"issue":envelope["issue"],"base_commit":envelope["base_commit"],"commit":commit,"provider":provider}
    else:
        commit=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
        diff=subprocess.check_output(["git","diff","--binary",envelope["base_commit"],commit,"--"])
        value={"schema_version":"agentic.registration-bootstrap-review-result/v1","ok":True,"verdict":"READY","intent":envelope["intent"],"run_id":envelope["run_id"],"bootstrap_id":envelope["bootstrap_id"],"issue":envelope["issue"],"base_commit":envelope["base_commit"],"commit":commit,"reviewer":"fake-independent-reviewer","diff_sha256":hashlib.sha256(diff).hexdigest()}
    result_path.parent.mkdir(parents=True,exist_ok=True)
    result_path.write_text(json.dumps(value,sort_keys=True,separators=(",",":")))
    result_path.chmod(0o600)
    raise SystemExit(0)

a=sys.argv[1:]; s=load(); s["calls"].append(a)
if a[:2]==["context","--json"]:
    save(s); emit({"backend":"dolt","database":"beads","project_id":"agentic","repo_root":os.environ["FAKE_BOOTSTRAP_REPO"],"dolt_mode":"local"})
if a and a[0]=="create":
    issue_id=flag(a,"--id"); metadata=json.loads(Path(flag(a,"--metadata")[1:]).read_text())
    if issue_id in s["issues"]: save(s); emit({"error":"exists"},1)
    creator="foreign" if os.environ.get("FAKE_BOOTSTRAP_BAD_CREATOR")=="foreign" else flag(a,"--actor")
    s["issues"][issue_id]={"id":issue_id,"title":flag(a,"--title"),"description":flag(a,"--description"),"acceptance":flag(a,"--acceptance"),"issue_type":flag(a,"--type"),"status":"open","priority":0,"external_ref":None,"assignee":None,"notes":"","metadata":metadata,"authority_revision":"r0","dependencies":[],"history":[{"action":"create","actor":creator}]}
    save(s); emit(s["issues"][issue_id])
if a[:2]==["show","--json"]:
    issue_id=a[-1]; issue=s["issues"].get(issue_id); save(s)
    emit([issue] if issue else [],0 if issue else 1)
if a[:2]==["history","--json"]:
    issue=s["issues"].get(a[-1]); save(s); emit(issue.get("history",[]) if issue else [],0 if issue else 1)
if a[:2]==["ready","--json"]:
    ready=[]
    for issue in s["issues"].values():
        if issue["status"]!="open": continue
        blockers=[edge["depends_on"] for edge in issue.get("dependencies",[]) if edge["type"]=="blocks"]
        if all(s["issues"][dep]["status"]=="closed" for dep in blockers): ready.append(issue)
    save(s); emit(ready)
if a[:2]==["list","--all"]:
    save(s); emit(list(s["issues"].values()))
if a and a[0]=="update" and "--claim" in a:
    issue=s["issues"][a[-1]]
    if os.environ.get("FAKE_BOOTSTRAP_RACE")=="1":
        issue["status"]="in_progress"; issue["assignee"]="foreign-racer"; bump(issue); save(s); emit({"error":"lost"},1)
    actor=flag(a,"--actor")
    if issue["status"]=="open":
        issue["status"]="in_progress"; issue["assignee"]=actor; bump(issue); save(s); emit(issue)
    if issue["assignee"]==actor: save(s); emit(issue)
    save(s); emit({"error":"claimed"},1)
if a[:4]==["authority","identity","--no-migrate","--json"]:
    identity={"schema_version":"agentic.bd-authority-identity-result/v1","ok":True,"full_profile_identity":{"backend_mode":"dolt","database_identity":"beads","project_identity":"agentic","repository_identity":sha({"backend":"dolt","database":"beads","project":"agentic"}),"core_schema_fingerprint":schema("core"),"full_schema_fingerprint":schema("full")},"profiles":s["profiles"],"schema_fingerprint":s["schema_fingerprint"],"history_cursor":"h"+str(s["history_counter"]),"install_receipts":s["install_receipts"],"mutation_receipts":s["mutation_receipts"]}
    if os.environ.get("FAKE_BOOTSTRAP_BAD_RESPONSE")=="identity_missing":
        del identity["history_cursor"]
    save(s); emit(identity)
if a[:2]==["authority","install"]:
    profile=flag(a,"--profile"); request={"profile":profile,"migration_id":flag(a,"--migration-id"),"migration_host":flag(a,"--migration-host"),"if_schema":flag(a,"--if-schema"),"actor":flag(a,"--actor")}; request_sha=sha(request)
    matches=[r for r in s["install_receipts"] if r["request_sha256"]==request_sha]
    if matches:
        receipt=matches[0]
    else:
        receipt={"schema_version":"agentic.bd-authority-install-receipt/v1","request_sha256":request_sha,"actor":request["actor"],"profile":profile,"migration_id":request["migration_id"],"migration_host":request["migration_host"],"before_schema":request["if_schema"],"after_schema":schema(profile),"history_cursor":history_cursor(s)}
        if os.environ.get("FAKE_BOOTSTRAP_BAD_RESPONSE")=="install_foreign_actor":
            receipt["actor"]="foreign"
        if os.environ.get("FAKE_BOOTSTRAP_BAD_RESPONSE")=="install_bad_after":
            receipt["after_schema"]=schema("forged")
        if os.environ.get("FAKE_BOOTSTRAP_BAD_RESPONSE")=="install_bad_cursor":
            receipt["history_cursor"]="forged"
        s["install_receipts"].append(receipt)
        if profile not in s["profiles"]: s["profiles"].append(profile)
        s["schema_fingerprint"]=schema(profile)
    returned=dict(receipt)
    if os.environ.get("FAKE_BOOTSTRAP_BAD_RESPONSE")=="install_action_fork": returned["history_cursor"]="forked"
    save(s); emit({"schema_version":"agentic.bd-authority-install-result/v1","ok":True,"operation":"install","receipt":returned})
if a[:2]==["authority","bootstrap-finalize"]:
    request=json.loads(Path(flag(a,"--request")).read_text()); issue=s["issues"][request["issue_id"]]
    existing=[r for r in s["mutation_receipts"] if r["request_sha256"]==sha(request)]
    if existing: save(s); emit(mutation_response(s,request,"bootstrap_finalize",issue,existing[0]["before_revision"]))
    expected=request["expected"]
    if issue["status"]!=expected["status"] or issue["assignee"]!=expected["assignee"] or issue["external_ref"] is not None or issue["authority_revision"]!=expected["authority_revision"]: save(s); emit({"ok":False},1)
    before=issue["authority_revision"]; issue["status"]="closed"; issue["external_ref"]=request["after"]["external_ref"]; issue["dependencies"]=[{"depends_on":request["after"]["container"]["issue_id"],"type":request["after"]["container"]["relation"]}]; bump(issue); response=mutation_response(s,request,"bootstrap_finalize",issue,before); save(s); emit(response)
if a[:2]==["authority","guarded-create"]:
    request=json.loads(Path(flag(a,"--request")).read_text()); envelope=request["envelope"]; issue_id=request["issue_id"]
    existing_receipt=[r for r in s["mutation_receipts"] if r["request_sha256"]==sha(request)]
    if existing_receipt: issue=s["issues"][issue_id]; save(s); emit(mutation_response(s,request,"guarded_create",issue,None))
    if any(i["external_ref"]==envelope["canonical_external_ref"] for i in s["issues"].values()): save(s); emit({"ok":False},1)
    edges=[{"depends_on":edge["depends_on"],"type":edge["type"]} for edge in request["initial_edges"]]
    if os.environ.get("FAKE_BOOTSTRAP_BAD_EDGE")=="1": edges=edges[:1]
    issue_type="bug" if os.environ.get("FAKE_BOOTSTRAP_BAD_TYPE")=="1" else envelope["issue_type"]
    issue={"id":issue_id,"title":envelope["title"],"description":envelope["description"],"acceptance":envelope["acceptance"],"issue_type":issue_type,"status":"open","priority":0,"external_ref":envelope["canonical_external_ref"],"assignee":None,"notes":"","metadata":envelope["metadata"],"authority_revision":"r1","dependencies":edges,"history":[]}
    s["issues"][issue_id]=issue; response=mutation_response(s,request,"guarded_create",issue,None); save(s); emit(response)
if a[:2]==["authority","transaction"]:
    request=json.loads(Path(flag(a,"--request")).read_text()); expected=request["expected"][0]; issue=s["issues"][expected["issue_id"]]
    existing=[r for r in s["mutation_receipts"] if r["request_sha256"]==sha(request)]
    if existing: save(s); emit(mutation_response(s,request,"conditional_close",issue,existing[0]["before_revision"]))
    if any((issue["authority_revision"]!=expected["authority_revision"],issue["status"]!=expected["status"],issue["assignee"]!=expected["assignee"])): save(s); emit({"ok":False},1)
    before=issue["authority_revision"]; issue["status"]="closed"; bump(issue); response=mutation_response(s,request,"conditional_close",issue,before); save(s); emit(response)
save(s); emit({"error":"unsupported","argv":a},2)
"""


def git_commit(repo: Path, message: str) -> str:
    run(["git", "add", "-A"], repo)
    run(["git", "commit", "-m", message], repo)
    return run(["git", "rev-parse", "HEAD"], repo).stdout.strip()


def prepare_attested_repo(tmp_path: Path, monkeypatch):
    module = load_controller()
    repo = tmp_path / "repo"
    source_spec = REPOSITORY / "specs" / "mardi-gras-agentic-integration"
    destination = repo / "specs" / "mardi-gras-agentic-integration"
    shutil.copytree(source_spec, destination)
    run(["git", "init", "-q"], repo)
    run(["git", "config", "user.email", "bootstrap@example.invalid"], repo)
    run(["git", "config", "user.name", "Bootstrap Test"], repo)
    baseline = git_commit(repo, "bootstrap source baseline")

    controller_path = destination / "bootstrap-registration.py"
    config_path = destination / "bootstrap-registration-v1.json"
    workflow_path = destination / "bootstrap-00a-workflow.md"
    module.REPO_ROOT = repo
    module.SCRIPT_PATH = controller_path
    module.SPEC_DIR = destination
    module.CONFIG_PATH = config_path

    config = json.loads(config_path.read_text())
    task_hashes = {
        source: hashlib.sha256((repo / source).read_bytes()).hexdigest()
        for _, source, *_ in module.TASKS
    }
    source_subject = {
        "schema_version": module.ATTESTATION_SCHEMA,
        "source_commit": baseline,
        "source_date_utc": datetime.fromtimestamp(
            int(run(["git", "show", "-s", "--format=%at", baseline], repo).stdout),
            tz=timezone.utc,
        ).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
        "spec_sha256": hashlib.sha256((repo / module.SPEC_PATH).read_bytes()).hexdigest(),
        "workflow_sha256": hashlib.sha256(workflow_path.read_bytes()).hexdigest(),
        "controller_sha256": hashlib.sha256(controller_path.read_bytes()).hexdigest(),
        "task_sha256": task_hashes,
    }
    config["attestation"] = {
        **source_subject,
        "ready_review": {
            "reviewer": "independent-test-critic",
            "verdict": "READY",
            "subject_sha256": hashlib.sha256(
                module._canonical_json(source_subject)
            ).hexdigest(),
            "evidence_sha256": "a" * 64,
        },
    }
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    attestation = git_commit(repo, "attest bootstrap source")

    tool = tmp_path / "fake-tool"
    tool.write_text(FAKE_TOOL)
    tool.chmod(0o700)
    state_file = tmp_path / "tracker.json"
    state_root = tmp_path / "state"
    state_root.mkdir(mode=0o700)
    monkeypatch.setenv("FAKE_BOOTSTRAP_STATE", str(state_file))
    monkeypatch.setenv("FAKE_BOOTSTRAP_REPO", str(repo))
    monkeypatch.delenv("FAKE_BOOTSTRAP_RACE", raising=False)
    monkeypatch.delenv("FAKE_BOOTSTRAP_BAD_RESPONSE", raising=False)
    monkeypatch.delenv("FAKE_BOOTSTRAP_BAD_HISTORY", raising=False)
    monkeypatch.delenv("FAKE_BOOTSTRAP_BAD_EDGE", raising=False)
    monkeypatch.delenv("FAKE_BOOTSTRAP_BAD_CREATOR", raising=False)
    monkeypatch.delenv("FAKE_BOOTSTRAP_BAD_TYPE", raising=False)

    def fake_accept(self, bootstrap_id, _worktree):
        kind = f"{bootstrap_id.lower()}_acceptance"
        committed = self.journal.committed(kind)
        if committed:
            return committed
        request = {"bootstrap_id": bootstrap_id, "commands": [["fake-acceptance"]]}
        if self.journal.prepared(kind) is None:
            self.journal.append(kind, "prepared", request)
        receipt = {"request_sha256": hashlib.sha256(module._canonical_json(request)).hexdigest(), "ok": True}
        self.journal.append(kind, "committed", receipt)
        return receipt

    monkeypatch.setattr(module.BootstrapController, "_accept", fake_accept)
    deps = module.ControllerDependencies(
        state_root=state_root,
        bd=tool,
        runtime=tool,
    )
    identity = {
        "backend": "dolt",
        "database": "beads",
        "project": "agentic",
    }
    suffix = hashlib.sha256(
        module._canonical_json(
            {
                "repository_identity": identity,
                "source_commit": baseline,
                "source_config_sha256": source_subject["source_config_sha256"],
                "definition_hash": config["tasks"][0]["definition_hash"],
            }
        )
    ).hexdigest()[:12]
    args = Namespace(
        config=str(config_path),
        confirmed=True,
        intent="01981f2c-6f40-7a2b-8f11-000000000001",
        issue=f"agentic-{suffix}",
        task=str(repo / module.TASKS[0][1]),
        runtime="codex",
        reviewed_commit=attestation,
    )
    return module, repo, state_file, deps, args, baseline, attestation


def test_closed_config_declares_executable_controller():
    module = load_controller()
    result = module.validate_config(
        REPOSITORY
        / "specs"
        / "mardi-gras-agentic-integration"
        / "bootstrap-registration-v1.json"
    )
    assert result["ok"] is True
    assert result["live_mutation_enabled"] is True
    assert result["attestation_state"] == "empty"


def test_actual_bd_11_context_shape_is_accepted():
    module = load_controller()
    context = {
        "backend": "dolt",
        "database": "beads",
        "project_id": "agentic",
        "repo_root": "/physical/repository",
        "dolt_mode": "local",
    }
    assert module.BootstrapController._repository_identity(context) == {
        "backend": "dolt",
        "database": "beads",
        "project": "agentic",
    }
    assert module.BootstrapController._issue_prefix(context) == "agentic"


def test_journal_recovers_one_next_event_and_cleans_only_dead_temps(tmp_path):
    module = load_controller()
    root = tmp_path / "journal"
    root.mkdir(mode=0o700)
    journal = module.EvidenceJournal(root, "01981f2c-6f40-7a2b-8f11-000000000001")
    journal.append("intent", "prepared", {"value": 1})
    sequence, previous = journal._head()
    event = {
        "schema_version": module.EVENT_SCHEMA,
        "owner": journal.owner,
        "writer": journal.process_owner,
        "sequence": sequence + 1,
        "previous": previous,
        "kind": "intent",
        "state": "committed",
        "payload": {"value": 2},
        "recorded_monotonic_ns": 1,
        "recorded_wall_utc": "2026-01-01T00:00:00.000000Z",
    }
    digest = hashlib.sha256(module._canonical_json(event)).hexdigest()
    module._write_atomic(
        journal.events / f"{sequence + 1:020d}-{digest}.json",
        event,
    )
    dead_owner = uuid.uuid4().hex
    module._write_immutable_direct(
        root / "owners" / f"process-{dead_owner}.json",
        {
            "schema_version": "agentic.registration-bootstrap-process-owner/v1",
            "process_owner": dead_owner,
            "intent": journal.owner,
            "pid": 999999,
            "process_start": "linux-procfs:1",
            "boot": module._boot_identity(),
        },
    )
    dead = root / f".head.json.{dead_owner}.999999.{uuid.uuid4().hex}.tmp"
    dead.write_text("dead")
    dead.chmod(0o600)
    recovered = module.EvidenceJournal(root, journal.owner)
    assert recovered._head() == (sequence + 1, digest)
    assert not dead.exists()


def test_journal_rejects_live_temporary_owner(tmp_path):
    module = load_controller()
    root = tmp_path / "journal"
    root.mkdir(mode=0o700)
    journal = module.EvidenceJournal(
        root,
        "01981f2c-6f40-7a2b-8f11-000000000001",
    )
    live = root / (
        f".head.json.{journal.process_owner}.{os.getpid()}."
        f"{uuid.uuid4().hex}.tmp"
    )
    live.write_text("live")
    live.chmod(0o600)
    with pytest.raises(module.BootstrapControlError) as caught:
        module.EvidenceJournal(root, journal.owner)
    assert caught.value.code == "live_temporary_owner"


@pytest.mark.parametrize("mode", ["malformed", "cross_intent"])
def test_journal_rejects_unowned_or_cross_intent_temporary(tmp_path, mode):
    module = load_controller()
    root = tmp_path / "journal"
    root.mkdir(mode=0o700)
    intent = "01981f2c-6f40-7a2b-8f11-000000000001"
    module.EvidenceJournal(root, intent)
    if mode == "malformed":
        temporary = root / ".malformed.tmp"
    else:
        process_owner = uuid.uuid4().hex
        module._write_immutable_direct(
            root / "owners" / f"process-{process_owner}.json",
            {
                "schema_version": "agentic.registration-bootstrap-process-owner/v1",
                "process_owner": process_owner,
                "intent": "01981f2c-6f40-7a2b-8f11-000000000099",
                "pid": 999999,
                "process_start": "linux-procfs:1",
                "boot": module._boot_identity(),
            },
        )
        temporary = root / (
            f".head.json.{process_owner}.999999.{uuid.uuid4().hex}.tmp"
        )
    temporary.write_text("temporary")
    temporary.chmod(0o600)
    with pytest.raises(module.BootstrapControlError):
        module.EvidenceJournal(root, intent)
    assert temporary.exists()


@pytest.mark.parametrize("mode", ["open_schema", "foreign_writer"])
def test_unique_next_event_gets_full_committed_validation(tmp_path, mode):
    module = load_controller()
    root = tmp_path / "journal"
    root.mkdir(mode=0o700)
    intent = "01981f2c-6f40-7a2b-8f11-000000000001"
    journal = module.EvidenceJournal(root, intent)
    journal.append("intent", "prepared", {"value": 1})
    sequence, previous = journal._head()
    writer = journal.process_owner
    if mode == "foreign_writer":
        writer = uuid.uuid4().hex
        module._write_immutable_direct(
            root / "owners" / f"process-{writer}.json",
            {
                "schema_version": "agentic.registration-bootstrap-process-owner/v1",
                "process_owner": writer,
                "intent": "01981f2c-6f40-7a2b-8f11-000000000099",
                "pid": 999999,
                "process_start": "linux-procfs:1",
                "boot": module._boot_identity(),
            },
        )
    event = {
        "schema_version": module.EVENT_SCHEMA,
        "owner": intent,
        "writer": writer,
        "sequence": sequence + 1,
        "previous": previous,
        "kind": "intent",
        "state": "committed",
        "payload": {"value": 2},
        "recorded_monotonic_ns": 1,
        "recorded_wall_utc": "2026-01-01T00:00:00.000000Z",
    }
    if mode == "open_schema":
        event["unknown"] = True
    digest = hashlib.sha256(module._canonical_json(event)).hexdigest()
    module._write_atomic(
        journal.events / f"{sequence + 1:020d}-{digest}.json",
        event,
    )
    with pytest.raises(module.BootstrapControlError):
        module.EvidenceJournal(root, intent)


def test_journal_rejects_symlinked_control_ancestor(tmp_path):
    module = load_controller()
    root = tmp_path / "journal"
    root.mkdir(mode=0o700)
    outside = tmp_path / "outside"
    outside.mkdir(mode=0o700)
    (root / "events").symlink_to(outside, target_is_directory=True)
    with pytest.raises(module.BootstrapControlError) as caught:
        module.EvidenceJournal(
            root,
            "01981f2c-6f40-7a2b-8f11-000000000001",
        )
    assert caught.value.code == "unsafe_state_path"


def test_descriptor_relative_write_does_not_follow_ancestor_swap(
    tmp_path,
    monkeypatch,
):
    module = load_controller()
    root = tmp_path / "journal"
    root.mkdir(mode=0o700)
    module.EvidenceJournal(
        root,
        "01981f2c-6f40-7a2b-8f11-000000000001",
    )
    victim = root / "receipts"
    module._secure_mkdir(victim)
    displaced = root / "displaced"
    outside = tmp_path / "outside"
    outside.mkdir(mode=0o700)
    real_open = module.os.open
    swapped = False

    def swap_then_open(path, flags, *args, **kwargs):
        nonlocal swapped
        if (
            not swapped
            and kwargs.get("dir_fd") is not None
            and isinstance(path, str)
            and path.startswith(".receipt.json.")
        ):
            victim.rename(displaced)
            victim.symlink_to(outside, target_is_directory=True)
            swapped = True
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(module.os, "open", swap_then_open)
    module._write_atomic(victim / "receipt.json", {"safe": True})
    assert swapped
    assert not (outside / "receipt.json").exists()
    assert json.loads((displaced / "receipt.json").read_text()) == {"safe": True}


def test_complete_fake_backed_bootstrap_is_serial_and_idempotent(tmp_path, monkeypatch):
    module, repo, state_file, deps, args, baseline, attestation = prepare_attested_repo(
        tmp_path, monkeypatch
    )
    result = module.run_00a(args, deps)
    assert result["ok"] is True
    assert set(result["issues"]) == {"00A", "00B", "00C", "00D"}
    state = json.loads(state_file.read_text())
    assert all(issue["status"] == "closed" for issue in state["issues"].values())
    assert state["profiles"] == ["core", "conditional", "full"]
    assert not list((deps.state_root / "bootstraps").rglob("worktrees/00?"))
    receipt_path = Path(result["receipt_path"])
    receipt_raw = receipt_path.read_bytes()
    assert stat.S_IMODE(receipt_path.stat().st_mode) == 0o600
    assert hashlib.sha256(receipt_raw).hexdigest() == result["receipt_sha256"]
    receipt = json.loads(receipt_raw)
    assert receipt_raw == module._canonical_json(receipt)
    assert set(receipt) == {
        "schema",
        "source_commit",
        "attestation_commit",
        "intent",
        "issues",
        "published_head",
        "event_chain",
        "provider",
    }
    assert receipt["schema"] == "agentic.registration-bootstrap-terminal-receipt/v1"
    assert set(receipt["intent"]) == {"id", "sha256"}
    assert set(receipt["issues"]) == {"00A", "00B", "00C", "00D"}
    assert set(receipt["event_chain"]) == {"head", "previous"}
    assert set(receipt["provider"]) == {
        "path",
        "sha256",
        "full_profile_identity",
    }
    assert set(receipt["provider"]["full_profile_identity"]) == {
        "backend_mode",
        "database_identity",
        "project_identity",
        "repository_identity",
        "core_schema_fingerprint",
        "full_schema_fingerprint",
    }
    assert run(["git", "merge-base", "--is-ancestor", attestation, "HEAD"], repo).returncode == 0
    first_head = result["published_head"]
    again = module.run_00a(args, deps)
    assert again["published_head"] == first_head
    assert again["receipt_sha256"] == result["receipt_sha256"]
    assert len(json.loads(state_file.read_text())["issues"]) == 4
    alternate_runtime = tmp_path / "other-runtime"
    shutil.copy2(deps.runtime, alternate_runtime)
    alternate_runtime.chmod(0o700)
    deps.runtime = alternate_runtime
    with pytest.raises(module.BootstrapControlError) as caught:
        module.run_00a(args, deps)
    assert caught.value.code == "intent_drift"


def test_claim_race_stops_before_worker_launch(tmp_path, monkeypatch):
    module, _repo, state_file, deps, args, *_ = prepare_attested_repo(
        tmp_path, monkeypatch
    )
    monkeypatch.setenv("FAKE_BOOTSTRAP_RACE", "1")
    with pytest.raises(module.BootstrapControlError) as caught:
        module.run_00a(args, deps)
    assert caught.value.code == "claim_lost"
    state = json.loads(state_file.read_text())
    issue = next(iter(state["issues"].values()))
    assert issue["assignee"] == "foreign-racer"
    assert not list((deps.state_root / "bootstraps").rglob("*-worker.json"))


@pytest.mark.parametrize("replacement", ["requeued", "foreign_claim"])
def test_committed_claim_is_reobserved_before_worker_launch(
    tmp_path,
    monkeypatch,
    replacement,
):
    module, _repo, state_file, deps, args, *_ = prepare_attested_repo(
        tmp_path,
        monkeypatch,
    )

    class StopAfterClaim:
        def __call__(self, point):
            if point == "00a_claim:after_commit":
                raise RuntimeError("stop after claim")

    deps.crash = StopAfterClaim()
    with pytest.raises(RuntimeError, match="stop after claim"):
        module.run_00a(args, deps)
    state = json.loads(state_file.read_text())
    issue = state["issues"][args.issue]
    if replacement == "requeued":
        issue["status"] = "open"
        issue["assignee"] = None
    else:
        issue["status"] = "in_progress"
        issue["assignee"] = "foreign-authorized-worker"
    issue["authority_revision"] = "r999"
    state_file.write_text(json.dumps(state, sort_keys=True, separators=(",", ":")))
    deps.crash = lambda _point: None
    with pytest.raises(module.BootstrapControlError) as caught:
        module.run_00a(args, deps)
    assert caught.value.code == "committed_stage_drift"
    assert not list((deps.state_root / "bootstraps").rglob("*-worker.json"))


@pytest.mark.parametrize("replacement", ["requeued", "foreign_claim"])
def test_post_publish_resume_rechecks_claim_before_provider_mutation(
    tmp_path,
    monkeypatch,
    replacement,
):
    module, _repo, state_file, deps, args, *_ = prepare_attested_repo(
        tmp_path,
        monkeypatch,
    )

    class StopAfterPublish:
        def __call__(self, point):
            if point == "00a_publish:after_commit":
                raise RuntimeError("stop after publish")

    deps.crash = StopAfterPublish()
    with pytest.raises(RuntimeError, match="stop after publish"):
        module.run_00a(args, deps)
    state = json.loads(state_file.read_text())
    issue = state["issues"][args.issue]
    if replacement == "requeued":
        issue["status"] = "open"
        issue["assignee"] = None
    else:
        issue["status"] = "in_progress"
        issue["assignee"] = "foreign-authorized-worker"
    issue["authority_revision"] = "r999"
    state_file.write_text(json.dumps(state, sort_keys=True, separators=(",", ":")))
    deps.crash = lambda _point: None
    with pytest.raises(module.BootstrapControlError) as caught:
        module.run_00a(args, deps)
    assert caught.value.code == "committed_stage_drift"
    calls = json.loads(state_file.read_text())["calls"]
    assert not [
        call
        for call in calls
        if tuple(call[:2])
        in {
            ("authority", "install"),
            ("authority", "bootstrap-finalize"),
            ("authority", "transaction"),
        }
    ]


def test_state_lock_rejects_symlinked_ancestor(tmp_path, monkeypatch):
    module, _repo, _state_file, deps, args, *_ = prepare_attested_repo(
        tmp_path,
        monkeypatch,
    )
    outside = tmp_path / "outside-locks"
    outside.mkdir(mode=0o700)
    (deps.state_root / "locks").symlink_to(outside, target_is_directory=True)
    with pytest.raises(module.BootstrapControlError) as caught:
        module.run_00a(args, deps)
    assert caught.value.code == "unsafe_state_path"
    assert not list(outside.iterdir())


@pytest.mark.parametrize(
    ("variable", "value", "expected_code"),
    [
        ("FAKE_BOOTSTRAP_BAD_RESPONSE", "identity_missing", "invalid_provider_response"),
        ("FAKE_BOOTSTRAP_BAD_RESPONSE", "install_foreign_actor", "invalid_provider_response"),
        ("FAKE_BOOTSTRAP_BAD_RESPONSE", "install_bad_after", "invalid_provider_response"),
        ("FAKE_BOOTSTRAP_BAD_RESPONSE", "install_bad_cursor", "invalid_provider_response"),
        ("FAKE_BOOTSTRAP_BAD_RESPONSE", "install_action_fork", "invalid_provider_response"),
        ("FAKE_BOOTSTRAP_BAD_RESPONSE", "mutation_bad_before", "invalid_provider_response"),
        ("FAKE_BOOTSTRAP_BAD_RESPONSE", "mutation_bad_cursor", "invalid_provider_response"),
        ("FAKE_BOOTSTRAP_BAD_RESPONSE", "mutation_action_fork", "invalid_provider_response"),
        ("FAKE_BOOTSTRAP_BAD_HISTORY", "missing", "issue_history_mismatch"),
        ("FAKE_BOOTSTRAP_BAD_HISTORY", "foreign", "issue_history_mismatch"),
        ("FAKE_BOOTSTRAP_BAD_EDGE", "1", "issue_edge_mismatch"),
        ("FAKE_BOOTSTRAP_BAD_CREATOR", "foreign", "issue_history_mismatch"),
        ("FAKE_BOOTSTRAP_BAD_TYPE", "1", "bootstrap_ref_conflict"),
    ],
)
def test_closed_provider_contract_rejects_missing_or_foreign_evidence(
    tmp_path,
    monkeypatch,
    variable,
    value,
    expected_code,
):
    module, _repo, _state_file, deps, args, *_ = prepare_attested_repo(
        tmp_path,
        monkeypatch,
    )
    monkeypatch.setenv(variable, value)
    with pytest.raises(module.BootstrapControlError) as caught:
        module.run_00a(args, deps)
    assert caught.value.code == expected_code


def test_crash_after_provider_close_recovers_exactly_once(tmp_path, monkeypatch):
    module, _repo, state_file, deps, args, *_ = prepare_attested_repo(
        tmp_path, monkeypatch
    )

    class CrashOnce:
        fired = False

        def __call__(self, point):
            if point == "00b_close:after_action" and not self.fired:
                self.fired = True
                raise RuntimeError("injected crash")

    deps.crash = CrashOnce()
    with pytest.raises(RuntimeError, match="injected crash"):
        module.run_00a(args, deps)
    deps.crash = lambda _point: None
    result = module.run_00a(args, deps)
    assert result["ok"] is True
    state = json.loads(state_file.read_text())
    assert len(state["issues"]) == 4
    assert all(issue["status"] == "closed" for issue in state["issues"].values())


@pytest.mark.parametrize("drift", ["history", "incident_edge"])
def test_terminal_proof_rejects_post_stage_tracker_drift(
    tmp_path,
    monkeypatch,
    drift,
):
    module, _repo, state_file, deps, args, *_ = prepare_attested_repo(
        tmp_path,
        monkeypatch,
    )

    class StopBeforeTerminal:
        def __call__(self, point):
            if point == "00d_close:after_commit":
                raise RuntimeError("stop before terminal")

    deps.crash = StopBeforeTerminal()
    with pytest.raises(RuntimeError, match="stop before terminal"):
        module.run_00a(args, deps)
    state = json.loads(state_file.read_text())
    final_issue = next(
        issue
        for issue in state["issues"].values()
        if str(issue.get("external_ref", "")).endswith(
            "00-install-beads-authorizer-bootstrap.md"
        )
    )
    if drift == "history":
        final_issue["history"].append(
            {"action": "comment", "actor": "concurrent-operator"}
        )
    else:
        state["issues"]["foreign-000000000001"] = {
            "id": "foreign-000000000001",
            "dependencies": [
                {
                    "depends_on": final_issue["id"],
                    "type": "blocks",
                }
            ],
        }
    state_file.write_text(json.dumps(state, sort_keys=True, separators=(",", ":")))
    deps.crash = lambda _point: None
    with pytest.raises(module.BootstrapControlError) as caught:
        module.run_00a(args, deps)
    assert caught.value.code == {
        "history": "committed_stage_drift",
        "incident_edge": "terminal_poststate_mismatch",
    }[drift]


@pytest.mark.parametrize(
    "barrier",
    ["terminal_snapshot:between_captures", "terminal:after_commit"],
)
def test_terminal_snapshot_barriers_reject_drift_before_receipt(
    tmp_path,
    monkeypatch,
    barrier,
):
    module, _repo, state_file, deps, args, *_ = prepare_attested_repo(
        tmp_path,
        monkeypatch,
    )

    class InjectIncidentEdge:
        fired = False

        def __call__(self, point):
            if point != barrier or self.fired:
                return
            self.fired = True
            state = json.loads(state_file.read_text())
            final_issue = next(
                issue
                for issue in state["issues"].values()
                if str(issue.get("external_ref", "")).endswith(
                    "00-install-beads-authorizer-bootstrap.md"
                )
            )
            state["issues"]["foreign-000000000001"] = {
                "id": "foreign-000000000001",
                "dependencies": [
                    {
                        "depends_on": final_issue["id"],
                        "type": "blocks",
                    }
                ],
            }
            state_file.write_text(
                json.dumps(state, sort_keys=True, separators=(",", ":"))
            )

    deps.crash = InjectIncidentEdge()
    with pytest.raises(module.BootstrapControlError) as caught:
        module.run_00a(args, deps)
    assert caught.value.code in {
        "terminal_poststate_mismatch",
        "terminal_snapshot_drift",
    }
    assert deps.crash.fired
    assert not list((deps.state_root / "bootstraps").rglob("receipts/*.json"))


def test_no_shell_or_unguarded_close_path_is_present():
    source = SCRIPT.read_text()
    assert "shell=True" not in source
    assert '[str(self.deps.bd), "close"' not in source
    assert "bootstrap_authority_unavailable" not in source
