package main

import (
	"flag"
	"fmt"
	"io"

	"github.com/sticklane/agentprof/internal/vertex"
)

// cmdVertex emits canonical samples from a Vertex AI request-response
// logging export file (vertex-logs-adapter SPEC R1).
func cmdVertex(args []string, stdout, stderr io.Writer) int {
	fs := flag.NewFlagSet("vertex", flag.ContinueOnError)
	fs.SetOutput(stderr)
	out := fs.String("o", "", "output path: .pb.gz writes a pprof profile, anything else JSONL (default stdout)")
	inputs, ok := parsePositionals(fs, args)
	if !ok {
		return 2
	}
	if len(inputs) != 1 {
		fmt.Fprintln(stderr, "agentprof vertex: expected exactly one logging export file\nusage: agentprof vertex <logs.json> [-o out]")
		return 2
	}

	return runFileAdapter("vertex", inputs[0], vertex.Parse, out, stdout, stderr)
}
