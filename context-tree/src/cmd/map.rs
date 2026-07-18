//! `ctx map` — a ranked project overview ordered by reference-graph importance
//! (R8), truncated to a token budget (C7), with `--doc` and C10 markers.

use crate::cmd::{first_doc_line, format_note_marker, load_index, note_value, tokens_for_bytes};
use crate::index::{IndexStore, SymbolRow};
use serde_json::json;
use std::cmp::Reverse;
use std::process::ExitCode;

/// Parsed `ctx map` arguments.
pub struct Args {
    pub tokens: usize,
    pub doc: bool,
    pub json: bool,
    pub no_sync: bool,
}

/// One rendered ranked line for a symbol (without the trailing newline).
fn line_for(store: &IndexStore, sym: &SymbolRow, doc: bool) -> String {
    let mut line = format!("{} {}", sym.kind, sym.qpath);
    line.push_str(&format_note_marker(store.note_marker(sym.id)));
    if doc && let Some(first) = first_doc_line(&sym.docstring) {
        line.push_str(" — ");
        line.push_str(first);
    }
    line
}

pub fn run(args: Args) -> ExitCode {
    let (out, code) = render(&args);
    print!("{out}");
    code
}

/// The exact stdout `run` would print, paired with the exit code. Shared with
/// the MCP wrapper (R15); error diagnostics still go to stderr via `eprintln!`.
pub fn render(args: &Args) -> (String, ExitCode) {
    let (_root, store) = match load_index(args.no_sync) {
        Ok(v) => v,
        Err(code) => return (String::new(), code),
    };
    let all = match store.all_symbols() {
        Ok(v) => v,
        Err(e) => {
            eprintln!("ctx map: {e}");
            return (String::new(), ExitCode::FAILURE);
        }
    };
    let counts = match store.reference_counts() {
        Ok(v) => v,
        Err(e) => {
            eprintln!("ctx map: {e}");
            return (String::new(), ExitCode::FAILURE);
        }
    };

    // Rank by reference-graph importance (R8), tie-broken by qpath so the order
    // is deterministic (rebuild-stable) rather than lexical/insertion order.
    let mut ranked: Vec<(&SymbolRow, usize)> = all
        .iter()
        .map(|s| (s, counts.get(&s.name).copied().unwrap_or(0)))
        .collect();
    ranked.sort_by(|a, b| {
        Reverse(a.1)
            .cmp(&Reverse(b.1))
            .then(a.0.qpath.cmp(&b.0.qpath))
    });

    // Truncate to the token budget (C7): a line joins the output only while the
    // running ceil(bytes/4) stays within the budget.
    let mut included: Vec<(&SymbolRow, usize, String)> = Vec::new();
    let mut bytes = 0usize;
    let mut truncated = false;
    for (sym, refs) in ranked {
        let line = line_for(&store, sym, args.doc);
        let next = bytes + line.len() + 1; // + newline
        if tokens_for_bytes(next) > args.tokens {
            truncated = true;
            break;
        }
        bytes = next;
        included.push((sym, refs, line));
    }

    if args.json {
        let symbols: Vec<serde_json::Value> = included
            .iter()
            .map(|(sym, refs, _)| {
                json!({
                    "qpath": sym.qpath,
                    "kind": sym.kind,
                    "refs": refs,
                    "signature": sym.signature,
                    "docstring": if args.doc { sym.docstring.clone() } else { String::new() },
                    "notes": note_value(&store, sym.id),
                })
            })
            .collect();
        (
            format!(
                "{}\n",
                json!({ "tokens": args.tokens, "truncated": truncated, "symbols": symbols })
            ),
            ExitCode::SUCCESS,
        )
    } else {
        let mut out = String::new();
        for (_, _, line) in &included {
            out.push_str(line);
            out.push('\n');
        }
        (out, ExitCode::SUCCESS)
    }
}
