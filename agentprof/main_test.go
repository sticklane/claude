package main

import (
	"bytes"
	"strings"
	"testing"
)

func TestRunVersionPrintsVersionAndExitsZero(t *testing.T) {
	var stdout, stderr bytes.Buffer
	code := run([]string{"--version"}, &stdout, &stderr)
	if code != 0 {
		t.Errorf("exit code = %d, want 0", code)
	}
	if !strings.Contains(stdout.String(), version) {
		t.Errorf("stdout = %q, want it to contain version %q", stdout.String(), version)
	}
}

func TestRunUnknownSubcommandPrintsUsageAndExitsTwo(t *testing.T) {
	var stdout, stderr bytes.Buffer
	code := run([]string{"bogus"}, &stdout, &stderr)
	if code != 2 {
		t.Errorf("exit code = %d, want 2", code)
	}
	if !strings.Contains(stderr.String(), "usage") && !strings.Contains(stderr.String(), "Usage") {
		t.Errorf("stderr = %q, want usage text", stderr.String())
	}
}

func TestRunMissingSubcommandPrintsUsageAndExitsTwo(t *testing.T) {
	var stdout, stderr bytes.Buffer
	code := run(nil, &stdout, &stderr)
	if code != 2 {
		t.Errorf("exit code = %d, want 2", code)
	}
	if !strings.Contains(stderr.String(), "usage") && !strings.Contains(stderr.String(), "Usage") {
		t.Errorf("stderr = %q, want usage text", stderr.String())
	}
}
