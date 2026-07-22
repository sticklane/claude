//! R11 / task 08 (and task 01 / R2's `--exact` extension) integration tests
//! for optional, additive LSP enrichment.
//!
//! `refs_no_lsp` is the regression guard: with no enrichment cache, `ctx refs`
//! still returns `heuristic` results and exits 0 (task 07's baseline). It always
//! runs.
//!
//! `refs_lsp_precise` drives the full enrich -> cache -> `ctx refs` pipeline
//! through a test double for "a configured language server available" and asserts
//! a `precise` result appears. It is deterministic and always runs.
//!
//! `refs_exact_no_server_matches_plain_refs` (task 01) is `--exact`'s
//! regression guard: with no enrichment cache and no server binary on `PATH`,
//! `ctx refs --exact <symbol>` is byte-identical to plain `ctx refs <symbol>`.
//!
//! `refs_exact_disambiguates_same_name_across_packages` (task 01 / R2) is the
//! golden disambiguation test: two definitions sharing one name in different
//! packages (the `main.rodSpecs`-style ambiguity R2 names) — with a resolver
//! available, `--exact` attributes each reference to the correct definition
//! rather than mixing them under one heuristic name match.
//!
//! `refs_lsp_precise_live` exercises the full `enrich` -> cache -> `ctx refs`
//! pipeline against a real `rust-analyzer`, and `refs_exact_live` exercises
//! the newer `ctx refs --exact` on-demand trigger against the same server.
//! Both are slow external dependencies, so — per the project's TDD rules
//! ("mock only slow/external dependencies") — they are `#[ignore]`d out of
//! the default suite and run explicitly with `cargo test refs_lsp_precise_live
//! -- --ignored` / `cargo test refs_exact_live -- --ignored`.

use context_tree::lsp::client::RustAnalyzerResolver;
use context_tree::lsp::{ReferenceResolver, ResolveTarget, Resolved, enrich};
use std::path::Path;
use std::process::{Command, Output};
use std::thread::sleep;
use std::time::Duration;

const PAST: Duration = Duration::from_millis(250);

fn write(root: &Path, rel: &str, content: &str) {
    let p = root.join(rel);
    if let Some(parent) = p.parent() {
        std::fs::create_dir_all(parent).unwrap();
    }
    std::fs::write(p, content).unwrap();
}

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

fn init(root: &Path) {
    let out = ctx(root, &["init"]);
    assert!(out.status.success(), "ctx init failed: {out:?}");
}

/// A test double for "a configured language server available": it confirms every
/// heuristic candidate as precise and attaches a signature — the deterministic
/// stand-in the enrichment trait was designed to admit.
struct FakeServer;

impl ReferenceResolver for FakeServer {
    fn resolve(&self, _root: &Path, target: &ResolveTarget) -> std::io::Result<Resolved> {
        Ok(Resolved {
            refs: target.candidates.clone(),
            signature: Some(format!("resolved:{}", target.name)),
        })
    }
}

#[test]
fn refs_no_lsp() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(
        root,
        "app.py",
        "def target():\n    return 1\n\n\ndef caller():\n    return target()\n",
    );
    sleep(PAST);
    init(root);

    // No enrichment cache exists: results are heuristic and the command exits 0.
    let out = ctx(root, &["refs", "target"]);
    assert_eq!(
        out.status.code(),
        Some(0),
        "refs exits 0 with no LSP: {out:?}"
    );
    let text = stdout(&out);
    assert!(
        text.contains("heuristic"),
        "results stay heuristic with no server configured: {text}"
    );
    assert!(
        !text.contains("precise"),
        "nothing is precise without enrichment: {text}"
    );
}

