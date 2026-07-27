package main

import (
	"bufio"
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"syscall"
	"time"

	"github.com/sticklane/agentprof/internal/claude"
	"github.com/sticklane/agentprof/internal/judge"
)

// TriggerClass labels how a single Skill invocation was decided.
type TriggerClass string

const (
	// ClassCorrectlyTriggered marks a model-auto-trigger the judge deemed a good fit.
	ClassCorrectlyTriggered TriggerClass = "correctly-triggered"
	// ClassMisfired marks a model-auto-trigger the judge deemed a bad fit.
	ClassMisfired TriggerClass = "misfired"
	// ClassUnresolvable marks an invocation whose SKILL.md was not found at either path.
	ClassUnresolvable TriggerClass = "unresolvable"
	// ClassExplicitInvocation marks a slash-command or disable-model-invocation invocation.
	ClassExplicitInvocation TriggerClass = "explicit_invocation"
	// ClassSelfChained marks an invocation with no user turn since the previous one.
	ClassSelfChained TriggerClass = "self_chained"
)

const (
	// SkillFormulaVersion identifies the scorecard eligibility formula.
	SkillFormulaVersion = "r6-v1"
	// TriggerMatcherVersion identifies deterministic quoted-phrase matching.
	TriggerMatcherVersion = "quoted-phrases-v1"
	// TriggerJudgePromptVersion identifies the applicability prompt.
	TriggerJudgePromptVersion = "trigger-fit-v1"
)

// triggerJudgeTier is the deep tier used for the trigger-correctness judgment.
const triggerJudgeTier = "opus"

// TriggerResult is one invocation's classification, plus the resolved description
// (populated only for the model-auto-trigger population that reached the judge).
type TriggerResult struct {
	Name        string
	Class       TriggerClass
	Description string
	Judgment    SkillJudgment
}

// TriggerInput pairs a task-01 SkillInvocation with the text of the user turn(s)
// that preceded it. SkillInvocation itself carries no user-turn text, so the
// caller supplies it here for the trigger-correctness judge comparison.
type TriggerInput struct {
	// Invocation and UserTurn are the trigger-classification evidence.
	Invocation claude.SkillInvocation
	UserTurn   string
	// SessionID, Timestamp, and EvidenceRecordIDs identify frozen evidence.
	SessionID         string
	Timestamp         time.Time
	EvidenceRecordIDs []string
}

// SkillJudgment is the immutable eligibility/trigger decision consumed by the
// scorecard. A record is keyed by formula version, session, and skill.
type SkillJudgment struct {
	SchemaVersion      int      `json:"schema_version"`
	FormulaVersion     string   `json:"formula_version"`
	TimestampUTC       string   `json:"timestamp_utc"`
	SessionID          string   `json:"session_id"`
	Skill              string   `json:"skill"`
	MatcherVersion     string   `json:"matcher_version"`
	SkillContentHash   string   `json:"skill_content_hash"`
	JudgeModel         string   `json:"judge_model"`
	JudgePromptVersion string   `json:"judge_prompt_version"`
	EligibilityVerdict string   `json:"eligibility_verdict"`
	TriggerVerdict     string   `json:"trigger_verdict"`
	EvidenceRecordIDs  []string `json:"evidence_record_ids"`
}

// SkillJudgmentStore is an append-only month-partitioned judgment directory.
type SkillJudgmentStore struct {
	// Root contains YYYY-MM.jsonl partitions; FormulaVersion defaults to R6.
	Root           string
	FormulaVersion string
}

// Resolver locates a skill's SKILL.md by the two-path resolution order the spec
// fixes: cwd-relative .claude/skills, then the plugin cache.
type Resolver struct {
	Cwd             string
	PluginCacheRoot string
}

