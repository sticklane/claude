package main

import (
	"flag"
	"fmt"
	"io"
	"strings"

	"github.com/sticklane/agentprof/internal/gcp"
	"github.com/sticklane/agentprof/internal/schema"
)

// cmdGCP emits canonical samples from a GCP billing export file (R9).
func cmdGCP(args []string, stdout, stderr io.Writer) int {
	fs := flag.NewFlagSet("gcp", flag.ContinueOnError)
	fs.SetOutput(stderr)
	out := fs.String("o", "", "output path: .pb.gz writes a pprof profile, anything else JSONL (default stdout)")
	frameLabels := fs.String("frame-labels", "", "comma-separated billing label keys to insert as frames after the project")
	inputs, ok := parsePositionals(fs, args)
	if !ok {
		return 2
	}
	if len(inputs) != 1 {
		fmt.Fprintln(stderr, "agentprof gcp: expected exactly one billing export file\nusage: agentprof gcp <billing.json> [-o out]")
		return 2
	}

	var keys []string
	for _, k := range strings.Split(*frameLabels, ",") {
		if k = strings.TrimSpace(k); k != "" {
			keys = append(keys, k)
		}
	}
	parse := func(r io.Reader) ([]schema.Sample, int, error) {
		return gcp.Parse(r, keys)
	}
	return runFileAdapter("gcp", inputs[0], parse, out, stdout, stderr)
}