#[test]
fn refs_lsp_precise() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(
        root,
        "app.py",
        "def target():\n    return 1\n\n\ndef caller():\n    return target()\n",
    );
    sleep(PAST);
    init(root);

    // Run the enrichment pass with a configured server (the test double).
    let cache = enrich(root, &FakeServer).expect("enrichment writes a cache");
    assert!(!cache.is_empty(), "the pass recorded precise data");

    // ctx refs now consults the cache and upgrades a result to precise.
    let out = ctx(root, &["refs", "target"]);
    assert_eq!(out.status.code(), Some(0), "refs still exits 0: {out:?}");
    let text = stdout(&out);
    assert!(
        text.contains("precise"),
        "with a configured server, at least one result is precise: {text}"
    );
    assert!(
        text.lines()
            .any(|l| l.starts_with("ref") && l.contains("precise")),
        "the reference is upgraded to precise: {text}"
    );
}

#[test]
fn enrich_load_roundtrips_precise_refs() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(
        root,
        "app.py",
        "def target():\n    return 1\n\n\ndef caller():\n    return target()\n",
    );
    sleep(PAST);
    init(root);

    enrich(root, &FakeServer).unwrap();
    let loaded = context_tree::lsp::EnrichmentCache::load(root).expect("cache loads back");
    assert!(
        loaded.is_precise("target", "app.py", 6),
        "the call-site reference (app.py:6) is recorded precise: {loaded:?}"
    );
    assert_eq!(
        loaded.signature("app.target"),
        Some("resolved:target"),
        "the resolved signature is stored under the symbol's qpath: {loaded:?}"
    );
}

#[test]
fn refs_exact_no_server_matches_plain_refs() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(
        root,
        "app.py",
        "def target():\n    return 1\n\n\ndef caller():\n    return target()\n",
    );
    sleep(PAST);
    init(root);

    // No cache exists and no LSP server binary is on PATH in this sandboxed
    // test environment: `--exact` must fall through to the exact same output
    // as plain `ctx refs` (task 01's Steps 4 "no available server, fall
    // through to the existing heuristic path unchanged").
    let plain = stdout(&ctx(root, &["refs", "target"]));
    let exact = stdout(&ctx(root, &["refs", "--exact", "target"]));
    assert_eq!(
        plain, exact,
        "with no LSP server available, --exact is byte-identical to plain refs"
    );
}

/// A resolver test double that disambiguates by package: it confirms a
/// candidate reference as precise only when it shares the queried
/// definition's own top-level directory — modelling what a real LSP server's
/// definition-scoped `references` call returns for two same-named symbols
/// defined in different packages (R2's motivating `main.rodSpecs`-in-
/// `go/cmd/mlhybrid`-vs-`attic/go-cmd/mloverlay` case).
struct DisambiguatingFakeServer;

impl ReferenceResolver for DisambiguatingFakeServer {
    fn resolve(&self, _root: &Path, target: &ResolveTarget) -> std::io::Result<Resolved> {
        let own_pkg = target.file.split('/').next().unwrap_or("");
        let refs = target
            .candidates
            .iter()
            .filter(|c| c.path.split('/').next() == Some(own_pkg))
            .cloned()
            .collect();
        Ok(Resolved {
            refs,
            signature: None,
        })
    }
}