// resolve returns the SKILL.md path for a skill name, trying the cwd-relative
// path first and the plugin cache (marketplace/plugin globbed) second.
func (r Resolver) resolve(name string) (string, bool) {
	local := filepath.Join(r.Cwd, ".claude", "skills", name, "SKILL.md")
	if isFile(local) {
		return local, true
	}
	matches, _ := filepath.Glob(filepath.Join(r.PluginCacheRoot, "*", "*", "skills", name, "SKILL.md"))
	for _, m := range matches {
		if isFile(m) {
			return m, true
		}
	}
	return "", false
}

// installedSkillPaths enumerates every currently-installed skill's SKILL.md
// across both the cwd-relative and plugin-cache layouts.
func (r Resolver) installedSkillPaths() []string {
	var paths []string
	local, _ := filepath.Glob(filepath.Join(r.Cwd, ".claude", "skills", "*", "SKILL.md"))
	paths = append(paths, local...)
	plugin, _ := filepath.Glob(filepath.Join(r.PluginCacheRoot, "*", "*", "skills", "*", "SKILL.md"))
	paths = append(paths, plugin...)
	return paths
}

// ClassifyTriggers classifies each invocation into exactly one TriggerClass.
// The population split runs first (explicit-slash-command, then self-chain); the
// remaining model-auto-trigger population is resolved to its SKILL.md and either
// exempted (disable-model-invocation), marked unresolvable, or scored by the judge.
func ClassifyTriggers(inputs []TriggerInput, r Resolver, j judge.Judge) ([]TriggerResult, error) {
	out := make([]TriggerResult, 0, len(inputs))
	for _, in := range inputs {
		res := TriggerResult{Name: in.Invocation.Name}
		switch {
		case in.Invocation.CommandTag != "":
			res.Class = ClassExplicitInvocation
		case !in.Invocation.PrecededByUserTurn:
			res.Class = ClassSelfChained
		default:
			path, ok := r.resolve(in.Invocation.Name)
			if !ok {
				res.Class = ClassUnresolvable
				break
			}
			fm, err := claude.SkillFrontmatter(path)
			if err != nil {
				return nil, err
			}
			if fm.DisableModelInvocation {
				res.Class = ClassExplicitInvocation
				break
			}
			res.Description = fm.Description
			reply, err := j.Judge(triggerPrompt(fm.Description, in.UserTurn), triggerJudgeTier)
			if err != nil {
				return nil, err
			}
			if judgedCorrect(reply) {
				res.Class = ClassCorrectlyTriggered
			} else {
				res.Class = ClassMisfired
			}
		}
		out = append(out, res)
	}
	return out, nil
}

// ClassifyTriggersFrozen reuses a persisted decision before reading current
// skill content or calling the judge, so reruns cannot rewrite history.
func ClassifyTriggersFrozen(
	inputs []TriggerInput,
	r Resolver,
	j judge.Judge,
	store SkillJudgmentStore,
	judgeModel string,
) ([]TriggerResult, error) {
	type groupKey struct {
		session string
		skill   string
	}
	type group struct {
		indices []int
		inputs  []TriggerInput
	}
	groups := map[groupKey]*group{}
	var order []groupKey
	for i, in := range inputs {
		if in.SessionID == "" || in.Timestamp.IsZero() {
			return nil, fmt.Errorf("frozen trigger judgment requires session id and timestamp")
		}
		if in.Invocation.Name == "" {
			return nil, fmt.Errorf("frozen trigger judgment requires skill name")
		}
		key := groupKey{session: in.SessionID, skill: in.Invocation.Name}
		if groups[key] == nil {
			groups[key] = &group{}
			order = append(order, key)
		}
		groups[key].indices = append(groups[key].indices, i)
		groups[key].inputs = append(groups[key].inputs, in)
	}

	out := make([]TriggerResult, len(inputs))
	for _, key := range order {
		group := groups[key]
		if existing, ok, err := store.find(key.session, key.skill); err != nil {
			return nil, err
		} else if ok {
			for i, input := range group.inputs {
				class := TriggerClass(existing.TriggerVerdict)
				if input.Invocation.CommandTag != "" {
					class = ClassExplicitInvocation
				} else if !input.Invocation.PrecededByUserTurn {
					class = ClassSelfChained
				}
				out[group.indices[i]] = TriggerResult{
					Name:     input.Invocation.Name,
					Class:    class,
					Judgment: existing,
				}
			}
			continue
		}

		classified, err := ClassifyTriggers(group.inputs, r, j)
		if err != nil {
			return nil, err
		}
		timestamp, candidate, err := aggregateTriggerJudgment(
			group.inputs,
			classified,
			r,
			j,
			store.formulaVersion(),
			judgeModel,
		)
		if err != nil {
			return nil, err
		}
		frozen, err := store.getOrAppend(timestamp, candidate)
		if err != nil {
			return nil, err
		}
		for i, result := range classified {
			result.Judgment = frozen
			out[group.indices[i]] = result
		}
	}
	return out, nil
}

