//! `ctx tree <path>` — a containment outline for a path subtree (R6), with a
//! depth cap, a result cap plus truncation line, `--doc`, and C10 markers.

use crate::cmd::{first_doc_line, format_note_marker, load_index};
use crate::index::{IndexStore, SymbolRow};
use serde_json::json;
use std::collections::HashMap;
use std::process::ExitCode;

/// Parsed `ctx tree` arguments.
pub struct Args {
    pub path: String,
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
    let (_root, store) = match load_index(args.no_sync) {
        Ok(v) => v,
        Err(code) => return code,
    };
    let all = match store.all_symbols() {
        Ok(v) => v,
        Err(e) => {
            eprintln!("ctx tree: {e}");
            return ExitCode::FAILURE;
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

    if args.json {
        return render_json(&args, &store, shown, omitted);
    }

    let mut out = String::new();
    let mut current_file: Option<&str> = None;
    for (sym, depth) in shown {
        if current_file != Some(sym.path.as_str()) {
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
    if omitted > 0 {
        out.push_str(&format!("... {omitted} more (raise --limit)\n"));
    }
    print!("{out}");
    ExitCode::SUCCESS
}

fn render_json<'a>(
    args: &Args,
    store: &IndexStore,
    shown: impl Iterator<Item = &'a (&'a SymbolRow, usize)>,
    omitted: usize,
) -> ExitCode {
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
    let payload = json!({
        "path": args.path,
        "truncated": omitted,
        "symbols": symbols,
    });
    println!("{payload}");
    ExitCode::SUCCESS
}

/// The C10 note tuple as JSON: `null` until task 09 populates notes.
pub fn note_value(store: &IndexStore, symbol_id: i64) -> serde_json::Value {
    match store.note_marker(symbol_id) {
        Some((count, stale)) => json!({ "count": count, "stale": stale }),
        None => serde_json::Value::Null,
    }
}
