//! `ctx tree <path>` — a containment outline for a path subtree (R6), with a
//! depth cap, a result cap plus truncation line, `--doc`, and C10 markers.

use crate::cmd::{first_doc_line, format_note_marker, load_index, note_value};
use crate::index::{IndexStore, SymbolRow};
use serde_json::json;
use std::collections::HashMap;
use std::process::ExitCode;

/// Parsed `ctx tree` arguments.
pub struct Args {
    pub path: String,
    pub files: bool,
    pub depth: Option<usize>,
    pub limit: usize,
    pub doc: bool,
    pub json: bool,
    pub no_sync: bool,
}

/// Does the indexed file `path` fall within the requested `scope`? A scope of
/// `.` (or empty) matches everything; otherwise an exact path or a `<scope>/…`
/// directory prefix matches.
fn in_scope(path: &str, scope: &str) -> bool {
    let scope = scope.strip_prefix("./").unwrap_or(scope);
    if scope.is_empty() || scope == "." {
        return true;
    }
    path == scope || path.starts_with(&format!("{scope}/"))
}

/// Directory-level depth of an indexed file `path` relative to the query
/// `scope`, 1-based: a file directly in `scope` is depth 1, one subdirectory
/// down is depth 2, and so on. Measured from the query path, never the index
/// root. Assumes `path` is already in scope (see [`in_scope`]).
fn file_depth(path: &str, scope: &str) -> usize {
    let scope = scope.strip_prefix("./").unwrap_or(scope);
    let rel = if scope.is_empty() || scope == "." {
        path
    } else if path == scope {
        // The scope names this exact file: it sits at the query path itself.
        return 1;
    } else {
        // in_scope guarantees `path` starts with `scope/`.
        &path[scope.len() + 1..]
    };
    1 + rel.matches('/').count()
}

/// Containment depth (0 = top-level) via the C1 parent chain, bounded so a
/// malformed cycle can never loop forever.
fn depth_of(sym: &SymbolRow, by_qpath: &HashMap<&str, &SymbolRow>) -> usize {
    let mut depth = 0;
    let mut cursor = sym.parent.as_deref();
    while let Some(parent) = cursor {
        if depth > 256 {
            break;
        }
        match by_qpath.get(parent) {
            Some(p) => {
                depth += 1;
                cursor = p.parent.as_deref();
            }
            None => break,
        }
    }
    depth
}

pub fn run(args: Args) -> ExitCode {
    let (out, code) = render(&args);
    print!("{out}");
    code
}

/// The exact stdout `run` would print, paired with the exit code. The MCP
/// wrapper (R15) calls this so it never reimplements the query and never writes
/// to the server's JSON-RPC stdout channel; error diagnostics still go to
/// stderr via `eprintln!`.
pub fn render(args: &Args) -> (String, ExitCode) {
    let (_root, store) = match load_index(args.no_sync) {
        Ok(v) => v,
        Err(code) => return (String::new(), code),
    };

    if args.files {
        return render_files(args, &store);
    }

    let all = match store.all_symbols() {
        Ok(v) => v,
        Err(e) => {
            eprintln!("ctx tree: {e}");
            return (String::new(), ExitCode::FAILURE);
        }
    };
    let by_qpath: HashMap<&str, &SymbolRow> = all.iter().map(|s| (s.qpath.as_str(), s)).collect();

    // Symbols within the requested scope, passing the depth cap, in the index's
    // deterministic (path, source) order.
    let selected: Vec<(&SymbolRow, usize)> = all
        .iter()
        .filter(|s| in_scope(&s.path, &args.path))
        .map(|s| (s, depth_of(s, &by_qpath)))
        .filter(|(_, d)| args.depth.is_none_or(|cap| *d < cap))
        .collect();

    let shown = selected.iter().take(args.limit);
    let omitted = selected.len().saturating_sub(args.limit);

    // Minified-skipped candidates in scope, path-ordered (R2). A skipped file
    // has zero symbols, so it never appears among `selected`; tree lists it
    // with a marker so a skip never reads as absence.
    let skipped: Vec<(String, String)> = match store.skipped_paths() {
        Ok(v) => v
            .into_iter()
            .filter(|(p, _)| in_scope(p, &args.path))
            .collect(),
        Err(e) => {
            eprintln!("ctx tree: {e}");
            return (String::new(), ExitCode::FAILURE);
        }
    };

    if args.json {
        return (
            render_json(args, &store, shown, omitted, &skipped),
            ExitCode::SUCCESS,
        );
    }

    let mut out = String::new();
    let mut current_file: Option<&str> = None;
    let mut si = 0; // next skipped candidate to emit, interleaved in path order
    for (sym, depth) in shown {
        if current_file != Some(sym.path.as_str()) {
            while si < skipped.len() && skipped[si].0.as_str() < sym.path.as_str() {
                out.push_str(&skipped[si].0);
                out.push_str(&skip_marker(&skipped[si].1));
                out.push('\n');
                si += 1;
            }
            out.push_str(&sym.path);
            out.push('\n');
            current_file = Some(sym.path.as_str());
        }
        out.push_str(&"  ".repeat(depth + 1));
        out.push_str(&sym.kind);
        out.push(' ');
        out.push_str(&sym.name);
        out.push_str(&format_note_marker(store.note_marker(sym.id)));
        if args.doc
            && let Some(line) = first_doc_line(&sym.docstring)
        {
            out.push_str(" — ");
            out.push_str(line);
        }
        out.push('\n');
    }
    // Skipped candidates sorting after the last symbol-bearing file.
    while si < skipped.len() {
        out.push_str(&skipped[si].0);
        out.push_str(&skip_marker(&skipped[si].1));
        out.push('\n');
        si += 1;
    }
    if omitted > 0 {
        out.push_str(&format!("... {omitted} more (raise --limit)\n"));
    }
    (out, ExitCode::SUCCESS)
}

