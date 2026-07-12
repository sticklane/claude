package antigravity

import (
	"database/sql"
	"fmt"
	"os"
	"path"
	"path/filepath"
	"strings"
	"time"

	"github.com/sticklane/agentprof/internal/pricing"
	"github.com/sticklane/agentprof/internal/schema"

	_ "modernc.org/sqlite" // pure-Go SQLite driver (no cgo), registers "sqlite"
)

// genField is the gen_metadata `data` blob's top-level wrapper field whose
// submessage carries the generation's fields the SPEC enumerates. Confirmed
// against the committed fixture (testdata/README.md): the display string
// (21), token submessage (4), Timestamp (9.4), and {key,value} map (20) all
// live one level down at 1->N, not at the blob root — the SPEC's field
// numbers are relative to this generation submessage, not the raw blob.
const genField = 1

// Collect globs <dir>/conversations/*.db, opens each SQLite file read-only,
// joins steps (step_type=15) to gen_metadata on idx, and returns one
// schema.Sample per joined row whose generation time is not before cutoff.
// The second return value counts skipped rows: locked/corrupt db files, or
// blobs the field-walker can't parse. The error is non-nil only for a
// glob-pattern failure; a bad db file is skipped, never fatal.
func Collect(dir string, cutoff time.Time) ([]schema.Sample, int, error) {
	files, err := filepath.Glob(filepath.Join(dir, "conversations", "*.db"))
	if err != nil {
		return nil, 0, err
	}
	var samples []schema.Sample
	skipped := 0
	for _, dbPath := range files {
		s, sk := collectFile(dbPath, cutoff)
		samples = append(samples, s...)
		skipped += sk
	}
	return samples, skipped, nil
}

// collectFile opens one db read-only (retrying once on a lock from an active
// -wal/-shm pair) and returns its in-window samples plus a skipped count.
func collectFile(dbPath string, cutoff time.Time) ([]schema.Sample, int) {
	db, err := openReadOnly(dbPath)
	if err != nil {
		// A locked db (live Antigravity session mid-write) may clear on a
		// second attempt; skip with a stderr note if it doesn't.
		db, err = openReadOnly(dbPath)
		if err != nil {
			fmt.Fprintf(os.Stderr, "antigravity: skipping %s: %v\n", filepath.Base(dbPath), err)
			return nil, 1
		}
	}
	defer db.Close()

	dbFile := filepath.Base(dbPath)
	cascadeID := strings.TrimSuffix(dbFile, ".db")
	project := projectFromDB(db)

	// gen_metadata.idx is a 0-based generation ordinal, NOT the steps.idx
	// position: the committed fixture's sole generation is steps.idx=2
	// (step_type=15) but its gen_metadata row is idx=0. So the k-th
	// step_type=15 step (ordered by steps.idx) joins to gen_metadata.idx=k —
	// a positional join, not the idx-equality the SPEC assumed (disproven by
	// the fixture; see testdata/README.md). Count(gen_metadata) equals
	// count(step_type=15) by construction, so this emits one sample per
	// generation.
	rows, err := db.Query(`SELECT g.data FROM ` +
		`(SELECT idx, ROW_NUMBER() OVER (ORDER BY idx) - 1 AS gen_ord ` +
		`FROM steps WHERE step_type = 15) s ` +
		`JOIN gen_metadata g ON g.idx = s.gen_ord ORDER BY s.idx`)
	if err != nil {
		fmt.Fprintf(os.Stderr, "antigravity: skipping %s: %v\n", dbFile, err)
		return nil, 1
	}
	defer rows.Close()

	var samples []schema.Sample
	skipped := 0
	for rows.Next() {
		var blob []byte
		if err := rows.Scan(&blob); err != nil {
			skipped++
			continue
		}
		sample, ok := buildSample(blob, project, cascadeID, dbFile)
		if !ok {
			skipped++
			continue
		}
		if sample.Time.Before(cutoff) {
			continue // out of window: an ordinary filter, not a skip
		}
		samples = append(samples, sample)
	}
	if err := rows.Err(); err != nil {
		// A corruption surfaced only mid-iteration counts as a skipped file.
		fmt.Fprintf(os.Stderr, "antigravity: skipping %s: %v\n", dbFile, err)
		skipped++
	}
	return samples, skipped
}

// openReadOnly opens dbPath read-only and verifies the connection.
func openReadOnly(dbPath string) (*sql.DB, error) {
	db, err := sql.Open("sqlite", fmt.Sprintf("file:%s?mode=ro", dbPath))
	if err != nil {
		return nil, err
	}
	if err := db.Ping(); err != nil {
		db.Close()
		return nil, err
	}
	return db, nil
}

