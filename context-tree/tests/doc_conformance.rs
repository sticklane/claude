//! docs↔binary conformance gate (specs/ctx-doc-drift-gate R1 + R3).
//!
//! Extracts every backtick-quoted `ctx <subcommand> [--flag …]` invocation
//! from the three doc surfaces agents load at query time — the ctx skill, its
//! antigravity mirror, and the CUJ guide — and asserts each named subcommand
//! and flag exists in the binary's clap definition (discovered by recursively
//! parsing `--help`). Known drift is suppressed by a shape-keyed waiver list;
//! a waiver that no longer matches any doc row is reported as a WARNING (never
//! a failure). A non-gating reverse-coverage report (R3) lists binary
//! capabilities absent from all three docs.

use std::collections::{BTreeMap, BTreeSet};
use std::fmt::Write as _;
use std::path::{Path, PathBuf};
use std::process::Command;

// ---------------------------------------------------------------------------
// Seeded known-drift waivers.
//
// Keyed by invocation SHAPE (subcommand path + flag), matched across all three
// doc files, so one entry covers identical rows in the skill and its mirror.
//
//   `map --limit` — the ctx skill and its antigravity mirror both document
//        `ctx map [--limit N]`, but the binary's flag is `--tokens`. The typo
//        fix is owned by specs/ctx-cujs/tasks/02; this spec's task 03 retires
//        this waiver once cujs/02 lands.
//   `show`        — docs/guides/ctx-cujs.md documents `ctx show <symbol>` for
//        an as-yet-unshipped subcommand (the guide itself notes "`show` is not
//        yet shipped"). Waived so R1 can land green before `show` ships or the
//        guide is corrected.
const WAIVERS: &[Waiver] = &[
    Waiver {
        subcommand: "map",
        flag: Some("--limit"),
    },
    Waiver {
        subcommand: "show",
        flag: None,
    },
];

#[derive(Clone, Copy)]
struct Waiver {
    /// Space-joined subcommand path, e.g. `"map"` or `"notes add"`.
    subcommand: &'static str,
    /// Flag long-name (`Some("--limit")`), or `None` for a whole unknown
    /// subcommand.
    flag: Option<&'static str>,
}

// ---------------------------------------------------------------------------
// CLI model, discovered from the binary's recursive `--help` output.

#[derive(Default)]
struct CliModel {
    /// subcommand path -> its flag long-names.
    flags: BTreeMap<Vec<String>, BTreeSet<String>>,
    /// subcommand path -> its child subcommand names.
    children: BTreeMap<Vec<String>, BTreeSet<String>>,
}

impl CliModel {
    fn is_subcommand(&self, path: &[String], name: &str) -> bool {
        self.children
            .get(path)
            .is_some_and(|kids| kids.contains(name))
    }

    fn flags_for(&self, path: &[String]) -> Option<&BTreeSet<String>> {
        self.flags.get(path)
    }
}

fn run_help(path: &[String]) -> Option<String> {
    let mut cmd = Command::new(env!("CARGO_BIN_EXE_ctx"));
    for segment in path {
        cmd.arg(segment);
    }
    cmd.arg("--help");
    let out = cmd.output().ok()?;
    if out.status.success() {
        String::from_utf8(out.stdout).ok()
    } else {
        None
    }
}

