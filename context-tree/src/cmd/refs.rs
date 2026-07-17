//! `ctx refs <symbol> [--limit N]` — definitions and references for a symbol
//! resolved by C3 suffix (R10). Each result is labeled `heuristic` (this task
//! ships no LSP pass, so `precise` is never emitted — R11/task 08 upgrades
//! matches). Heuristic matching is scope-aware where the grammar has locals
//! queries: a reference bound to a function-local definition of the same name
//! is excluded from the cross-file candidate set. Results cap at `--limit`
//! (default 50) per direction with a truncation line naming the flag.

use crate::cmd::{EXIT_AMBIGUOUS, EXIT_NO_MATCH, format_note_marker, load_index, note_value};
use crate::index::{IndexStore, RefRow, ScopeRow, SymbolRow};
use crate::path::resolve_suffix;
use serde_json::json;
use std::collections::HashSet;
use std::path::Path;
use std::process::ExitCode;

/// Parsed `ctx refs` arguments.
pub struct Args {
    pub symbol: String,
    pub limit: usize,
    pub json: bool,
    pub no_sync: bool,
}

/// 1-based line of `byte` within the file at `root/rel`; 1 when the source can't
/// be read (the listing degrades rather than fails).
fn line_of(root: &Path, rel: &str, byte: usize) -> usize {
    match std::fs::read(root.join(rel)) {
        Ok(bytes) => {
            bytes[..byte.min(bytes.len())]
                .iter()
                .filter(|&&b| b == b'\n')
                .count()
                + 1
        }
        Err(_) => 1,
    }
}

/// A reference is a shadowed local when a same-named locals-query scope binding
/// in the same file encloses its byte position — languages without locals
/// queries emit no scopes, so this is a no-op fallback to plain name matching.
fn is_shadowed(rf: &RefRow, scopes: &[ScopeRow]) -> bool {
    scopes.iter().any(|s| {
        s.name == rf.name
            && s.path == rf.path
            && rf.byte >= s.scope_start_byte
            && rf.byte < s.scope_end_byte
    })
}

pub fn run(args: Args) -> ExitCode {
    let (root, store) = match load_index(args.no_sync) {
        Ok(v) => v,
        Err(code) => return code,
    };
    let all = match store.all_symbols() {
        Ok(v) => v,
        Err(e) => {
            eprintln!("ctx refs: {e}");
            return ExitCode::FAILURE;
        }
    };

    // Resolve <symbol> per C3: exact/suffix over qualified paths.
    let qpaths: Vec<String> = all.iter().map(|s| s.qpath.clone()).collect();
    let matched: HashSet<&str> = resolve_suffix(&qpaths, &args.symbol).into_iter().collect();
    let mut defs: Vec<&SymbolRow> = all
        .iter()
        .filter(|s| matched.contains(s.qpath.as_str()))
        .collect();
    defs.sort_by(|a, b| a.qpath.cmp(&b.qpath));

    let names: HashSet<&str> = defs.iter().map(|d| d.name.as_str()).collect();
    match names.len() {
        0 => {
            if args.json {
                println!("{}", json!({ "error": "no match", "symbol": args.symbol }));
            } else {
                eprintln!("ctx refs: no symbol matches '{}'", args.symbol);
            }
            return ExitCode::from(EXIT_NO_MATCH);
        }
        1 => {}
        _ => {
            // C3: a suffix spanning several distinct symbols is ambiguous.
            if args.json {
                let candidates: Vec<_> = defs.iter().map(|d| json!(d.qpath)).collect();
                println!(
                    "{}",
                    json!({ "error": "ambiguous", "symbol": args.symbol, "candidates": candidates })
                );
            } else {
                eprintln!("ctx refs: '{}' is ambiguous — candidates:", args.symbol);
                for d in &defs {
                    println!("{}", d.qpath);
                }
            }
            return ExitCode::from(EXIT_AMBIGUOUS);
        }
    }
    let target_name = *names.iter().next().unwrap();

    let all_refs = match store.all_references() {
        Ok(v) => v,
        Err(e) => {
            eprintln!("ctx refs: {e}");
            return ExitCode::FAILURE;
        }
    };
    let scopes = match store.all_scopes() {
        Ok(v) => v,
        Err(e) => {
            eprintln!("ctx refs: {e}");
            return ExitCode::FAILURE;
        }
    };
    let refs: Vec<&RefRow> = all_refs
        .iter()
        .filter(|r| r.name == target_name && !is_shadowed(r, &scopes))
        .collect();

    let def_shown = defs.len().min(args.limit);
    let ref_shown = refs.len().min(args.limit);
    let def_omitted = defs.len() - def_shown;
    let ref_omitted = refs.len() - ref_shown;

    if args.json {
        return render_json(&args, &store, &root, &defs, &refs, def_omitted, ref_omitted);
    }

    let mut out = String::new();
    for d in defs.iter().take(def_shown) {
        let marker = format_note_marker(store.note_marker(d.id));
        out.push_str(&format!(
            "def {} {}:{} heuristic{}\n",
            d.qpath,
            d.path,
            line_of(&root, &d.path, d.ident_start_byte),
            marker,
        ));
    }
    if def_omitted > 0 {
        out.push_str(&format!(
            "... {def_omitted} more definitions (raise --limit)\n"
        ));
    }
    for r in refs.iter().take(ref_shown) {
        out.push_str(&format!(
            "ref {} {}:{} heuristic\n",
            r.name,
            r.path,
            r.row + 1,
        ));
    }
    if ref_omitted > 0 {
        out.push_str(&format!(
            "... {ref_omitted} more references (raise --limit)\n"
        ));
    }
    print!("{out}");
    ExitCode::SUCCESS
}

#[allow(clippy::too_many_arguments)]
fn render_json(
    args: &Args,
    store: &IndexStore,
    root: &Path,
    defs: &[&SymbolRow],
    refs: &[&RefRow],
    def_omitted: usize,
    ref_omitted: usize,
) -> ExitCode {
    let definitions: Vec<_> = defs
        .iter()
        .take(args.limit)
        .map(|d| {
            json!({
                "qpath": d.qpath,
                "file": d.path,
                "line": line_of(root, &d.path, d.ident_start_byte),
                "label": "heuristic",
                "notes": note_value(store, d.id),
            })
        })
        .collect();
    let references: Vec<_> = refs
        .iter()
        .take(args.limit)
        .map(|r| {
            json!({
                "name": r.name,
                "file": r.path,
                "line": r.row + 1,
                "kind": r.kind,
                "label": "heuristic",
            })
        })
        .collect();
    println!(
        "{}",
        json!({
            "symbol": args.symbol,
            "definitions": definitions,
            "references": references,
            "truncated": { "definitions": def_omitted, "references": ref_omitted },
        })
    );
    ExitCode::SUCCESS
}