func aggregateTriggerJudgment(
	inputs []TriggerInput,
	results []TriggerResult,
	r Resolver,
	j judge.Judge,
	formulaVersion string,
	judgeModel string,
) (time.Time, SkillJudgment, error) {
	timestamp := inputs[0].Timestamp
	var evidence []string
	var userTurns []string
	hasExplicit := false
	hasSelfChain := false
	hasUnresolvable := false
	hasCorrect := false
	hasMisfired := false
	for i, input := range inputs {
		if input.Timestamp.Before(timestamp) {
			timestamp = input.Timestamp
		}
		evidence = append(evidence, input.EvidenceRecordIDs...)
		if strings.TrimSpace(input.UserTurn) != "" {
			userTurns = append(userTurns, input.UserTurn)
		}
		switch results[i].Class {
		case ClassExplicitInvocation:
			hasExplicit = true
		case ClassSelfChained:
			hasSelfChain = true
		case ClassUnresolvable:
			hasUnresolvable = true
		case ClassCorrectlyTriggered:
			hasCorrect = true
		case ClassMisfired:
			hasMisfired = true
		}
	}

	skill := inputs[0].Invocation.Name
	contentHash := "unknown"
	description := ""
	if path, ok := r.resolve(skill); ok {
		content, err := os.ReadFile(path)
		if err != nil {
			return time.Time{}, SkillJudgment{}, err
		}
		contentHash = fileSHA256FromBytes(content)
		if !hasExplicit {
			frontmatter, err := claude.SkillFrontmatterBytes(content)
			if err != nil {
				return time.Time{}, SkillJudgment{}, err
			}
			description = frontmatter.Description
		}
	}

	combinedTurns := strings.Join(userTurns, "\n")
	matcherHit := description != "" && matchesDeclaredPhrase(description, combinedTurns)
	matcherApplicable := matcherHit && hasCorrect
	if matcherHit && !hasCorrect && !hasMisfired && !hasExplicit {
		reply, err := j.Judge(triggerPrompt(description, combinedTurns), triggerJudgeTier)
		if err != nil {
			return time.Time{}, SkillJudgment{}, err
		}
		matcherApplicable = judgedCorrect(reply)
	}

	eligibility := "ineligible-self-chain"
	trigger := string(ClassSelfChained)
	persistedJudgeModel := "none"
	switch {
	case hasExplicit:
		eligibility = "explicit"
		trigger = string(ClassExplicitInvocation)
	case hasCorrect && matcherHit:
		eligibility = "applicable"
		trigger = string(ClassCorrectlyTriggered)
		persistedJudgeModel = judgeModel
	case matcherApplicable:
		eligibility = "applicable"
		trigger = "missed"
		persistedJudgeModel = judgeModel
	case hasCorrect:
		eligibility = "not-applicable"
		trigger = string(ClassCorrectlyTriggered)
		persistedJudgeModel = judgeModel
	case hasMisfired:
		eligibility = "not-applicable"
		trigger = string(ClassMisfired)
		persistedJudgeModel = judgeModel
	case matcherHit:
		eligibility = "not-applicable"
		trigger = "not-triggered"
		persistedJudgeModel = judgeModel
	case hasUnresolvable:
		eligibility = "unknown"
		trigger = string(ClassUnresolvable)
	case !hasSelfChain:
		return time.Time{}, SkillJudgment{}, fmt.Errorf(
			"no trigger evidence for (%s, %s)",
			inputs[0].SessionID,
			skill,
		)
	}

	return timestamp, SkillJudgment{
		SchemaVersion:      1,
		FormulaVersion:     formulaVersion,
		TimestampUTC:       timestamp.UTC().Format(time.RFC3339Nano),
		SessionID:          inputs[0].SessionID,
		Skill:              skill,
		MatcherVersion:     TriggerMatcherVersion,
		SkillContentHash:   contentHash,
		JudgeModel:         persistedJudgeModel,
		JudgePromptVersion: TriggerJudgePromptVersion,
		EligibilityVerdict: eligibility,
		TriggerVerdict:     trigger,
		EvidenceRecordIDs:  uniqueSorted(evidence),
	}, nil
}