/// Parse one `--help` page into (child subcommands, flag long-names).
fn parse_help(output: &str) -> (BTreeSet<String>, BTreeSet<String>) {
    let mut children = BTreeSet::new();
    let mut flags = BTreeSet::new();
    let mut section = Section::None;

    for line in output.lines() {
        let trimmed = line.trim();
        match trimmed {
            "Commands:" => {
                section = Section::Commands;
                continue;
            }
            "Options:" => {
                section = Section::Options;
                continue;
            }
            "Arguments:" => {
                section = Section::Other;
                continue;
            }
            _ => {}
        }
        // A blank line, or a non-indented line (e.g. `Usage:`, the summary),
        // closes the current section.
        if trimmed.is_empty() || !line.starts_with(' ') {
            section = Section::None;
            continue;
        }
        match section {
            Section::Commands => {
                if let Some(name) = trimmed.split_whitespace().next() {
                    // `help` is clap's built-in, never a documented verb.
                    if name != "help" && looks_like_subcommand(name) {
                        children.insert(name.to_string());
                    }
                }
            }
            Section::Options => {
                if let Some(tok) = trimmed.split_whitespace().find(|w| w.starts_with("--")) {
                    let name: String = tok
                        .chars()
                        .take_while(|c| c.is_ascii_alphanumeric() || *c == '-')
                        .collect();
                    if name.len() > 2 {
                        flags.insert(name);
                    }
                }
            }
            Section::Other | Section::None => {}
        }
    }
    (children, flags)
}

enum Section {
    None,
    Commands,
    Options,
    Other,
}

/// Build the full CLI model by BFS over `--help` pages, keeping only children
/// whose own `--help` succeeds (prunes any description word misread as a verb).
fn build_cli_model() -> CliModel {
    let mut model = CliModel::default();
    let mut queue: Vec<Vec<String>> = vec![Vec::new()];

    while let Some(path) = queue.pop() {
        let Some(help) = run_help(&path) else {
            continue;
        };
        let (children, flags) = parse_help(&help);
        model.flags.insert(path.clone(), flags);

        let mut kept = BTreeSet::new();
        for child in children {
            let mut child_path = path.clone();
            child_path.push(child.clone());
            if run_help(&child_path).is_some() {
                kept.insert(child);
                queue.push(child_path);
            }
        }
        model.children.insert(path.clone(), kept);
    }
    model
}

// ---------------------------------------------------------------------------
// Invocation extraction + tokenizer.

/// A token that could be a subcommand: lowercase ASCII letters and dashes
/// only (e.g. `notes`, `add`, `pre-commit`). Excludes flags (`--x`),
/// placeholders (`<x>`), quoted args, enum lists, and colon forms.
fn looks_like_subcommand(tok: &str) -> bool {
    !tok.is_empty()
        && tok.chars().all(|c| c.is_ascii_lowercase() || c == '-')
        && tok.starts_with(|c: char| c.is_ascii_lowercase())
}

/// Extract every backtick-quoted span that is a `ctx …` invocation. Handles
/// inline code (single backticks, possibly wrapping across a source newline)
/// and fenced code blocks (```), while ignoring non-`ctx` inline code.
fn extract_ctx_invocations(markdown: &str) -> Vec<String> {
    let mut invocations = Vec::new();
    let mut unfenced = String::new();
    let mut in_fence = false;

    for line in markdown.lines() {
        let starts_fence = {
            let t = line.trim_start();
            t.starts_with("```") || t.starts_with("~~~")
        };
        if starts_fence {
            in_fence = !in_fence;
            continue;
        }
        if in_fence {
            let t = line.trim();
            if t == "ctx" || t.starts_with("ctx ") {
                invocations.push(normalize_ws(t));
            }
        } else {
            unfenced.push_str(line);
            unfenced.push('\n');
        }
    }

    // In fence-free text, odd-indexed `split('`')` segments are inline code.
    for (idx, segment) in unfenced.split('`').enumerate() {
        if idx % 2 == 1 {
            let norm = normalize_ws(segment);
            if norm == "ctx" || norm.starts_with("ctx ") {
                invocations.push(norm);
            }
        }
    }
    invocations
}

fn normalize_ws(s: &str) -> String {
    s.split_whitespace().collect::<Vec<_>>().join(" ")
}

