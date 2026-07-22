package main

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/sticklane/agentprof/internal/judge"
)

// writeRawSkillMD writes verbatim SKILL.md content under
// <skillsDir>/<name>/SKILL.md (skillsDir is a `.claude/skills` directory).
func writeRawSkillMD(t *testing.T, skillsDir, name, content string) {
	t.Helper()
	dir := filepath.Join(skillsDir, name)
	if err := os.MkdirAll(dir, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, "SKILL.md"), []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
}

// writeTranscriptFile writes JSONL lines to <claudeDir>/projects/<proj>/<session>.jsonl.
func writeTranscriptFile(t *testing.T, claudeDir, proj, session string, lines []string) {
	t.Helper()
	dir := filepath.Join(claudeDir, "projects", proj)
	if err := os.MkdirAll(dir, 0o755); err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(dir, session+".jsonl")
	if err := os.WriteFile(path, []byte(strings.Join(lines, "\n")+"\n"), 0o644); err != nil {
		t.Fatal(err)
	}
}

// routingJudge answers trigger-judge and outcome-judge prompts differently,
// keyed by prompt content, so one fake can drive an end-to-end run that makes
// both kinds of judge call. Trigger prompts naming a MISFIREME skill return
// "misfired"; every other trigger prompt returns "correctly-triggered"; every
// outcome prompt returns "success".
type routingJudge struct {
	calls []judge.FakeCall
}

func (j *routingJudge) Judge(prompt, tier string) (string, error) {
	j.calls = append(j.calls, judge.FakeCall{Prompt: prompt, Tier: tier})
	if strings.Contains(prompt, "auto-triggered by the model") {
		if strings.Contains(prompt, "MISFIREME") {
			return "misfired", nil
		}
		return "correctly-triggered", nil
	}
	return "success", nil
}

func (j *routingJudge) outcomeCalls() []judge.FakeCall {
	var out []judge.FakeCall
	for _, c := range j.calls {
		if !strings.Contains(c.Prompt, "auto-triggered by the model") {
			out = append(out, c)
		}
	}
	return out
}

const goodSkillMD = `---
description: Does the good thing. Trigger phrase "frobnicate the widget".
outcome-rubric: |
  Success requires a verifier PASS or a merged commit visible in the transcript.
---

Body.
`

const badSkillMD = `---
description: MISFIREME handles unrelated things.
---

Body.
`