// FreezePossibleMissJudgment judges one deterministic matcher hit only when no
// frozen session/skill record already exists.
func FreezePossibleMissJudgment(
	sessionID string,
	timestamp time.Time,
	miss PossibleMiss,
	evidenceRecordIDs []string,
	r Resolver,
	j judge.Judge,
	store SkillJudgmentStore,
) (SkillJudgment, error) {
	if existing, ok, err := store.find(sessionID, miss.Skill); err != nil {
		return SkillJudgment{}, err
	} else if ok {
		return existing, nil
	}
	path, ok := r.resolve(miss.Skill)
	if !ok {
		return SkillJudgment{}, fmt.Errorf("matched skill %q no longer resolves", miss.Skill)
	}
	content, err := os.ReadFile(path)
	if err != nil {
		return SkillJudgment{}, err
	}
	fm, err := claude.SkillFrontmatterBytes(content)
	if err != nil {
		return SkillJudgment{}, err
	}
	reply, err := j.Judge(triggerPrompt(fm.Description, miss.UserTurn), triggerJudgeTier)
	if err != nil {
		return SkillJudgment{}, err
	}
	hash := fileSHA256FromBytes(content)
	eligibility, trigger := "not-applicable", "not-triggered"
	if judgedCorrect(reply) {
		eligibility, trigger = "applicable", "missed"
	}
	return store.getOrAppend(timestamp, SkillJudgment{
		SchemaVersion:      1,
		FormulaVersion:     store.formulaVersion(),
		TimestampUTC:       timestamp.UTC().Format(time.RFC3339Nano),
		SessionID:          sessionID,
		Skill:              miss.Skill,
		MatcherVersion:     TriggerMatcherVersion,
		SkillContentHash:   hash,
		JudgeModel:         triggerJudgeTier,
		JudgePromptVersion: TriggerJudgePromptVersion,
		EligibilityVerdict: eligibility,
		TriggerVerdict:     trigger,
		EvidenceRecordIDs:  uniqueSorted(evidenceRecordIDs),
	})
}

func fileSHA256FromBytes(content []byte) string {
	sum := sha256.Sum256(content)
	return hex.EncodeToString(sum[:])
}

func (s SkillJudgmentStore) formulaVersion() string {
	if s.FormulaVersion == "" {
		return SkillFormulaVersion
	}
	return s.FormulaVersion
}