/// Strip the wrapping of a flag token (`[--file` → `--file`) and return its
/// long-name, or `None` when the token is not a flag.
fn flag_name(tok: &str) -> Option<String> {
    let t = tok.trim_start_matches(['[', '"', '\'', '(']);
    if !t.starts_with("--") {
        return None;
    }
    let name: String = t
        .chars()
        .take_while(|c| c.is_ascii_alphanumeric() || *c == '-')
        .collect();
    (name.len() > 2).then_some(name)
}

// ---------------------------------------------------------------------------
// Analysis.

#[derive(Clone, PartialEq, Eq)]
enum DriftKind {
    UnknownSubcommand,
    UnknownFlag,
}

#[derive(Clone)]
struct Drift {
    file: String,
    invocation: String,
    /// Space-joined subcommand path, or the offending token for an unknown
    /// subcommand.
    subcommand: String,
    flag: Option<String>,
    kind: DriftKind,
}

impl Drift {
    fn describe(&self) -> String {
        match self.kind {
            DriftKind::UnknownSubcommand => format!("unknown subcommand `{}`", self.subcommand),
            DriftKind::UnknownFlag => format!(
                "unknown flag `{}` on `{}`",
                self.flag.as_deref().unwrap_or(""),
                self.subcommand
            ),
        }
    }

    fn matches_waiver(&self, w: &Waiver) -> bool {
        self.subcommand == w.subcommand && self.flag.as_deref() == w.flag
    }
}

/// One invocation's outcome: the valid path/flags it documents (for reverse
/// coverage) and any drift it introduces.
struct Analyzed {
    documented_path: Vec<String>,
    documented_flags: Vec<(Vec<String>, String)>,
    drift: Vec<Drift>,
}

fn analyze_invocation(file: &str, invocation: &str, model: &CliModel) -> Analyzed {
    let toks: Vec<&str> = invocation.split_whitespace().collect();
    let mut drift = Vec::new();
    let mut documented_flags = Vec::new();

    // toks[0] is `ctx`; walk the subcommand path greedily.
    let mut path: Vec<String> = Vec::new();
    let mut i = 1;
    while i < toks.len() {
        let tok = toks[i];
        if !looks_like_subcommand(tok) {
            break; // a flag, placeholder, or positional — path is settled.
        }
        if model.is_subcommand(&path, tok) {
            path.push(tok.to_string());
            i += 1;
        } else {
            drift.push(Drift {
                file: file.to_string(),
                invocation: invocation.to_string(),
                subcommand: tok.to_string(),
                flag: None,
                kind: DriftKind::UnknownSubcommand,
            });
            i += 1;
            break;
        }
    }

    let valid = model.flags_for(&path);
    for tok in &toks[i..] {
        if let Some(flag) = flag_name(tok) {
            if valid.is_some_and(|s| s.contains(&flag)) {
                documented_flags.push((path.clone(), flag));
            } else {
                drift.push(Drift {
                    file: file.to_string(),
                    invocation: invocation.to_string(),
                    subcommand: path.join(" "),
                    flag: Some(flag),
                    kind: DriftKind::UnknownFlag,
                });
            }
        }
    }

    Analyzed {
        documented_path: path,
        documented_flags,
        drift,
    }
}

struct Report {
    drift: Vec<Drift>,
    waived: Vec<Drift>,
    stale_waivers: Vec<Waiver>,
    reverse_coverage: Vec<String>,
}

