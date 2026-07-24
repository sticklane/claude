package main

import (
	"io"

	"github.com/sticklane/agentprof/internal/vertex"
)

// cmdVertex emits canonical samples from a Vertex AI request-response
// logging export file (vertex-logs-adapter SPEC R1).
func cmdVertex(args []string, stdout, stderr io.Writer) int {
	out, input, code, ok := singleFileCmd(
		"vertex", "logging export file", "agentprof vertex <logs.json> [-o out]",
		args, stderr, nil,
	)
	if !ok {
		return code
	}
	return runFileAdapter("vertex", input, vertex.Parse, out, stdout, stderr)
}
