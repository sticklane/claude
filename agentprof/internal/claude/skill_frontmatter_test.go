package claude_test

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/sticklane/agentprof/internal/claude"
)

// writeSkill writes a SKILL.md with the given content and returns its path.
func writeSkill(t *testing.T, content string) string {
	t.Helper()
	path := filepath.Join(t.TempDir(), "SKILL.md")
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
	return path
}

func TestSkillFrontmatterReadsDescription(t *testing.T) {
	path := writeSkill(t, `---
name: build
description: Executes one task file end to end. Trigger - "/build".
---

# body
`)
	fm, err := claude.SkillFrontmatter(path)
	if err != nil {
		t.Fatalf("SkillFrontmatter: %v", err)
	}
	if fm.Description != `Executes one task file end to end. Trigger - "/build".` {
		t.Errorf("Description = %q", fm.Description)
	}
	if fm.OutcomeRubric != "" {
		t.Errorf("OutcomeRubric = %q, want empty", fm.OutcomeRubric)
	}
	if fm.DisableModelInvocation {
		t.Error("DisableModelInvocation = true, want false")
	}
}

func TestSkillFrontmatterReadsOutcomeRubricBlockScalar(t *testing.T) {
	path := writeSkill(t, `---
name: grader
description: Grades a run.
outcome-rubric: |
  The run must:
  - produce a report
  - cite evidence
---

# body
`)
	fm, err := claude.SkillFrontmatter(path)
	if err != nil {
		t.Fatalf("SkillFrontmatter: %v", err)
	}
	if !strings.Contains(fm.OutcomeRubric, "produce a report") ||
		!strings.Contains(fm.OutcomeRubric, "cite evidence") {
		t.Errorf("OutcomeRubric = %q, want the block-scalar lines", fm.OutcomeRubric)
	}
	if fm.Description != "Grades a run." {
		t.Errorf("Description = %q, want %q", fm.Description, "Grades a run.")
	}
}

func TestSkillFrontmatterReadsDisableModelInvocation(t *testing.T) {
	path := writeSkill(t, `---
name: evals
description: Paid headless eval runner.
disable-model-invocation: true
---

# body
`)
	fm, err := claude.SkillFrontmatter(path)
	if err != nil {
		t.Fatalf("SkillFrontmatter: %v", err)
	}
	if !fm.DisableModelInvocation {
		t.Error("DisableModelInvocation = false, want true")
	}
}

func TestSkillFrontmatterMinimalHasNoOptionalFields(t *testing.T) {
	path := writeSkill(t, `---
name: bare
---

# body
`)
	fm, err := claude.SkillFrontmatter(path)
	if err != nil {
		t.Fatalf("SkillFrontmatter: %v", err)
	}
	if fm.Description != "" {
		t.Errorf("Description = %q, want empty", fm.Description)
	}
	if fm.OutcomeRubric != "" {
		t.Errorf("OutcomeRubric = %q, want empty", fm.OutcomeRubric)
	}
	if fm.DisableModelInvocation {
		t.Error("DisableModelInvocation = true, want false")
	}
}
