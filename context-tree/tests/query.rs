//! R3/R6/R7/R8/R18 + C1/C3/C4/C7/C10 query-command integration tests for
//! `ctx tree`, `ctx sig`, and `ctx map`.

use std::path::Path;
use std::process::{Command, Output};
use std::thread::sleep;
use std::time::Duration;

/// Larger than the sync engine's racy-edit window (100 ms), so fixture files
/// sit safely outside it relative to a later query's sweep.
const PAST: Duration = Duration::from_millis(250);

fn write(root: &Path, rel: &str, content: &str) {
    let p = root.join(rel);
    if let Some(parent) = p.parent() {
        std::fs::create_dir_all(parent).unwrap();
    }
    std::fs::write(p, content).unwrap();
}

/// Run `ctx <args>` in `root`, returning the raw output (exit code NOT asserted).
fn ctx(root: &Path, args: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_ctx"))
        .current_dir(root)
        .args(args)
        .output()
        .unwrap()
}

fn stdout(out: &Output) -> String {
    String::from_utf8(out.stdout.clone()).unwrap()
}

fn stderr(out: &Output) -> String {
    String::from_utf8(out.stderr.clone()).unwrap()
}

fn init(root: &Path) {
    let out = ctx(root, &["init"]);
    assert!(out.status.success(), "ctx init failed: {out:?}");
}

// ----------------------------------------------------------------------------
// C4 root guard
// ----------------------------------------------------------------------------

#[test]
fn root_guard_exits_2_and_names_ctx_init_without_a_context_root() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "a.py", "def a():\n    return 1\n");
    sleep(PAST);

    let out = ctx(root, &["map"]);
    assert_eq!(out.status.code(), Some(2), "no .context/ ancestor exits 2");
    assert!(
        stderr(&out).contains("ctx init"),
        "the guard names `ctx init`: {}",
        stderr(&out)
    );
}

#[test]
fn root_guard_query_succeeds_after_init() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "a.py", "def a():\n    return 1\n");
    sleep(PAST);
    init(root);

    let out = ctx(root, &["map"]);
    assert_eq!(out.status.code(), Some(0), "map succeeds once initialized");
}

// ----------------------------------------------------------------------------
// ctx tree
// ----------------------------------------------------------------------------

const NESTED_PY: &str = "\
class Handler:
    def handle(self):
        return 1


def helper():
    return 2
";

#[test]
fn tree_outlines_containment_with_indentation() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "app.py", NESTED_PY);
    sleep(PAST);
    init(root);

    let out = ctx(root, &["tree", "app.py"]);
    assert_eq!(out.status.code(), Some(0));
    let text = stdout(&out);
    assert!(text.contains("Handler"), "outline names the class: {text}");
    assert!(text.contains("handle"), "outline names the method: {text}");
    assert!(
        text.contains("helper"),
        "outline names the function: {text}"
    );
    // The method is nested more deeply than its containing class.
    let class_indent = indent_of(&text, "Handler");
    let method_indent = indent_of(&text, "handle");
    assert!(
        method_indent > class_indent,
        "the method is indented under its class: {text}"
    );
}

/// Leading-space count of the first line mentioning `needle`.
fn indent_of(text: &str, needle: &str) -> usize {
    let line = text
        .lines()
        .find(|l| l.contains(needle))
        .unwrap_or_else(|| panic!("no line contains {needle:?} in:\n{text}"));
    line.len() - line.trim_start().len()
}

#[test]
fn tree_depth_cap_hides_deeper_symbols() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "app.py", NESTED_PY);
    sleep(PAST);
    init(root);

    let out = ctx(root, &["tree", "app.py", "--depth", "1"]);
    assert_eq!(out.status.code(), Some(0));
    let text = stdout(&out);
    assert!(text.contains("Handler"), "top-level class shown: {text}");
    assert!(
        !text.contains("handle"),
        "the nested method is hidden by --depth 1: {text}"
    );
}