func validateSkillJudgment(
	row SkillJudgment,
	expectedFormula string,
) (time.Time, error) {
	if row.SchemaVersion != 1 {
		return time.Time{}, fmt.Errorf("schema_version must be 1")
	}
	if row.FormulaVersion != expectedFormula {
		return time.Time{}, fmt.Errorf(
			"formula_version must be %q",
			expectedFormula,
		)
	}
	if row.SessionID == "" || row.Skill == "" {
		return time.Time{}, fmt.Errorf("session_id and skill must be non-empty")
	}
	if row.MatcherVersion != TriggerMatcherVersion {
		return time.Time{}, fmt.Errorf(
			"matcher_version must be %q",
			TriggerMatcherVersion,
		)
	}
	if row.JudgePromptVersion != TriggerJudgePromptVersion {
		return time.Time{}, fmt.Errorf(
			"judge_prompt_version must be %q",
			TriggerJudgePromptVersion,
		)
	}
	if row.SkillContentHash != "unknown" && !isSHA256(row.SkillContentHash) {
		return time.Time{}, fmt.Errorf(
			"skill_content_hash must be SHA-256 or unknown",
		)
	}
	if !strings.HasSuffix(row.TimestampUTC, "Z") {
		return time.Time{}, fmt.Errorf("timestamp_utc must be UTC RFC3339")
	}
	parsed, err := time.Parse(time.RFC3339Nano, row.TimestampUTC)
	if err != nil {
		return time.Time{}, fmt.Errorf("timestamp_utc: %w", err)
	}
	_, offset := parsed.Zone()
	if offset != 0 {
		return time.Time{}, fmt.Errorf("timestamp_utc must be UTC")
	}
	pair := [2]string{row.EligibilityVerdict, row.TriggerVerdict}
	noJudge := false
	switch pair {
	case [2]string{"explicit", string(ClassExplicitInvocation)},
		[2]string{"ineligible-self-chain", string(ClassSelfChained)},
		[2]string{"unknown", string(ClassUnresolvable)}:
		noJudge = true
	case [2]string{"applicable", string(ClassCorrectlyTriggered)},
		[2]string{"applicable", "missed"},
		[2]string{"not-applicable", string(ClassCorrectlyTriggered)},
		[2]string{"not-applicable", string(ClassMisfired)},
		[2]string{"not-applicable", "not-triggered"}:
	default:
		return time.Time{}, fmt.Errorf(
			"invalid eligibility/trigger verdict pair %q/%q",
			row.EligibilityVerdict,
			row.TriggerVerdict,
		)
	}
	if noJudge {
		if row.JudgeModel != "none" {
			return time.Time{}, fmt.Errorf("judge_model must be none")
		}
	} else if row.JudgeModel == "" ||
		row.JudgeModel == "none" ||
		row.JudgeModel == "unknown" {
		return time.Time{}, fmt.Errorf("judge_model must identify the judge")
	}
	if len(row.EvidenceRecordIDs) == 0 {
		return time.Time{}, fmt.Errorf("evidence_record_ids must be non-empty")
	}
	seen := map[string]bool{}
	for _, recordID := range row.EvidenceRecordIDs {
		if strings.TrimSpace(recordID) == "" {
			return time.Time{}, fmt.Errorf(
				"evidence_record_ids must contain non-empty strings",
			)
		}
		if seen[recordID] {
			return time.Time{}, fmt.Errorf(
				"evidence_record_ids must not contain duplicates",
			)
		}
		seen[recordID] = true
	}
	return parsed, nil
}

func isSHA256(value string) bool {
	if len(value) != sha256.Size*2 || value != strings.ToLower(value) {
		return false
	}
	decoded, err := hex.DecodeString(value)
	return err == nil && len(decoded) == sha256.Size
}

func uniqueSorted(values []string) []string {
	seen := map[string]bool{}
	var unique []string
	for _, value := range values {
		if seen[value] {
			continue
		}
		seen[value] = true
		unique = append(unique, value)
	}
	sort.Strings(unique)
	return unique
}

func (s SkillJudgmentStore) find(sessionID, skill string) (SkillJudgment, bool, error) {
	if err := os.MkdirAll(s.Root, 0o755); err != nil {
		return SkillJudgment{}, false, err
	}
	lock, err := os.OpenFile(filepath.Join(s.Root, ".lock"), os.O_CREATE|os.O_RDWR, 0o600)
	if err != nil {
		return SkillJudgment{}, false, err
	}
	defer lock.Close()
	if err := syscall.Flock(int(lock.Fd()), syscall.LOCK_SH); err != nil {
		return SkillJudgment{}, false, err
	}
	defer syscall.Flock(int(lock.Fd()), syscall.LOCK_UN) //nolint:errcheck
	return s.findUnlocked(sessionID, skill)
}

