package main

import (
	"fmt"
	"io"
	"os"

	"github.com/sticklane/agentprof/internal/output"
	"github.com/sticklane/agentprof/internal/schema"
)

// runFileAdapter is the shared tail of the gcp and vertex subcommands: it
// opens input, runs parse over it, reports skipped rows and errors, guards
// against an empty result, and writes the samples. name ("gcp" / "vertex")
// prefixes the diagnostic messages. otel deliberately does not use this
// helper (see specs/archive/adapter-file-runner/SPEC.md).
func runFileAdapter(
	name string,
	input string,
	parse func(io.Reader) ([]schema.Sample, int, error),
	out *string,
	stdout, stderr io.Writer,
) int {
	f, err := os.Open(input)
	if err != nil {
		fmt.Fprintf(stderr, "agentprof %s: %v\n", name, err)
		return 1
	}
	samples, skipped, err := parse(f)
	f.Close()
	if err != nil {
		fmt.Fprintf(stderr, "agentprof %s: reading %s: %v\n", name, input, err)
		return 1
	}

	if skipped > 0 {
		fmt.Fprintf(stderr, "skipped %d rows\n", skipped)
	}
	if len(samples) == 0 {
		fmt.Fprintf(stderr, "agentprof %s: no valid rows in input\n", name)
		return 1
	}
	if err := output.Write(samples, *out, stdout); err != nil {
		fmt.Fprintf(stderr, "agentprof %s: %v\n", name, err)
		return 1
	}
	return 0
}