#[test]
fn tree_limit_cap_emits_a_truncation_line_naming_the_flag() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    let mut src = String::new();
    for i in 0..10 {
        src.push_str(&format!("def f{i}():\n    return {i}\n\n\n"));
    }
    write(root, "many.py", &src);
    sleep(PAST);
    init(root);

    let out = ctx(root, &["tree", "many.py", "--limit", "3"]);
    assert_eq!(out.status.code(), Some(0));
    let text = stdout(&out);
    assert!(
        text.contains("more") && text.contains("--limit"),
        "a truncation line names the omitted count and --limit: {text}"
    );
    // 10 functions, limit 3 -> 7 omitted.
    assert!(text.contains('7'), "the omitted count (7) is named: {text}");
}

#[test]
fn tree_doc_appends_first_docstring_line() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(
        root,
        "d.py",
        "def documented():\n    \"\"\"First line.\n\n    More.\n    \"\"\"\n    return 1\n",
    );
    sleep(PAST);
    init(root);

    let plain = stdout(&ctx(root, &["tree", "d.py"]));
    assert!(
        !plain.contains("First line."),
        "the default omits docstrings: {plain}"
    );
    let out = ctx(root, &["tree", "d.py", "--doc"]);
    assert_eq!(out.status.code(), Some(0));
    let doc = stdout(&out);
    assert!(
        doc.contains("First line."),
        "--doc appends the first docstring line: {doc}"
    );
    assert!(
        !doc.contains("More."),
        "--doc appends only the FIRST docstring line: {doc}"
    );
}

#[test]
fn tree_empty_scope_prints_nothing_and_exits_0() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "a.py", "def a():\n    return 1\n");
    sleep(PAST);
    init(root);

    let out = ctx(root, &["tree", "does/not/exist"]);
    assert_eq!(out.status.code(), Some(0), "an empty scope still exits 0");
    assert!(
        stdout(&out).trim().is_empty(),
        "an empty scope prints nothing: {:?}",
        stdout(&out)
    );
}

#[test]
fn tree_marker_plumbing_renders_c10_grammar() {
    // C10 marker rendering (task 09 populates the counts; the grammar is fixed
    // here). The store returns None today, so real output carries no marker.
    assert_eq!(context_tree::cmd::format_note_marker(None), "");
    assert_eq!(
        context_tree::cmd::format_note_marker(Some((3, false))),
        " [notes:3]"
    );
    assert_eq!(
        context_tree::cmd::format_note_marker(Some((2, true))),
        " [notes:2!]"
    );
}

// ----------------------------------------------------------------------------
// ctx sig
// ----------------------------------------------------------------------------

const TWO_HANDLERS: &str = "\
class Handler:
    \"\"\"Handles things.\"\"\"
    pass


class AuthHandler:
    \"\"\"Handles auth.\"\"\"
    pass
";

#[test]
fn sig_default_prints_signature_and_first_docstring_line() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(
        root,
        "app.py",
        "def solo():\n    \"\"\"Only line.\n\n    Detail.\n    \"\"\"\n    return 1\n",
    );
    sleep(PAST);
    init(root);

    let out = ctx(root, &["sig", "solo"]);
    assert_eq!(out.status.code(), Some(0));
    let text = stdout(&out);
    assert!(text.contains("solo"), "signature is printed: {text}");
    assert!(text.contains("Only line."), "first docstring line: {text}");
    assert!(
        !text.contains("Detail."),
        "the default prints only the first docstring line: {text}"
    );
    assert!(
        !text.contains("[notes:"),
        "no note marker until task 09: {text}"
    );
}

#[test]
fn sig_doc_prints_the_full_docstring() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(
        root,
        "app.py",
        "def solo():\n    \"\"\"Only line.\n\n    Detail.\n    \"\"\"\n    return 1\n",
    );
    sleep(PAST);
    init(root);

    let out = ctx(root, &["sig", "solo", "--doc"]);
    assert_eq!(out.status.code(), Some(0));
    let text = stdout(&out);
    assert!(
        text.contains("Only line.") && text.contains("Detail."),
        "--doc prints the full docstring: {text}"
    );
}