func (s SkillJudgmentStore) findUnlocked(sessionID, skill string) (SkillJudgment, bool, error) {
	paths, err := filepath.Glob(filepath.Join(s.Root, "*.jsonl"))
	if err != nil {
		return SkillJudgment{}, false, err
	}
	var found *SkillJudgment
	for _, path := range paths {
		rows, err := readSkillJudgmentsForFormula(path, s.formulaVersion())
		if err != nil {
			return SkillJudgment{}, false, err
		}
		for _, row := range rows {
			if row.FormulaVersion != s.formulaVersion() ||
				row.SessionID != sessionID || row.Skill != skill {
				continue
			}
			if found != nil {
				return SkillJudgment{}, false, fmt.Errorf(
					"duplicate frozen judgment for (%s, %s, %s)",
					row.FormulaVersion, sessionID, skill,
				)
			}
			copy := row
			found = &copy
		}
	}
	if found == nil {
		return SkillJudgment{}, false, nil
	}
	return *found, true, nil
}

func (s SkillJudgmentStore) getOrAppend(
	timestamp time.Time,
	candidate SkillJudgment,
) (SkillJudgment, error) {
	candidateTime, err := validateSkillJudgment(
		candidate,
		s.formulaVersion(),
	)
	if err != nil {
		return SkillJudgment{}, fmt.Errorf("invalid frozen judgment: %w", err)
	}
	if !candidateTime.Equal(timestamp) {
		return SkillJudgment{}, fmt.Errorf(
			"judgment timestamp does not match partition timestamp",
		)
	}
	if err := os.MkdirAll(s.Root, 0o755); err != nil {
		return SkillJudgment{}, err
	}
	lock, err := os.OpenFile(filepath.Join(s.Root, ".lock"), os.O_CREATE|os.O_RDWR, 0o600)
	if err != nil {
		return SkillJudgment{}, err
	}
	defer lock.Close()
	if err := syscall.Flock(int(lock.Fd()), syscall.LOCK_EX); err != nil {
		return SkillJudgment{}, err
	}
	defer syscall.Flock(int(lock.Fd()), syscall.LOCK_UN) //nolint:errcheck

	if existing, ok, err := s.findUnlocked(candidate.SessionID, candidate.Skill); err != nil {
		return SkillJudgment{}, err
	} else if ok {
		return existing, nil
	}
	path := skillJudgmentPath(s.Root, timestamp)
	file, err := os.OpenFile(path, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o600)
	if err != nil {
		return SkillJudgment{}, err
	}
	payload, err := json.Marshal(candidate)
	if err == nil {
		payload = append(payload, '\n')
		_, err = file.Write(payload)
	}
	if err == nil {
		err = file.Sync()
	}
	closeErr := file.Close()
	if err != nil {
		return SkillJudgment{}, err
	}
	if closeErr != nil {
		return SkillJudgment{}, closeErr
	}
	return candidate, nil
}

func skillJudgmentPath(root string, timestamp time.Time) string {
	return filepath.Join(root, timestamp.UTC().Format("2006-01")+".jsonl")
}

func readSkillJudgments(path string) ([]SkillJudgment, error) {
	return readSkillJudgmentsForFormula(path, SkillFormulaVersion)
}

func readSkillJudgmentsForFormula(
	path string,
	expectedFormula string,
) ([]SkillJudgment, error) {
	file, err := os.Open(path)
	if os.IsNotExist(err) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	defer file.Close()
	var rows []SkillJudgment
	scanner := bufio.NewScanner(file)
	line := 0
	for scanner.Scan() {
		line++
		var row SkillJudgment
		decoder := json.NewDecoder(bytes.NewReader(scanner.Bytes()))
		decoder.DisallowUnknownFields()
		if err := decoder.Decode(&row); err != nil {
			return nil, fmt.Errorf(
				"%s:%d: malformed judgment: %w",
				path,
				line,
				err,
			)
		}
		if err := decoder.Decode(&struct{}{}); err != io.EOF {
			return nil, fmt.Errorf(
				"%s:%d: malformed judgment: trailing JSON",
				path,
				line,
			)
		}
		if _, err := validateSkillJudgment(row, expectedFormula); err != nil {
			return nil, fmt.Errorf(
				"%s:%d: invalid judgment: %w",
				path,
				line,
				err,
			)
		}
		rows = append(rows, row)
	}
	return rows, scanner.Err()
}