// e2eTranscript exercises all five per-invocation populations:
//   - goodskill: model-auto-triggered (resolvable, custom rubric) -> correct -> success
//   - badskill:  model-auto-triggered (resolvable, MISFIREME desc) -> misfired
//   - ghostskill: model-auto-triggered, unresolvable
//   - goodskill again: a self-chain (no intervening user turn)
//   - build: opened by a <command-name> tag -> explicit_invocation
func e2eTranscript() []string {
	return []string{
		`{"type":"user","timestamp":"2026-07-10T09:00:00Z","cwd":"/x/app","message":{"role":"user","content":"please do the good thing"}}`,
		`{"type":"assistant","timestamp":"2026-07-10T09:00:01Z","cwd":"/x/app","message":{"id":"m1","model":"claude-fable-5","content":[{"type":"tool_use","id":"tg","name":"Skill","input":{"skill":"goodskill"}}]}}`,
		`{"type":"user","timestamp":"2026-07-10T09:00:02Z","cwd":"/x/app","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"tg","content":"good done; verifier PASS"}]}}`,
		`{"type":"user","timestamp":"2026-07-10T09:00:03Z","cwd":"/x/app","message":{"role":"user","content":"now handle the unrelated thing"}}`,
		`{"type":"assistant","timestamp":"2026-07-10T09:00:04Z","cwd":"/x/app","message":{"id":"m2","model":"claude-fable-5","content":[{"type":"tool_use","id":"tb","name":"Skill","input":{"skill":"badskill"}}]}}`,
		`{"type":"user","timestamp":"2026-07-10T09:00:05Z","cwd":"/x/app","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"tb","content":"bad result"}]}}`,
		`{"type":"user","timestamp":"2026-07-10T09:00:06Z","cwd":"/x/app","message":{"role":"user","content":"please summon the ghost"}}`,
		`{"type":"assistant","timestamp":"2026-07-10T09:00:07Z","cwd":"/x/app","message":{"id":"m3","model":"claude-fable-5","content":[{"type":"tool_use","id":"th","name":"Skill","input":{"skill":"ghostskill"}}]}}`,
		`{"type":"user","timestamp":"2026-07-10T09:00:08Z","cwd":"/x/app","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"th","content":"ghost result"}]}}`,
		`{"type":"assistant","timestamp":"2026-07-10T09:00:09Z","cwd":"/x/app","message":{"id":"m4","model":"claude-fable-5","content":[{"type":"tool_use","id":"ts","name":"Skill","input":{"skill":"goodskill"}}]}}`,
		`{"type":"user","timestamp":"2026-07-10T09:00:10Z","cwd":"/x/app","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"ts","content":"chained good"}]}}`,
		`{"type":"user","timestamp":"2026-07-10T09:00:11Z","cwd":"/x/app","message":{"role":"user","content":"<command-name>build</command-name><command-args>specs/x</command-args>"}}`,
		`{"type":"assistant","timestamp":"2026-07-10T09:00:12Z","cwd":"/x/app","message":{"id":"m5","model":"claude-fable-5","content":[{"type":"tool_use","id":"te","name":"Skill","input":{"skill":"build","args":"specs/x"}}]}}`,
		`{"type":"user","timestamp":"2026-07-10T09:00:13Z","cwd":"/x/app","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"te","content":"built"}]}}`,
	}
}

// e2eFixture builds a claudeDir + a Resolver cwd with goodskill/badskill
// installed (ghostskill deliberately absent), returning both plus a cutoff.
func e2eFixture(t *testing.T) (claudeDir string, r Resolver, cutoff time.Time) {
	t.Helper()
	claudeDir = t.TempDir()
	writeTranscriptFile(t, claudeDir, "proj", "sess-e2e", e2eTranscript())

	cwd := t.TempDir()
	skills := filepath.Join(cwd, ".claude", "skills")
	writeRawSkillMD(t, skills, "goodskill", goodSkillMD)
	writeRawSkillMD(t, skills, "badskill", badSkillMD)

	return claudeDir, Resolver{Cwd: cwd, PluginCacheRoot: t.TempDir()}, time.Now().AddDate(0, 0, -30)
}

func reportFor(reports []skillReport, skill string) *skillReport {
	for i := range reports {
		if reports[i].Skill == skill {
			return &reports[i]
		}
	}
	return nil
}

func TestSkillcheckEndToEndCategoryCounts(t *testing.T) {
	claudeDir, r, cutoff := e2eFixture(t)
	j := &routingJudge{}

	reports, err := runSkillcheck(claudeDir, cutoff, "", "haiku", r, j)
	if err != nil {
		t.Fatalf("runSkillcheck: %v", err)
	}

	good := reportFor(reports, "goodskill")
	if good == nil {
		t.Fatalf("no report for goodskill; got %+v", reports)
	}
	if good.Invocations != 2 {
		t.Errorf("goodskill invocations = %d, want 2", good.Invocations)
	}
	if good.Trigger.Correct != 1 || good.Trigger.SelfChained != 1 {
		t.Errorf("goodskill trigger = %+v, want correct=1 self_chained=1", good.Trigger)
	}
	if good.Outcome.Success != 1 {
		t.Errorf("goodskill outcome = %+v, want success=1", good.Outcome)
	}

	bad := reportFor(reports, "badskill")
	if bad == nil || bad.Trigger.Misfired != 1 {
		t.Fatalf("badskill report = %+v, want misfired=1", bad)
	}
	ghost := reportFor(reports, "ghostskill")
	if ghost == nil || ghost.Trigger.Unresolvable != 1 {
		t.Fatalf("ghostskill report = %+v, want unresolvable=1", ghost)
	}
	build := reportFor(reports, "build")
	if build == nil || build.Trigger.ExplicitInvocation != 1 {
		t.Fatalf("build report = %+v, want explicit_invocation=1", build)
	}
}