#[test]
fn sig_c3_suffix_resolves_to_the_boundary_match_not_a_substring() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "app.py", TWO_HANDLERS);
    sleep(PAST);
    init(root);

    // `Handler` is a `.`-boundary suffix of `app.Handler` only; a substring
    // matcher would ambiguously also hit `app.AuthHandler` and exit 3.
    let out = ctx(root, &["sig", "Handler"]);
    assert_eq!(
        out.status.code(),
        Some(0),
        "suffix match is unambiguous: {}",
        stdout(&out)
    );
    assert!(
        stdout(&out).contains("Handles things."),
        "resolved to app.Handler: {}",
        stdout(&out)
    );
}

#[test]
fn sig_no_match_exits_1() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "app.py", TWO_HANDLERS);
    sleep(PAST);
    init(root);

    let out = ctx(root, &["sig", "Nonexistent"]);
    assert_eq!(out.status.code(), Some(1), "no match exits 1");
}

/// specs/ctx-absence-check R2 (task 01): `sig --json` no-match EXTENDS the
/// existing error object — the legacy `error`/`symbol` keys survive unchanged
/// and `boundary_note`/`suggested_check` are added. The suggested command is
/// brace-free (repeated `--include` flags) and bounded.
#[test]
fn sig_no_match_json_extends_error_object() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "app.py", TWO_HANDLERS);
    sleep(PAST);
    init(root);

    let out = ctx(root, &["sig", "Nonexistent", "--json"]);
    assert_eq!(out.status.code(), Some(1), "no-match exit code unchanged");
    let v: serde_json::Value = serde_json::from_str(&stdout(&out)).unwrap();

    // Legacy keys survive unchanged.
    assert_eq!(
        v["error"].as_str(),
        Some("no match"),
        "legacy error key: {v}"
    );
    assert_eq!(
        v["symbol"].as_str(),
        Some("Nonexistent"),
        "legacy symbol key: {v}"
    );

    // New keys added.
    assert!(
        v["boundary_note"].as_str().is_some(),
        "boundary_note key added: {v}"
    );
    let sc = v["suggested_check"]
        .as_str()
        .unwrap_or_else(|| panic!("suggested_check key added: {v}"));
    assert!(
        sc.contains("grep -rl") && sc.contains("| head -20"),
        "suggested_check is a bounded grep: {sc}"
    );
    assert!(
        !sc.contains('{'),
        "suggested_check uses repeated flags, not a brace pattern: {sc}"
    );
}

/// specs/ctx-absence-check task 05: a `sig --json` no-match whose query is a
/// case variant of an indexed symbol carries the near-miss candidate list in a
/// `did_you_mean` array — JSON/MCP consumers get the same R4 suggestion the
/// text path prints, alongside the unchanged legacy and boundary keys.
#[test]
fn sig_no_match_json_includes_did_you_mean_candidates() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    // Only the camelCase `figureBboxes` is indexed; the query is a case variant.
    write(root, "app.py", "def figureBboxes():\n    return 1\n");
    sleep(PAST);
    init(root);

    let out = ctx(root, &["sig", "FigureBboxes", "--json"]);
    assert_eq!(out.status.code(), Some(1), "case-variant miss exits 1");
    let v: serde_json::Value = serde_json::from_str(&stdout(&out)).unwrap();

    // Legacy + boundary keys still present (parity gap is additive only).
    assert_eq!(
        v["error"].as_str(),
        Some("no match"),
        "legacy error key: {v}"
    );
    assert!(
        v["boundary_note"].as_str().is_some(),
        "boundary_note survives: {v}"
    );

    let cands = v["did_you_mean"]
        .as_array()
        .unwrap_or_else(|| panic!("did_you_mean is a JSON array: {v}"));
    assert!(
        cands.iter().any(|c| c.as_str() == Some("figureBboxes")),
        "the case-variant candidate is listed: {v}"
    );
}

