package claude

import (
	"os"
	"strings"
)

// Frontmatter is the subset of a SKILL.md's YAML frontmatter the skill audit
// reads. Optional fields are zero-valued when absent.
type Frontmatter struct {
	// Description is the skill's `description:` field.
	Description string
	// OutcomeRubric is the skill's `outcome-rubric:` field (often a block
	// scalar), "" when absent.
	OutcomeRubric string
	// DisableModelInvocation is the skill's `disable-model-invocation:` flag.
	DisableModelInvocation bool
}

// SkillFrontmatter parses the three audited fields from a SKILL.md's leading
// `---`-delimited frontmatter. It intentionally hand-parses only the top-level
// keys it needs (description, outcome-rubric, disable-model-invocation) rather
// than pulling in a YAML dependency; a file with no frontmatter yields a zero
// Frontmatter and no error.
func SkillFrontmatter(path string) (Frontmatter, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return Frontmatter{}, err
	}
	fields := frontmatterFields(string(data))
	return Frontmatter{
		Description:            fields["description"],
		OutcomeRubric:          fields["outcome-rubric"],
		DisableModelInvocation: strings.EqualFold(strings.TrimSpace(fields["disable-model-invocation"]), "true"),
	}, nil
}

// frontmatterFields returns the top-level `key: value` pairs of the leading
// `---`-delimited frontmatter block. A key whose inline value is empty or a
// block-scalar indicator (|, |-, >, >-) takes the following more-indented lines
// as a dedented multi-line value.
func frontmatterFields(content string) map[string]string {
	fields := map[string]string{}
	lines := strings.Split(content, "\n")

	i := 0
	for i < len(lines) && strings.TrimSpace(lines[i]) == "" {
		i++
	}
	if i >= len(lines) || strings.TrimSpace(lines[i]) != "---" {
		return fields
	}
	i++ // past the opening ---

	for i < len(lines) {
		line := lines[i]
		if strings.TrimSpace(line) == "---" {
			break
		}
		if !isTopLevelKey(line) {
			i++
			continue
		}
		key, val, _ := strings.Cut(line, ":")
		key = strings.TrimSpace(key)
		val = strings.TrimSpace(val)
		if isBlockScalarIndicator(val) {
			var block []string
			i++
			for i < len(lines) {
				next := lines[i]
				if strings.TrimSpace(next) == "---" || isTopLevelKey(next) {
					break
				}
				block = append(block, strings.TrimSpace(next))
				i++
			}
			fields[key] = strings.TrimSpace(strings.Join(block, "\n"))
			continue
		}
		fields[key] = unquote(val)
		i++
	}
	return fields
}

// isTopLevelKey reports whether a line begins a top-level mapping key (no
// leading indentation, and a colon present).
func isTopLevelKey(line string) bool {
	if line == "" || line[0] == ' ' || line[0] == '\t' {
		return false
	}
	return strings.Contains(line, ":")
}

func isBlockScalarIndicator(val string) bool {
	switch val {
	case "", "|", "|-", "|+", ">", ">-", ">+":
		return true
	}
	return false
}

// unquote strips a single matching pair of surrounding single or double quotes.
func unquote(s string) string {
	if len(s) >= 2 {
		if (s[0] == '"' && s[len(s)-1] == '"') || (s[0] == '\'' && s[len(s)-1] == '\'') {
			return s[1 : len(s)-1]
		}
	}
	return s
}