func TestSkillcheckMisfiredAndUnresolvableNeverReachOutcomeScoring(t *testing.T) {
	claudeDir, r, cutoff := e2eFixture(t)
	j := &routingJudge{}

	if _, err := runSkillcheck(claudeDir, cutoff, "", "haiku", r, j); err != nil {
		t.Fatalf("runSkillcheck: %v", err)
	}

	oc := j.outcomeCalls()
	// Exactly one correctly-triggered invocation (goodskill/tg) is outcome-scored.
	if len(oc) != 1 {
		t.Fatalf("outcome judge calls = %d, want exactly 1 (only the correctly-triggered invocation)", len(oc))
	}
	for _, c := range oc {
		if strings.Contains(c.Prompt, "Skill invoked: badskill") {
			t.Error("a misfired invocation reached outcome scoring")
		}
		if strings.Contains(c.Prompt, "Skill invoked: ghostskill") {
			t.Error("an unresolvable invocation reached outcome scoring")
		}
	}
}

func TestSkillcheckFindingsCarryEvidenceAndTranscriptRef(t *testing.T) {
	claudeDir, r, cutoff := e2eFixture(t)
	j := &routingJudge{}

	reports, err := runSkillcheck(claudeDir, cutoff, "", "haiku", r, j)
	if err != nil {
		t.Fatalf("runSkillcheck: %v", err)
	}

	bad := reportFor(reports, "badskill")
	if bad == nil || len(bad.Findings) != 1 {
		t.Fatalf("badskill findings = %+v, want exactly 1", bad)
	}
	f := bad.Findings[0]
	if f.Verdict != "misfired" {
		t.Errorf("finding verdict = %q, want misfired", f.Verdict)
	}
	if strings.TrimSpace(f.Evidence) == "" {
		t.Error("finding evidence is empty")
	}
	if f.Session != "sess-e2e" {
		t.Errorf("finding session = %q, want sess-e2e", f.Session)
	}
	if !strings.Contains(f.TranscriptRef, "sess-e2e.jsonl") {
		t.Errorf("finding transcript_ref = %q, want it to point at the transcript file", f.TranscriptRef)
	}

	// A correctly-triggered + success invocation produces no finding.
	good := reportFor(reports, "goodskill")
	for _, fn := range good.Findings {
		if fn.Verdict == "success" || fn.Verdict == "correct" {
			t.Errorf("goodskill has a finding for an obvious verdict: %+v", fn)
		}
	}
}

func TestSkillcheckPossibleMissDetected(t *testing.T) {
	claudeDir := t.TempDir()
	// A user turn that names an installed skill's trigger phrase but never invokes it.
	lines := []string{
		`{"type":"user","timestamp":"2026-07-10T09:00:00Z","cwd":"/x/app","message":{"role":"user","content":"can you frobnicate the widget for me"}}`,
		`{"type":"assistant","timestamp":"2026-07-10T09:00:01Z","cwd":"/x/app","message":{"id":"m1","model":"claude-fable-5","content":[{"type":"text","text":"sure"}]}}`,
	}
	writeTranscriptFile(t, claudeDir, "proj", "sess-miss", lines)

	cwd := t.TempDir()
	writeRawSkillMD(t, filepath.Join(cwd, ".claude", "skills"), "goodskill", goodSkillMD)
	r := Resolver{Cwd: cwd, PluginCacheRoot: t.TempDir()}

	reports, err := runSkillcheck(claudeDir, time.Now().AddDate(0, 0, -30), "", "haiku", r, &routingJudge{})
	if err != nil {
		t.Fatalf("runSkillcheck: %v", err)
	}
	good := reportFor(reports, "goodskill")
	if good == nil || good.Trigger.PossibleMisses < 1 {
		t.Fatalf("goodskill possible_misses = %+v, want >= 1", good)
	}
}

