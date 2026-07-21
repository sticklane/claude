package judge

import (
	"context"
	"strings"
	"testing"
)

func configDir(t *testing.T, cmdEnv []string) string {
	t.Helper()
	var dir string
	for _, e := range cmdEnv {
		if strings.HasPrefix(e, "CLAUDE_CONFIG_DIR=") {
			dir = strings.TrimPrefix(e, "CLAUDE_CONFIG_DIR=")
		}
	}
	if dir == "" {
		t.Fatalf("no CLAUDE_CONFIG_DIR in subprocess env: %v", cmdEnv)
	}
	return dir
}

func TestCLIJudgeCommandSetsScratchConfigDirAndFlags(t *testing.T) {
	root := t.TempDir()
	j := &CLIJudge{ScratchRoot: root}

	cmd, err := j.command(context.Background(), "grade this run", "haiku")
	if err != nil {
		t.Fatalf("command: %v", err)
	}

	dir := configDir(t, cmd.Env)
	if !strings.HasPrefix(dir, root) {
		t.Errorf("scratch CLAUDE_CONFIG_DIR %q not under root %q (R12 self-pollution guard)", dir, root)
	}
	for i, arg := range cmd.Args {
		if i > 0 && strings.HasPrefix(arg, "CLAUDE_CONFIG_DIR") {
			t.Errorf("config dir passed as argv, must be env: %v", cmd.Args)
		}
	}
	joined := strings.Join(cmd.Args, " ")
	for _, want := range []string{"-p", "--model haiku", "--output-format json"} {
		if !strings.Contains(joined, want) {
			t.Errorf("subprocess args %q lack %q", joined, want)
		}
	}
}

func TestCLIJudgeCommandUsesFreshScratchDirPerInvocation(t *testing.T) {
	root := t.TempDir()
	j := &CLIJudge{ScratchRoot: root}

	c1, err := j.command(context.Background(), "p", "haiku")
	if err != nil {
		t.Fatalf("command: %v", err)
	}
	c2, err := j.command(context.Background(), "p", "haiku")
	if err != nil {
		t.Fatalf("command: %v", err)
	}
	if d1, d2 := configDir(t, c1.Env), configDir(t, c2.Env); d1 == d2 {
		t.Errorf("two invocations shared scratch config dir %q, want fresh per invocation", d1)
	}
}

func TestFakeJudgeRecordsPromptAndTier(t *testing.T) {
	var j Judge = &Fake{Reply: "PASS"}
	got, err := j.Judge("is it good?", "opus")
	if err != nil {
		t.Fatalf("Judge: %v", err)
	}
	if got != "PASS" {
		t.Errorf("reply = %q, want PASS", got)
	}
	fake := j.(*Fake)
	if len(fake.Calls) != 1 {
		t.Fatalf("recorded %d calls, want 1", len(fake.Calls))
	}
	if fake.Calls[0].Prompt != "is it good?" || fake.Calls[0].Tier != "opus" {
		t.Errorf("recorded call = %+v, want {Prompt:is it good? Tier:opus}", fake.Calls[0])
	}
}