/// specs/ctx-absence-check task 05: a `sig --json` no-match with no near-miss
/// candidate OMITS the `did_you_mean` key entirely — the no-candidate object
/// stays byte-identical to the task-01 R2 shape.
#[test]
fn sig_no_match_json_omits_did_you_mean_when_no_near_miss() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "app.py", "def solo():\n    return 1\n");
    sleep(PAST);
    init(root);

    let out = ctx(root, &["sig", "Zzzznonexistent", "--json"]);
    assert_eq!(out.status.code(), Some(1), "no-match exits 1");
    let v: serde_json::Value = serde_json::from_str(&stdout(&out)).unwrap();

    assert!(
        v.get("did_you_mean").is_none(),
        "no did_you_mean key when nothing is close: {v}"
    );
}

/// specs/ctx-absence-check task 05: the `refs --json` surface carries the same
/// `did_you_mean` array as `sig --json` — both share the no-match path.
#[test]
fn refs_no_match_json_includes_did_you_mean_candidates() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "app.py", "def figureBboxes():\n    return 1\n");
    sleep(PAST);
    init(root);

    let out = ctx(root, &["refs", "FigureBboxes", "--json"]);
    assert_eq!(out.status.code(), Some(1), "case-variant miss exits 1");
    let v: serde_json::Value = serde_json::from_str(&stdout(&out)).unwrap();

    let cands = v["did_you_mean"]
        .as_array()
        .unwrap_or_else(|| panic!("did_you_mean is a JSON array: {v}"));
    assert!(
        cands.iter().any(|c| c.as_str() == Some("figureBboxes")),
        "the case-variant candidate is listed: {v}"
    );
}

#[test]
fn sig_ambiguous_lists_candidates_and_exits_3() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "a.py", "class Handler:\n    pass\n");
    write(root, "b.py", "class Handler:\n    pass\n");
    sleep(PAST);
    init(root);

    let out = ctx(root, &["sig", "Handler"]);
    assert_eq!(out.status.code(), Some(3), "an ambiguous name exits 3");
    let text = stdout(&out);
    assert!(
        text.contains("a.py") && text.contains("b.py"),
        "the candidate list names each file: {text}"
    );
    assert!(
        text.contains("a.Handler") && text.contains("b.Handler"),
        "the candidate list names each qualified path: {text}"
    );
}

// ----------------------------------------------------------------------------
// ctx map
// ----------------------------------------------------------------------------

/// `zeta_used` is called 3 times and sorts LAST alphabetically; `alpha_unused`
/// is never called and sorts FIRST. Reference-graph ranking must invert the
/// alphabetical order.
const RANKED_PY: &str = "\
def zeta_used():
    return 1


def alpha_unused():
    return 2


def c1():
    return zeta_used()


def c2():
    return zeta_used()


def c3():
    return zeta_used()
";

#[test]
fn map_ranking_orders_by_reference_count_not_alphabetical() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "app.py", RANKED_PY);
    sleep(PAST);
    init(root);

    let out = ctx(root, &["map"]);
    assert_eq!(out.status.code(), Some(0));
    let text = stdout(&out);
    let zi = text
        .find("zeta_used")
        .unwrap_or_else(|| panic!("zeta_used absent:\n{text}"));
    let ai = text
        .find("alpha_unused")
        .unwrap_or_else(|| panic!("alpha_unused absent:\n{text}"));
    assert!(
        zi < ai,
        "the referenced symbol ranks above the unreferenced one:\n{text}"
    );
}

/// A real-repo pathology (capability-shakedown finding 2026-07-20): a bash
/// scratch variable reused at top level dedups into `t#1`/`t#2`/`t#3`, and
/// because reference counts are keyed by bare name, every dedup copy inherits
/// the full aggregate count of the common name `t` — crowding real functions
/// out of the top of `ctx map`. Ranking must down-weight `variable`-kind
/// symbols relative to functions/classes/methods so the API surface leads.
const BASH_SCRATCH_NOISE: &str = "\
t=\"a\"
t=\"b\"
t=\"c\"

real_api() {
  echo hi
}

caller() {
  t alpha
  t beta
  t gamma
  t delta
  t epsilon
  real_api
}
";