func TestSkillcheckSkillFilterNarrowsToOneSkill(t *testing.T) {
	claudeDir, r, cutoff := e2eFixture(t)
	reports, err := runSkillcheck(claudeDir, cutoff, "badskill", "haiku", r, &routingJudge{})
	if err != nil {
		t.Fatalf("runSkillcheck: %v", err)
	}
	if len(reports) != 1 || reports[0].Skill != "badskill" {
		t.Fatalf("filtered reports = %+v, want only badskill", reports)
	}
}

func TestSkillcheckJSONReportShapeHasCategorySet(t *testing.T) {
	claudeDir, r, cutoff := e2eFixture(t)
	reports, err := runSkillcheck(claudeDir, cutoff, "", "haiku", r, &routingJudge{})
	if err != nil {
		t.Fatalf("runSkillcheck: %v", err)
	}
	raw, err := renderReportsJSON(reports)
	if err != nil {
		t.Fatalf("renderReportsJSON: %v", err)
	}
	var parsed []map[string]json.RawMessage
	if err := json.Unmarshal(raw, &parsed); err != nil {
		t.Fatalf("report JSON did not parse as an array of objects: %v\n%s", err, raw)
	}
	if len(parsed) == 0 {
		t.Fatal("report JSON is empty")
	}
	obj := parsed[0]
	for _, key := range []string{"skill", "invocations", "trigger", "outcome", "findings"} {
		if _, ok := obj[key]; !ok {
			t.Errorf("report object missing key %q", key)
		}
	}
	var trig map[string]int
	if err := json.Unmarshal(obj["trigger"], &trig); err != nil {
		t.Fatalf("trigger did not parse: %v", err)
	}
	for _, key := range []string{"correct", "misfired", "unresolvable", "explicit_invocation", "self_chained", "possible_misses"} {
		if _, ok := trig[key]; !ok {
			t.Errorf("trigger aggregate missing category %q", key)
		}
	}
	var out map[string]int
	if err := json.Unmarshal(obj["outcome"], &out); err != nil {
		t.Fatalf("outcome did not parse: %v", err)
	}
	for _, key := range []string{"success", "failure", "unknown"} {
		if _, ok := out[key]; !ok {
			t.Errorf("outcome aggregate missing category %q", key)
		}
	}
}

func TestSkillcheckTableFormatRendersParseableCounts(t *testing.T) {
	claudeDir, r, cutoff := e2eFixture(t)
	reports, err := runSkillcheck(claudeDir, cutoff, "", "haiku", r, &routingJudge{})
	if err != nil {
		t.Fatalf("runSkillcheck: %v", err)
	}
	table := renderReportsTable(reports)

	// Parse the table: locate the header, map column name -> index, then read
	// the goodskill row's cells by column (parse-then-assert, not substring).
	lines := strings.Split(strings.TrimSpace(table), "\n")
	if len(lines) < 2 {
		t.Fatalf("table has too few lines:\n%s", table)
	}
	cols := map[string]int{}
	for i, name := range strings.Fields(lines[0]) {
		cols[strings.ToLower(name)] = i
	}
	for _, need := range []string{"skill", "invocations", "correct", "misfired", "unresolvable", "self_chained", "success"} {
		if _, ok := cols[need]; !ok {
			t.Fatalf("table header missing column %q:\n%s", need, lines[0])
		}
	}
	var goodRow []string
	for _, line := range lines[1:] {
		fields := strings.Fields(line)
		if len(fields) > cols["skill"] && fields[cols["skill"]] == "goodskill" {
			goodRow = fields
		}
	}
	if goodRow == nil {
		t.Fatalf("no goodskill row in table:\n%s", table)
	}
	if goodRow[cols["invocations"]] != "2" {
		t.Errorf("goodskill invocations cell = %q, want 2", goodRow[cols["invocations"]])
	}
	if goodRow[cols["correct"]] != "1" {
		t.Errorf("goodskill correct cell = %q, want 1", goodRow[cols["correct"]])
	}
	if goodRow[cols["self_chained"]] != "1" {
		t.Errorf("goodskill self_chained cell = %q, want 1", goodRow[cols["self_chained"]])
	}
	if goodRow[cols["success"]] != "1" {
		t.Errorf("goodskill success cell = %q, want 1", goodRow[cols["success"]])
	}
}