/// The trailing marker for a skipped-file line: the reason's category (the part
/// before the first `-`, so `minified-name` and `minified-content` both render
/// as the single `(skipped: minified)` output class R2 specifies).
fn skip_marker(reason: &str) -> String {
    let category = reason.split('-').next().unwrap_or(reason);
    format!(" (skipped: {category})")
}

/// `--files` mode: the indexed file paths under `args.path`, one per line (or a
/// JSON array with `--json`), filtered by the directory-level `--depth` cap. No
/// symbol lines — this answers "which files are under X" directly, so the
/// emitted count equals the index's file membership under the path.
fn render_files(args: &Args, store: &IndexStore) -> (String, ExitCode) {
    let paths = match store.indexed_paths() {
        Ok(v) => v,
        Err(e) => {
            eprintln!("ctx tree: {e}");
            return (String::new(), ExitCode::FAILURE);
        }
    };
    let selected: Vec<&str> = paths
        .iter()
        .map(String::as_str)
        .filter(|p| in_scope(p, &args.path))
        .filter(|p| {
            args.depth
                .is_none_or(|cap| file_depth(p, &args.path) <= cap)
        })
        .collect();

    if args.json {
        return (format!("{}\n", json!(selected)), ExitCode::SUCCESS);
    }
    let mut out = String::new();
    for p in selected {
        out.push_str(p);
        out.push('\n');
    }
    (out, ExitCode::SUCCESS)
}

fn render_json<'a>(
    args: &Args,
    store: &IndexStore,
    shown: impl Iterator<Item = &'a (&'a SymbolRow, usize)>,
    omitted: usize,
    skipped: &[(String, String)],
) -> String {
    let symbols: Vec<serde_json::Value> = shown
        .map(|(sym, depth)| {
            json!({
                "qpath": sym.qpath,
                "kind": sym.kind,
                "name": sym.name,
                "file": sym.path,
                "depth": depth,
                "signature": sym.signature,
                "docstring": if args.doc { sym.docstring.clone() } else { String::new() },
                "notes": note_value(store, sym.id),
            })
        })
        .collect();
    let skipped_json: Vec<serde_json::Value> = skipped
        .iter()
        .map(|(path, reason)| {
            json!({
                "path": path,
                "reason": reason,
                "marker": skip_marker(reason).trim(),
            })
        })
        .collect();
    let payload = json!({
        "path": args.path,
        "truncated": omitted,
        "symbols": symbols,
        "skipped": skipped_json,
    });
    format!("{payload}\n")
}