// buildSample decodes one gen_metadata blob into a schema.Sample. It returns
// ok=false (a skip) if the blob's wrapper, Timestamp, or model display string
// can't be parsed.
func buildSample(blob []byte, project, cascadeID, dbFile string) (schema.Sample, bool) {
	gen, ok := ReadField(blob, genField)
	if !ok || gen.WireType != 2 {
		return schema.Sample{}, false
	}
	g := gen.Bytes

	// Time: 3->9->4 is a protobuf Timestamp {1: seconds, 2: nanos}.
	secF, ok := ReadPath(g, 9, 4, 1)
	if !ok {
		return schema.Sample{}, false
	}
	var nanos int64
	if nanoF, ok := ReadPath(g, 9, 4, 2); ok {
		nanos = int64(nanoF.Varint)
	}
	t := time.Unix(int64(secF.Varint), nanos).UTC()

	// Model display string: 3->21 (the raw field passed as-is to PriceGemini).
	modelF, ok := ReadField(g, 21)
	if !ok || modelF.WireType != 2 {
		return schema.Sample{}, false
	}
	model := string(modelF.Bytes)

	// Token counts: 3->4 submessage. The fixture README justifies sub-field 2
	// as input tokens and sub-field 3 as output tokens by magnitude; sub-fields
	// 6/9/10 are unidentified, so no cache_read_tokens is emitted (Solution's
	// no-guess rule).
	values := map[string]int64{"calls": 1}
	var usage pricing.Usage
	if tok, ok := ReadField(g, 4); ok && tok.WireType == 2 {
		if inF, ok := ReadField(tok.Bytes, 2); ok && inF.WireType == 0 {
			values["input_tokens"] = int64(inF.Varint)
			usage.InputTokens = int64(inF.Varint)
		}
		if outF, ok := ReadField(tok.Bytes, 3); ok && outF.WireType == 0 {
			values["output_tokens"] = int64(outF.Varint)
			usage.OutputTokens = int64(outF.Varint)
		}
	}
	if cost, priced := pricing.PriceGemini(model, usage); priced {
		values["cost_microusd"] = cost
	}

	labels := map[string]string{
		"source":    "antigravity",
		"session":   cascadeID,
		"model_raw": model,
		"db_file":   dbFile,
	}
	// trajectory_id: the finer-grained id from the gen 3->20 {key,value} map.
	if tid := mapValue(g, "trajectory_id"); tid != "" {
		labels["trajectory_id"] = tid
	}

	if project == "" {
		project = cascadeID // last resort: keep the Stack root non-empty
	}
	stack := []string{project, "antigravity", model}

	return schema.Sample{Time: t, Stack: stack, Values: values, Labels: labels}, true
}

// mapValue returns the value for key in the gen submessage's repeated field-20
// {1: key, 2: value} string map, or "" if absent.
func mapValue(g []byte, key string) string {
	fields, ok := Walk(g)
	if !ok {
		return ""
	}
	for _, f := range fields {
		if f.Num != 20 || f.WireType != 2 {
			continue
		}
		k, kok := ReadField(f.Bytes, 1)
		v, vok := ReadField(f.Bytes, 2)
		if kok && vok && string(k.Bytes) == key {
			return string(v.Bytes)
		}
	}
	return ""
}

// projectFromDB reads the project frame from trajectory_metadata_blob (id='main').
func projectFromDB(db *sql.DB) string {
	var blob []byte
	if err := db.QueryRow(`SELECT data FROM trajectory_metadata_blob WHERE id = 'main'`).Scan(&blob); err != nil {
		return ""
	}
	return projectFromTrajectoryBlob(blob)
}

// projectFromTrajectoryBlob applies Solution item 2's extraction rule: prefer
// the field-18 project label when present and non-empty, else the basename of
// the workspace file:// URI (field 1, sub-field 1), else the raw URI.
func projectFromTrajectoryBlob(blob []byte) string {
	if f18, ok := ReadField(blob, 18); ok && f18.WireType == 2 && len(f18.Bytes) > 0 {
		return string(f18.Bytes)
	}
	if uriF, ok := ReadPath(blob, 1, 1); ok && uriF.WireType == 2 && len(uriF.Bytes) > 0 {
		return workspaceBasename(string(uriF.Bytes))
	}
	return ""
}

// workspaceBasename returns the final path element of a file:// workspace URI,
// falling back to the raw URI if a basename can't be extracted.
func workspaceBasename(uri string) string {
	p := strings.TrimPrefix(uri, "file://")
	p = strings.TrimRight(p, "/")
	base := path.Base(p)
	if base == "" || base == "." || base == "/" {
		return uri
	}
	return base
}