func TestSkillcheckJudgeTierSessionIsRejected(t *testing.T) {
	if _, err := resolveJudgeTierToModel("session"); err == nil {
		t.Error("resolveJudgeTierToModel(session) returned no error; a fresh subprocess has no model to inherit")
	}
	// The CLI surface rejects it rather than silently defaulting to scout.
	var stdout, stderr bytes.Buffer
	code := cmdSkillcheck([]string{"--judge-tier", "session"}, &stdout, &stderr)
	if code == 0 {
		t.Errorf("skillcheck --judge-tier session exit = %d, want non-zero", code)
	}
	if !strings.Contains(strings.ToLower(stderr.String()), "session") {
		t.Errorf("stderr = %q, want it to explain the session tier rejection", stderr.String())
	}
}

func TestSkillcheckJudgeTierResolvesConcreteModels(t *testing.T) {
	cases := map[string]string{"scout": "haiku", "deep": "opus", "frontier": "fable"}
	for tier, want := range cases {
		got, err := resolveJudgeTierToModel(tier)
		if err != nil {
			t.Errorf("resolveJudgeTierToModel(%q) errored: %v", tier, err)
			continue
		}
		if got != want {
			t.Errorf("resolveJudgeTierToModel(%q) = %q, want %q", tier, got, want)
		}
	}
}

func TestSkillcheckHelpDocumentsEveryFlag(t *testing.T) {
	var stdout, stderr bytes.Buffer
	cmdSkillcheck([]string{"--help"}, &stdout, &stderr)
	help := stdout.String() + stderr.String()
	for _, flag := range []string{"--days", "--since", "--skill", "--judge-tier", "-o", "--format"} {
		if !strings.Contains(help, flag) {
			t.Errorf("--help output does not document %q:\n%s", flag, help)
		}
	}
}

func TestSkillcheckWiresScratchIsolatedCLIJudge(t *testing.T) {
	// The judge skillcheck runs with must be the CLI-backed judge configured
	// with a scratch ScratchRoot, so grading never writes into the profiled
	// ~/.claude tree. The CLAUDE_CONFIG_DIR-in-env proof lives in
	// internal/judge/cli_test.go; this asserts the wiring feeds that mechanism
	// a scratch root (proving the wiring, not just the package).
	scratch := t.TempDir()
	j := newSkillcheckJudge(scratch)
	if j.ScratchRoot != scratch {
		t.Fatalf("skillcheck judge ScratchRoot = %q, want the scratch dir %q", j.ScratchRoot, scratch)
	}

	// The actual invocation path (cmdSkillcheck) feeds newSkillcheckJudge the
	// default scratch root, which must be a real scratch location outside the
	// profiled ~/.claude tree — since CLIJudge derives CLAUDE_CONFIG_DIR as
	// <ScratchRoot>/judge-*, a scratch ScratchRoot guarantees the grading
	// subprocess's CLAUDE_CONFIG_DIR lands under scratch (env proof:
	// internal/judge/cli_test.go).
	def := defaultJudgeScratchRoot()
	if def == "" {
		t.Fatal("skillcheck's default judge ScratchRoot is empty; grading would pollute the profiled ~/.claude tree")
	}
	if !strings.HasPrefix(def, os.TempDir()) {
		t.Errorf("default judge ScratchRoot %q is not under the OS temp dir %q", def, os.TempDir())
	}
	if strings.Contains(def, filepath.Join(".claude", "projects")) {
		t.Errorf("default judge ScratchRoot %q is inside the profiled ~/.claude/projects tree", def)
	}
}