#[test]
fn map_ranks_functions_above_high_ref_scratch_variables() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "lib.sh", BASH_SCRATCH_NOISE);
    sleep(PAST);
    init(root);

    let out = ctx(root, &["map"]);
    assert_eq!(out.status.code(), Some(0));
    let text = stdout(&out);
    let fi = text
        .find("real_api")
        .unwrap_or_else(|| panic!("real_api absent:\n{text}"));
    let vi = text
        .find("lib.t#1")
        .unwrap_or_else(|| panic!("variable lib.t#1 absent:\n{text}"));
    assert!(
        fi < vi,
        "a function must rank above high-ref-count scratch variables:\n{text}"
    );
}

#[test]
fn map_token_budget_truncates_output() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    let mut src = String::new();
    for i in 0..20 {
        src.push_str(&format!("def f{i}():\n    return {i}\n\n\n"));
    }
    write(root, "many.py", &src);
    sleep(PAST);
    init(root);

    let small = stdout(&ctx(root, &["map", "--tokens", "5"]));
    let big = stdout(&ctx(root, &["map", "--tokens", "100000"]));
    // C7: ceil(bytes/4) <= budget.
    let small_tokens = small.len().div_ceil(4);
    assert!(
        small_tokens <= 5,
        "a --tokens 5 budget bounds the output to <=5 tokens ({small_tokens}): {small:?}"
    );
    assert!(
        small.lines().count() < big.lines().count(),
        "the small budget truncates relative to the large one"
    );
}

#[test]
fn map_doc_appends_first_docstring_lines() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(
        root,
        "d.py",
        "def documented():\n    \"\"\"Doc marker.\"\"\"\n    return 1\n",
    );
    sleep(PAST);
    init(root);

    let plain = stdout(&ctx(root, &["map"]));
    assert!(
        !plain.contains("Doc marker."),
        "default omits docs: {plain}"
    );
    let doc = stdout(&ctx(root, &["map", "--doc"]));
    assert!(
        doc.contains("Doc marker."),
        "--doc appends the first docstring line: {doc}"
    );
}

// ----------------------------------------------------------------------------
// --json variants
// ----------------------------------------------------------------------------

#[test]
fn json_variants_emit_the_asserted_key_per_verb() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "app.py", "def solo():\n    return 1\n");
    sleep(PAST);
    init(root);

    let tree = ctx(root, &["tree", "app.py", "--json"]);
    assert_eq!(tree.status.code(), Some(0));
    let tv: serde_json::Value = serde_json::from_str(&stdout(&tree)).unwrap();
    assert!(tv.get("symbols").is_some(), "tree --json has .symbols");

    let sig = ctx(root, &["sig", "solo", "--json"]);
    assert_eq!(sig.status.code(), Some(0));
    let sv: serde_json::Value = serde_json::from_str(&stdout(&sig)).unwrap();
    assert!(sv.get("signature").is_some(), "sig --json has .signature");

    let map = ctx(root, &["map", "--json"]);
    assert_eq!(map.status.code(), Some(0));
    let mv: serde_json::Value = serde_json::from_str(&stdout(&map)).unwrap();
    assert!(mv.get("symbols").is_some(), "map --json has .symbols");
}

// ----------------------------------------------------------------------------
// Rebuild equivalence (C4, CUJ11)
// ----------------------------------------------------------------------------

const EQUIV_PY: &str = "\
class Handler:
    \"\"\"Handles.\"\"\"
    def handle(self):
        return other()


def other():
    return 1
";

fn cache_dir(root: &Path) -> std::path::PathBuf {
    root.join(".context").join("cache")
}

fn journal_last_parsed(root: &Path) -> u64 {
    let text = std::fs::read_to_string(cache_dir(root).join("sync-journal.jsonl")).unwrap();
    let last = text.lines().rfind(|l| !l.trim().is_empty()).unwrap();
    let v: serde_json::Value = serde_json::from_str(last).unwrap();
    v["parsed"].as_u64().unwrap()
}

