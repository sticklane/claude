//! `ctx sig <symbol>` — a symbol's signature (and docstring) resolved by C3
//! suffix matching (R7). Exit 0 on a unique match, 1 on no match, 3 on an
//! ambiguous match (candidate list printed).

use crate::cmd::{
    EXIT_AMBIGUOUS, EXIT_NO_MATCH, first_doc_line, format_note_marker, load_index, note_value,
};
use crate::index::SymbolRow;
use crate::path::resolve_suffix;
use serde_json::json;
use std::collections::HashSet;
use std::path::Path;
use std::process::ExitCode;

/// Parsed `ctx sig` arguments.
pub struct Args {
    pub symbol: String,
    pub doc: bool,
    pub json: bool,
    pub no_sync: bool,
}

/// 1-based line of `byte` within the file at `root/rel`; 1 when the source can't
/// be read (the candidate list degrades rather than fails).
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

pub fn run(args: Args) -> ExitCode {
    let (out, code) = render(&args);
    print!("{out}");
    code
}

/// The exact stdout `run` would print, paired with the exit code. Shared with
/// the MCP wrapper (R15); error diagnostics still go to stderr via `eprintln!`.
pub fn render(args: &Args) -> (String, ExitCode) {
    let (root, store) = match load_index(args.no_sync) {
        Ok(v) => v,
        Err(code) => return (String::new(), code),
    };
    let all = match store.all_symbols() {
        Ok(v) => v,
        Err(e) => {
            eprintln!("ctx sig: {e}");
            return (String::new(), ExitCode::FAILURE);
        }
    };

    let qpaths: Vec<String> = all.iter().map(|s| s.qpath.clone()).collect();
    let matched: HashSet<&str> = resolve_suffix(&qpaths, &args.symbol).into_iter().collect();
    let mut hits: Vec<&SymbolRow> = all
        .iter()
        .filter(|s| matched.contains(s.qpath.as_str()))
        .collect();
    hits.sort_by(|a, b| a.qpath.cmp(&b.qpath));

    let mut out = String::new();
    match hits.as_slice() {
        [] => {
            if args.json {
                out.push_str(&format!(
                    "{}\n",
                    json!({ "error": "no match", "symbol": args.symbol })
                ));
            } else {
                eprintln!("ctx sig: no symbol matches '{}'", args.symbol);
            }
            (out, ExitCode::from(EXIT_NO_MATCH))
        }
        [sym] => {
            if args.json {
                out.push_str(&format!(
                    "{}\n",
                    json!({
                        "qpath": sym.qpath,
                        "kind": sym.kind,
                        "signature": sym.signature,
                        "docstring": sym.docstring,
                        "file": sym.path,
                        "notes": note_value(&store, sym.id),
                    })
                ));
            } else {
                out.push_str(&sym.signature);
                out.push_str(&format_note_marker(store.note_marker(sym.id)));
                out.push('\n');
                if args.doc {
                    if !sym.docstring.trim().is_empty() {
                        out.push_str(&format!("{}\n", sym.docstring.trim_end()));
                    }
                } else if let Some(line) = first_doc_line(&sym.docstring) {
                    out.push_str(&format!("{line}\n"));
                }
            }
            (out, ExitCode::SUCCESS)
        }
        many => {
            if args.json {
                let candidates: Vec<serde_json::Value> = many
                    .iter()
                    .map(|s| {
                        json!({
                            "qpath": s.qpath,
                            "file": s.path,
                            "line": line_of(&root, &s.path, s.ident_start_byte),
                        })
                    })
                    .collect();
                out.push_str(&format!(
                    "{}\n",
                    json!({ "error": "ambiguous", "symbol": args.symbol, "candidates": candidates })
                ));
            } else {
                eprintln!("ctx sig: '{}' is ambiguous — candidates:", args.symbol);
                for s in many {
                    out.push_str(&format!(
                        "{}  {}:{}\n",
                        s.qpath,
                        s.path,
                        line_of(&root, &s.path, s.ident_start_byte)
                    ));
                }
            }
            (out, ExitCode::from(EXIT_AMBIGUOUS))
        }
    }
}