func fileSHA256(path string) (string, error) {
	content, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	sum := sha256.Sum256(content)
	return hex.EncodeToString(sum[:]), nil
}

// triggerPrompt builds the trigger-correctness grading prompt, grounding the
// judgment in the skill's actual description and the preceding user turn.
func triggerPrompt(description, userTurn string) string {
	return fmt.Sprintf(`A skill was auto-triggered by the model. Decide whether the trigger was a good fit.

Skill description (its declared purpose and trigger phrases):
%s

Preceding user turn(s):
%s

Answer with exactly one word: "correctly-triggered" if the user turn is a good fit for this skill's description, or "misfired" if it is not.`, description, userTurn)
}

// judgedCorrect reads the judge's verdict text, treating an affirmative reply as
// a correct trigger. It parses structure rather than an exact string.
func judgedCorrect(reply string) bool {
	r := strings.ToLower(strings.TrimSpace(reply))
	if strings.Contains(r, "misfire") {
		return false
	}
	return strings.Contains(r, "correct") || strings.HasPrefix(r, "yes")
}

// PossibleMiss is one user turn whose text matched an installed skill's declared
// trigger phrase without a corresponding Skill invocation.
type PossibleMiss struct {
	UserTurn string
	Skill    string
	Phrase   string
}

// DetectPossibleMisses flags non-triggering user turns that match an installed
// skill's declared trigger phrase, via deterministic substring matching only
// (no judge call). Trigger phrases are the double-quoted spans in each installed
// skill's description.
func DetectPossibleMisses(userTurns []string, r Resolver) ([]PossibleMiss, error) {
	type installedSkill struct {
		name    string
		phrases []string
	}
	var installed []installedSkill
	for _, path := range r.installedSkillPaths() {
		fm, err := claude.SkillFrontmatter(path)
		if err != nil {
			return nil, err
		}
		installed = append(installed, installedSkill{
			name:    filepath.Base(filepath.Dir(path)),
			phrases: quotedPhrases(fm.Description),
		})
	}

	var misses []PossibleMiss
	for _, turn := range userTurns {
		lower := strings.ToLower(turn)
		for _, s := range installed {
			for _, ph := range s.phrases {
				if ph == "" {
					continue
				}
				if strings.Contains(lower, strings.ToLower(ph)) {
					misses = append(misses, PossibleMiss{UserTurn: turn, Skill: s.name, Phrase: ph})
					break
				}
			}
		}
	}
	return misses, nil
}

// quotedPhrases extracts the double-quoted spans from a description, the
// deterministic proxy for a skill's declared trigger phrases.
func quotedPhrases(description string) []string {
	var phrases []string
	rest := description
	for {
		i := strings.IndexByte(rest, '"')
		if i < 0 {
			break
		}
		rest = rest[i+1:]
		j := strings.IndexByte(rest, '"')
		if j < 0 {
			break
		}
		if ph := strings.TrimSpace(rest[:j]); ph != "" {
			phrases = append(phrases, ph)
		}
		rest = rest[j+1:]
	}
	return phrases
}

func matchesDeclaredPhrase(description, userTurn string) bool {
	lower := strings.ToLower(userTurn)
	for _, phrase := range quotedPhrases(description) {
		if strings.Contains(lower, strings.ToLower(phrase)) {
			return true
		}
	}
	return false
}

// isFile reports whether path exists and is a regular file.
func isFile(path string) bool {
	info, err := os.Stat(path)
	return err == nil && !info.IsDir()
}