fn analyze(docs: &[(String, String)], model: &CliModel, waivers: &[Waiver]) -> Report {
    let mut all_drift = Vec::new();
    let mut documented_paths: BTreeSet<Vec<String>> = BTreeSet::new();
    let mut documented_flags: BTreeSet<(Vec<String>, String)> = BTreeSet::new();

    for (file, content) in docs {
        for invocation in extract_ctx_invocations(content) {
            let analyzed = analyze_invocation(file, &invocation, model);
            if !analyzed.documented_path.is_empty() {
                documented_paths.insert(analyzed.documented_path);
            }
            documented_flags.extend(analyzed.documented_flags);
            all_drift.extend(analyzed.drift);
        }
    }

    // Partition drift by the waiver it matches; track which waivers fired.
    let mut used = vec![false; waivers.len()];
    let mut drift = Vec::new();
    let mut waived = Vec::new();
    for d in all_drift {
        match waivers.iter().position(|w| d.matches_waiver(w)) {
            Some(idx) => {
                used[idx] = true;
                waived.push(d);
            }
            None => drift.push(d),
        }
    }
    let stale_waivers = waivers
        .iter()
        .zip(used)
        .filter_map(|(w, fired)| (!fired).then_some(*w))
        .collect();

    let reverse_coverage = compute_reverse_coverage(model, &documented_paths, &documented_flags);

    Report {
        drift,
        waived,
        stale_waivers,
        reverse_coverage,
    }
}

/// Binary capabilities (subcommands and flags) absent from all doc surfaces.
fn compute_reverse_coverage(
    model: &CliModel,
    documented_paths: &BTreeSet<Vec<String>>,
    documented_flags: &BTreeSet<(Vec<String>, String)>,
) -> Vec<String> {
    let mut out = Vec::new();
    for (path, flags) in &model.flags {
        if path.is_empty() {
            continue; // the bare `ctx` root is not a documentable verb.
        }
        if !documented_paths.contains(path) {
            out.push(path.join(" "));
        }
        for flag in flags {
            if !documented_flags.contains(&(path.clone(), flag.clone())) {
                out.push(format!("{} {}", path.join(" "), flag));
            }
        }
    }
    out.sort();
    out.dedup();
    out
}

fn render_report(report: &Report) -> String {
    let mut s = String::new();
    let _ = writeln!(s, "== ctx docs↔binary conformance ==");
    let _ = writeln!(s, "unwaived drift: {}", report.drift.len());
    for d in &report.drift {
        let _ = writeln!(
            s,
            "  DRIFT [{}] `{}` — {}",
            d.file,
            d.invocation,
            d.describe()
        );
    }
    let _ = writeln!(s, "waived drift: {}", report.waived.len());
    for d in &report.waived {
        let _ = writeln!(
            s,
            "  waived [{}] `{}` — {}",
            d.file,
            d.invocation,
            d.describe()
        );
    }
    let _ = writeln!(s, "stale-waiver warnings: {}", report.stale_waivers.len());
    for w in &report.stale_waivers {
        let _ = writeln!(
            s,
            "  WARNING: waiver `{} {}` matches no documented invocation",
            w.subcommand,
            w.flag.unwrap_or("")
        );
    }
    let _ = writeln!(s, "-- reverse-coverage report (non-gating) --");
    if report.reverse_coverage.is_empty() {
        let _ = writeln!(s, "  (none — every binary capability is documented)");
    } else {
        for capability in &report.reverse_coverage {
            let _ = writeln!(s, "  undocumented: {capability}");
        }
    }
    s
}

// ---------------------------------------------------------------------------
// Doc loading.

fn repo_root() -> PathBuf {
    // CARGO_MANIFEST_DIR is the crate dir (`<repo>/context-tree`); the docs
    // live at the repo root above it.
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("context-tree has a parent repo root")
        .to_path_buf()
}

fn read_doc(rel: &str) -> (String, String) {
    let path = repo_root().join(rel);
    let content = std::fs::read_to_string(&path)
        .unwrap_or_else(|e| panic!("read doc surface {}: {e}", path.display()));
    (rel.to_string(), content)
}

fn load_real_docs() -> Vec<(String, String)> {
    vec![
        read_doc(".claude/skills/ctx/SKILL.md"),
        read_doc("antigravity/.agents/skills/ctx/SKILL.md"),
        read_doc("docs/guides/ctx-cujs.md"),
    ]
}