#[test]
fn rebuild_equivalence_byte_identical_after_cache_delete() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "app.py", EQUIV_PY);
    sleep(PAST);
    init(root);

    let before_map = stdout(&ctx(root, &["map"]));
    let before_tree = stdout(&ctx(root, &["tree", "app.py"]));
    let before_sig = stdout(&ctx(root, &["sig", "Handler"]));

    std::fs::remove_dir_all(cache_dir(root)).unwrap();
    sleep(PAST);

    let after_map = stdout(&ctx(root, &["map"]));
    let after_tree = stdout(&ctx(root, &["tree", "app.py"]));
    let after_sig = stdout(&ctx(root, &["sig", "Handler"]));

    assert_eq!(before_map, after_map, "map output is rebuild-stable");
    assert_eq!(before_tree, after_tree, "tree output is rebuild-stable");
    assert_eq!(before_sig, after_sig, "sig output is rebuild-stable");
}

#[test]
fn rebuild_equivalence_transparent_rebuild_on_tampered_schema_version() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(root, "app.py", EQUIV_PY);
    write(root, "other.py", "def z():\n    return 1\n");
    sleep(PAST);
    init(root);

    // Prime the index.
    let _ = ctx(root, &["map"]);

    // Tamper the persisted schema version so the next open must rebuild (C4).
    {
        let conn = rusqlite::Connection::open(cache_dir(root).join("index.sqlite")).unwrap();
        conn.execute("UPDATE schema_meta SET version = 999", [])
            .unwrap();
    }
    sleep(PAST);

    let out = ctx(root, &["map"]);
    assert_eq!(out.status.code(), Some(0), "the query still succeeds");
    // A transparent rebuild re-parses every indexed file.
    let indexed = 2;
    assert_eq!(
        journal_last_parsed(root),
        indexed,
        "the post-tamper sweep re-parsed the full indexed file count"
    );
}

// ----------------------------------------------------------------------------
// file-scoped selector `<path>:<name>` + `--in <path-prefix>` (R1, task 02)
// ----------------------------------------------------------------------------

/// Two `package main` Go files in different directories both defining a
/// package-level `rodSpecs` — the collision C1 alone cannot resolve, since the
/// Go module component is the package name so both symbols carry the qualified
/// path `main.rodSpecs`.
const RODSPECS_A: &str = "package main\n\nvar rodSpecs = 1\n";
const RODSPECS_B: &str = "package main\n\nvar rodSpecs = 2\n";

fn two_rodspecs(root: &Path) {
    write(root, "go/cmd/mlhybrid/main.go", RODSPECS_A);
    write(root, "go/cmd/mloverlay/main.go", RODSPECS_B);
    sleep(PAST);
    init(root);
}

#[test]
fn selector_bare_form_is_ambiguous_but_file_scoped_form_resolves_uniquely_for_sig() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    two_rodspecs(root);

    // The bare qpath suffix cannot pick a file — exit 3.
    let bare = ctx(root, &["sig", "rodSpecs"]);
    assert_eq!(
        bare.status.code(),
        Some(3),
        "the bare collision is ambiguous: {}",
        stdout(&bare)
    );

    // The file-scoped `<path>:<name>` form narrows to exactly one — exit 0.
    let scoped = ctx(root, &["sig", "go/cmd/mlhybrid/main.go:rodSpecs"]);
    assert_eq!(
        scoped.status.code(),
        Some(0),
        "the file-scoped selector resolves uniquely: {} / {}",
        stdout(&scoped),
        stderr(&scoped)
    );
}

#[test]
fn selector_in_prefix_flag_disambiguates_the_collision_for_sig() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    two_rodspecs(root);

    let out = ctx(root, &["sig", "rodSpecs", "--in", "go/cmd/mlhybrid"]);
    assert_eq!(
        out.status.code(),
        Some(0),
        "--in narrows the candidate set to one file: {} / {}",
        stdout(&out),
        stderr(&out)
    );
}

