// Package judge runs a single LLM grading call per invocation, mirroring
// internal/naming's Namer/CLINamer shape. A Judge grades a prompt with a named
// model tier and returns the model's verdict text; the CLI-backed
// implementation isolates each call under a scratch CLAUDE_CONFIG_DIR so
// grading never pollutes the profiled ~/.claude tree (R12).
package judge

// Judge grades a prompt with the given model tier, returning the model's
// response text.
type Judge interface {
	Judge(prompt, tier string) (string, error)
}