fn load_fixture(rel: &str) -> (String, String) {
    let path = Path::new(env!("CARGO_MANIFEST_DIR")).join(rel);
    let content = std::fs::read_to_string(&path)
        .unwrap_or_else(|e| panic!("read fixture {}: {e}", path.display()));
    (rel.to_string(), content)
}

// ---------------------------------------------------------------------------
// Tests.

/// R1: the docs conform to the binary once known drift is waived.
#[test]
fn docs_conform_to_binary_with_seeded_waivers() {
    let model = build_cli_model();
    let docs = load_real_docs();
    let report = analyze(&docs, &model, WAIVERS);

    // Printed so `cargo test -- --nocapture` surfaces the reverse-coverage
    // report (R3) and the waived/warning lines.
    println!("{}", render_report(&report));

    assert!(
        report.drift.is_empty(),
        "unwaived docs↔binary drift:\n{}",
        report
            .drift
            .iter()
            .map(|d| format!("  [{}] `{}` — {}", d.file, d.invocation, d.describe()))
            .collect::<Vec<_>>()
            .join("\n")
    );
}

/// R1 regression fixture: the `map --limit` shape is caught in BOTH the skill
/// and its antigravity mirror when unwaived.
#[test]
fn map_limit_drift_is_detected_in_both_skill_files_when_unwaived() {
    let model = build_cli_model();
    let docs = load_real_docs();
    let report = analyze(&docs, &model, &[]);

    let map_limit_files: Vec<&str> = report
        .drift
        .iter()
        .filter(|d| d.subcommand == "map" && d.flag.as_deref() == Some("--limit"))
        .map(|d| d.file.as_str())
        .collect();

    assert!(
        map_limit_files.contains(&".claude/skills/ctx/SKILL.md"),
        "map --limit drift not caught in the ctx skill; got {map_limit_files:?}"
    );
    assert!(
        map_limit_files.contains(&"antigravity/.agents/skills/ctx/SKILL.md"),
        "map --limit drift not caught in the antigravity mirror; got {map_limit_files:?}"
    );
}

/// R1 waiver semantics: a waiver matching no doc row warns, and — critically —
/// does not fail (drift stays empty, so the gate exits 0).
#[test]
fn stale_waiver_warns_without_failing() {
    let model = build_cli_model();
    let docs = vec![load_fixture("tests/fixtures/doc_conformance/valid_only.md")];
    let waivers = &[Waiver {
        subcommand: "frobnicate",
        flag: Some("--nope"),
    }];

    let report = analyze(&docs, &model, waivers);

    assert!(
        report.drift.is_empty(),
        "the fixture documents only valid invocations, so there is no drift"
    );
    assert_eq!(
        report.stale_waivers.len(),
        1,
        "the unmatched waiver must be reported stale"
    );
    // A stale waiver is a warning, never a failure: the gate would still pass.
    assert!(render_report(&report).contains("WARNING"));
}

/// R3: the reverse-coverage section is present and well-formed even when empty.
#[test]
fn reverse_coverage_section_is_present_and_well_formed_when_empty() {
    let empty = Report {
        drift: Vec::new(),
        waived: Vec::new(),
        stale_waivers: Vec::new(),
        reverse_coverage: Vec::new(),
    };
    let rendered = render_report(&empty);
    assert!(
        rendered.contains("reverse-coverage"),
        "the reverse-coverage section header must always be emitted"
    );
    assert!(
        rendered.contains("(none"),
        "the empty reverse-coverage section must be well-formed"
    );
}

/// R3: over the real docs the report populates with undocumented capabilities
/// (e.g. `sync`), and still carries the reverse-coverage header.
#[test]
fn reverse_coverage_lists_undocumented_capabilities() {
    let model = build_cli_model();
    let docs = load_real_docs();
    let report = analyze(&docs, &model, WAIVERS);

    assert!(
        !report.reverse_coverage.is_empty(),
        "the docs omit some binary capabilities, so the report is populated"
    );
    assert!(render_report(&report).contains("reverse-coverage"));
}