#[test]
fn selector_file_scoped_form_resolves_uniquely_for_show() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    two_rodspecs(root);

    assert_eq!(ctx(root, &["show", "rodSpecs"]).status.code(), Some(3));
    let out = ctx(root, &["show", "go/cmd/mloverlay/main.go:rodSpecs"]);
    assert_eq!(
        out.status.code(),
        Some(0),
        "show resolves the file-scoped selector: {} / {}",
        stdout(&out),
        stderr(&out)
    );
    assert!(
        stdout(&out).contains("rodSpecs"),
        "show prints the selected symbol's span: {}",
        stdout(&out)
    );
}

#[test]
fn selector_file_scoped_form_resolves_uniquely_for_refs() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    two_rodspecs(root);

    let out = ctx(root, &["refs", "go/cmd/mlhybrid/main.go:rodSpecs"]);
    assert_eq!(
        out.status.code(),
        Some(0),
        "refs resolves the file-scoped selector: {} / {}",
        stdout(&out),
        stderr(&out)
    );
    let def_lines = stdout(&out)
        .lines()
        .filter(|l| l.starts_with("def "))
        .count();
    assert_eq!(
        def_lines,
        1,
        "exactly one definition survives the file filter: {}",
        stdout(&out)
    );
    assert!(
        stdout(&out).contains("go/cmd/mlhybrid/main.go"),
        "the surviving def is from the named file: {}",
        stdout(&out)
    );
}

#[test]
fn selector_file_scoped_form_resolves_uniquely_for_notes() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    two_rodspecs(root);

    // Bare add is ambiguous (exit 3); the file-scoped anchor resolves.
    assert_eq!(
        ctx(root, &["notes", "add", "rodSpecs", "body"])
            .status
            .code(),
        Some(3),
        "the bare anchor is ambiguous"
    );
    let add = ctx(
        root,
        &["notes", "add", "go/cmd/mlhybrid/main.go:rodSpecs", "body"],
    );
    assert_eq!(
        add.status.code(),
        Some(0),
        "notes add resolves the file-scoped anchor: {} / {}",
        stdout(&add),
        stderr(&add)
    );
    let show = ctx(root, &["notes", "go/cmd/mlhybrid/main.go:rodSpecs"]);
    assert_eq!(
        show.status.code(),
        Some(0),
        "notes show resolves the file-scoped selector: {} / {}",
        stdout(&show),
        stderr(&show)
    );
    assert!(
        stdout(&show).contains("body"),
        "notes show prints the note anchored under that file: {}",
        stdout(&show)
    );
}

#[test]
fn ambiguity_listing_gains_a_per_candidate_file_scoped_rerun_hint() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    two_rodspecs(root);

    let out = ctx(root, &["sig", "rodSpecs"]);
    assert_eq!(
        out.status.code(),
        Some(3),
        "still ambiguous: {}",
        stdout(&out)
    );
    let text = stdout(&out);
    // Each candidate now shows the file-scoped form to rerun with. The `:rodSpecs`
    // suffix distinguishes the hint from the existing `<file>:<line>` locator.
    assert!(
        text.contains("go/cmd/mlhybrid/main.go:rodSpecs"),
        "rerun hint for candidate A: {text}"
    );
    assert!(
        text.contains("go/cmd/mloverlay/main.go:rodSpecs"),
        "rerun hint for candidate B: {text}"
    );
}

#[test]
fn ambiguity_json_carries_a_per_candidate_rerun_selector() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    two_rodspecs(root);

    let out = ctx(root, &["sig", "rodSpecs", "--json"]);
    assert_eq!(out.status.code(), Some(3));
    let v: serde_json::Value = serde_json::from_str(&stdout(&out)).unwrap();
    let candidates = v["candidates"].as_array().expect("candidates array");
    let reruns: Vec<&str> = candidates
        .iter()
        .filter_map(|c| c["rerun"].as_str())
        .collect();
    assert!(
        reruns.contains(&"go/cmd/mlhybrid/main.go:rodSpecs")
            && reruns.contains(&"go/cmd/mloverlay/main.go:rodSpecs"),
        "each candidate carries its file-scoped rerun selector: {v}"
    );
}
