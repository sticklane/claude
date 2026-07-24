package main

import (
	"flag"
	"io"
	"strings"

	"github.com/sticklane/agentprof/internal/gcp"
	"github.com/sticklane/agentprof/internal/schema"
)

// cmdGCP emits canonical samples from a GCP billing export file (R9).
func cmdGCP(args []string, stdout, stderr io.Writer) int {
	var frameLabels *string
	out, input, code, ok := singleFileCmd(
		"gcp", "billing export file", "agentprof gcp <billing.json> [-o out]",
		args, stderr,
		func(fs *flag.FlagSet) {
			frameLabels = fs.String("frame-labels", "", "comma-separated billing label keys to insert as frames after the project")
		},
	)
	if !ok {
		return code
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
	return runFileAdapter("gcp", input, parse, out, stdout, stderr)
}
