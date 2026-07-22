//! `ctx show <symbol>` — a resolved symbol's exact source span, read from the
//! freshly-reconciled index (R2). Resolved by the same C3 suffix matcher as
//! `ctx sig`/`ctx refs`; exit 0 on a unique match, 1 on no match, 3 on an
//! ambiguous match (candidate list printed).

use crate::cmd::{EXIT_AMBIGUOUS, EXIT_NO_MATCH, load_index, no_match};
use crate::index::SymbolRow;
use crate::path::resolve_suffix;
use serde_json::json;
use std::collections::HashSet;
use std::path::Path;
use std::process::ExitCode;

/// Default line cap for the plain-text truncation guard, overridden by `--head`.
const DEFAULT_HEAD: usize = 200;

/// Parsed `ctx show` arguments.
pub struct Args {
    pub symbol: String,
    pub head: Option<usize>,
    pub json: bool,
    pub no_sync: bool,
}

/// 1-based line of `byte` within the file at `root/rel`; 1 when the source
/// can't be read (mirrors `sig::line_of`'s degrade-rather-than-fail shape).
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

/// The exact stdout `run` would print, paired with the exit code.
pub fn render(args: &Args) -> (String, ExitCode) {
    let (root, store) = match load_index(args.no_sync) {
        Ok(v) => v,
        Err(code) => return (String::new(), code),
    };
    let all = match store.all_symbols() {
        Ok(v) => v,
        Err(e) => {
            eprintln!("ctx show: {e}");
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

    match hits.as_slice() {
        [] => {
            let mut out = String::new();
            if args.json {
                out.push_str(&format!(
                    "{}\n",
                    json!({
                        "error": "no match",
                        "symbol": args.symbol,
                        "boundary_note": no_match::BOUNDARY_NOTE,
                        "suggested_check": no_match::suggested_check(&args.symbol),
                    })
                ));
            } else {
                eprintln!("ctx show: no symbol matches '{}'", args.symbol);
                let candidates =
                    no_match::did_you_mean(&args.symbol, all.iter().map(|s| s.name.as_str()));
                if !candidates.is_empty() {
                    eprintln!("did you mean: {}", candidates.join(", "));
                }
                eprintln!("note: {}", no_match::BOUNDARY_NOTE);
                eprintln!("  {}", no_match::suggested_check(&args.symbol));
            }
            (out, ExitCode::from(EXIT_NO_MATCH))
        }
        [sym] => render_span(&root, sym, args),
        many => {
            let mut out = String::new();
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
                eprintln!("ctx show: '{}' is ambiguous — candidates:", args.symbol);
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

/// Render the resolved symbol's exact span: the raw source bytes
/// `[full_start_byte, full_end_byte)` from the working tree, converted to
/// 1-based inclusive start/end lines.
fn render_span(root: &Path, sym: &SymbolRow, args: &Args) -> (String, ExitCode) {
    let src = match std::fs::read(root.join(&sym.path)) {
        Ok(b) => b,
        Err(e) => {
            eprintln!("ctx show: cannot read {}: {e}", sym.path);
            return (String::new(), ExitCode::FAILURE);
        }
    };
    let start_line = line_of(root, &sym.path, sym.full_start_byte);
    let end_line = line_of(root, &sym.path, sym.full_end_byte);
    let text = String::from_utf8_lossy(&src[sym.full_start_byte..sym.full_end_byte.min(src.len())])
        .into_owned();

    let mut out = String::new();
    if args.json {
        out.push_str(&format!(
            "{}\n",
            json!({
                "path": sym.path,
                "start_line": start_line,
                "end_line": end_line,
                "text": text,
            })
        ));
    } else {
        let cap = args.head.unwrap_or(DEFAULT_HEAD);
        let lines: Vec<&str> = text.lines().collect();
        if lines.len() > cap {
            for line in &lines[..cap] {
                out.push_str(line);
                out.push('\n');
            }
            out.push_str(&format!(
                "\u{2026} +{} more lines, use --head/Read\n",
                lines.len() - cap
            ));
        } else {
            out.push_str(&text);
            out.push('\n');
        }
    }
    (out, ExitCode::SUCCESS)
}