#[test]
fn refs_exact_disambiguates_same_name_across_packages() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    // Two packages, each defining `rodSpecs` and calling its own — the
    // ambiguity a bare heuristic name match cannot tell apart (R2).
    write(
        root,
        "pkg_a/mod.py",
        "def rodSpecs():\n    return 1\n\n\ndef caller_a():\n    return rodSpecs()\n",
    );
    write(
        root,
        "pkg_b/mod.py",
        "def rodSpecs():\n    return 2\n\n\ndef caller_b():\n    return rodSpecs()\n",
    );
    sleep(PAST);
    init(root);

    // Pre-populate the enrichment cache the way `--exact`'s on-demand trigger
    // would (same `enrich` entry point, same generation stamping) — using the
    // disambiguating double in place of a real server so the test stays
    // deterministic.
    let cache = enrich(root, &DisambiguatingFakeServer).expect("enrichment writes a cache");
    assert!(!cache.is_empty(), "the pass recorded precise data");

    let out = ctx(root, &["refs", "--exact", "rodSpecs"]);
    assert_eq!(out.status.code(), Some(0), "refs --exact exits 0: {out:?}");
    let text = stdout(&out);

    let pkg_a_line = text
        .lines()
        .find(|l| l.starts_with("ref") && l.contains("pkg_a/mod.py"))
        .unwrap_or_else(|| panic!("no ref line for pkg_a/mod.py: {text}"));
    let pkg_b_line = text
        .lines()
        .find(|l| l.starts_with("ref") && l.contains("pkg_b/mod.py"))
        .unwrap_or_else(|| panic!("no ref line for pkg_b/mod.py: {text}"));

    assert!(
        pkg_a_line.contains("precise") && pkg_a_line.contains("pkg_a.mod.rodSpecs"),
        "pkg_a's reference is attributed to pkg_a's own definition: {pkg_a_line}"
    );
    assert!(
        !pkg_a_line.contains("pkg_b.mod.rodSpecs"),
        "pkg_a's reference is NOT attributed to pkg_b's definition: {pkg_a_line}"
    );
    assert!(
        pkg_b_line.contains("precise") && pkg_b_line.contains("pkg_b.mod.rodSpecs"),
        "pkg_b's reference is attributed to pkg_b's own definition: {pkg_b_line}"
    );
    assert!(
        !pkg_b_line.contains("pkg_a.mod.rodSpecs"),
        "pkg_b's reference is NOT attributed to pkg_a's definition: {pkg_b_line}"
    );
}

/// Live end-to-end against a real rust-analyzer. `#[ignore]`d out of the default
/// suite (slow external dependency); run with `-- --ignored`.
#[test]
#[ignore]
fn refs_lsp_precise_live() {
    if !RustAnalyzerResolver::available() {
        eprintln!(
            "SKIP refs_lsp_precise_live: no language server ({}) on PATH",
            RustAnalyzerResolver::server_binary()
        );
        return;
    }
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(
        root,
        "Cargo.toml",
        "[package]\nname = \"fixture\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n[[bin]]\nname = \"fixture\"\npath = \"src/main.rs\"\n",
    );
    write(
        root,
        "src/main.rs",
        "fn target() -> i32 {\n    1\n}\n\nfn main() {\n    let _ = target();\n    let _ = target();\n}\n",
    );
    sleep(PAST);
    init(root);

    let cache = enrich(root, &RustAnalyzerResolver).expect("enrichment runs");
    assert!(
        !cache.is_empty(),
        "rust-analyzer confirmed at least one precise reference"
    );

    let out = ctx(root, &["refs", "target"]);
    assert_eq!(out.status.code(), Some(0), "refs exits 0: {out:?}");
    let text = stdout(&out);
    assert!(
        text.contains("precise"),
        "with rust-analyzer available, a result is precise: {text}"
    );
}

/// Live end-to-end of the NEWER `ctx refs --exact` on-demand trigger (task
/// 01): unlike [`refs_lsp_precise_live`] above, this never calls `enrich`
/// directly — it exercises `--exact`'s own auto-trigger path against a real
/// rust-analyzer. `#[ignore]`d out of the default suite (slow external
/// dependency); run with `-- --ignored`.
#[test]
#[ignore]
fn refs_exact_live() {
    if !RustAnalyzerResolver::available() {
        eprintln!(
            "SKIP refs_exact_live: no language server ({}) on PATH",
            RustAnalyzerResolver::server_binary()
        );
        return;
    }
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    write(
        root,
        "Cargo.toml",
        "[package]\nname = \"fixture\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n[[bin]]\nname = \"fixture\"\npath = \"src/main.rs\"\n",
    );
    write(
        root,
        "src/main.rs",
        "fn target() -> i32 {\n    1\n}\n\nfn main() {\n    let _ = target();\n    let _ = target();\n}\n",
    );
    sleep(PAST);
    init(root);

    // No `enrich` call here — `--exact` alone must trigger it on demand.
    let out = ctx(root, &["refs", "--exact", "target"]);
    assert_eq!(out.status.code(), Some(0), "refs --exact exits 0: {out:?}");
    let text = stdout(&out);
    assert!(
        text.contains("precise"),
        "with rust-analyzer available, --exact upgrades a result to precise: {text}"
    );
}
