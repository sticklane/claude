//! `ctx notes add <symbol> …`, `ctx notes <symbol>`, and `ctx notes list` (R12):
//! note CRUD and derived-freshness reads. Add resolves its anchor by C3 suffix
//! and refuses an ambiguous anchor exactly as the query commands do (exit 3);
//! the read forms run the R3 staleness sweep first (via [`load_index`]) so their
//! freshness reflects the working tree.

use crate::cmd::{EXIT_AMBIGUOUS, EXIT_NO_MATCH, load_index};
use crate::index::NoteRow;
use crate::notes::anchor::{self, Resolution};
use crate::notes::{self, NoteDraft};
use serde_json::json;
use std::io::Read;
use std::process::ExitCode;

/// Which `ctx notes` form is being run.
pub enum Action {
    Add {
        symbol: String,
        text: Option<String>,
        kind: Option<String>,
        file: Option<String>,
    },
    List {
        kind: Option<String>,
        stale: bool,
        file: Option<String>,
    },
    Show {
        symbol: String,
    },
    /// `ctx notes` with neither a subcommand nor a `<symbol>`.
    Usage,
}

/// Parsed `ctx notes` arguments.
pub struct Args {
    pub action: Action,
    pub json: bool,
    pub no_sync: bool,
}

pub fn run(args: Args) -> ExitCode {
    match args.action {
        Action::Add {
            symbol,
            text,
            kind,
            file,
        } => add(&symbol, text, kind, file, args.no_sync, args.json),
        Action::List { kind, stale, file } => list(kind, stale, file, args.no_sync, args.json),
        Action::Show { symbol } => show(&symbol, args.no_sync, args.json),
        Action::Usage => {
            eprintln!("ctx notes: expected `add`, `list`, or a <symbol>");
            ExitCode::from(EXIT_NO_MATCH)
        }
    }
}

/// Resolve the note body from the positional text, `--file <path>`, or stdin
/// (`--file -`), in that precedence order.
fn note_body(text: Option<String>, file: Option<String>) -> Result<String, String> {
    if let Some(t) = text {
        return Ok(t);
    }
    match file.as_deref() {
        Some("-") => {
            let mut buf = String::new();
            std::io::stdin()
                .read_to_string(&mut buf)
                .map_err(|e| format!("cannot read stdin: {e}"))?;
            Ok(buf)
        }
        Some(path) => std::fs::read_to_string(path).map_err(|e| format!("cannot read {path}: {e}")),
        None => Err("a note body is required (positional text, --file <path>, or --file -)".into()),
    }
}

fn add(
    symbol: &str,
    text: Option<String>,
    kind: Option<String>,
    file: Option<String>,
    no_sync: bool,
    json: bool,
) -> ExitCode {
    let body = match note_body(text, file) {
        Ok(b) => b,
        Err(e) => {
            eprintln!("ctx notes add: {e}");
            return ExitCode::FAILURE;
        }
    };
    let (root, store) = match load_index(no_sync) {
        Ok(v) => v,
        Err(code) => return code,
    };
    let symbols = match store.all_symbols() {
        Ok(v) => v,
        Err(e) => {
            eprintln!("ctx notes add: {e}");
            return ExitCode::FAILURE;
        }
    };

    match anchor::resolve(&symbols, symbol) {
        Resolution::None => {
            eprintln!("ctx notes add: no symbol matches '{symbol}'");
            ExitCode::from(EXIT_NO_MATCH)
        }
        Resolution::Ambiguous(candidates) => {
            eprintln!("ctx notes add: '{symbol}' is ambiguous — candidates:");
            for s in candidates {
                println!("{}  {}", s.qpath, s.path);
            }
            ExitCode::from(EXIT_AMBIGUOUS)
        }
        Resolution::Unique(sym) => {
            let draft = NoteDraft {
                anchor_path: sym.qpath.clone(),
                anchor_hash: sym.body_hash.clone(),
                kind,
                body,
            };
            match notes::write_note(&root, &draft) {
                Ok(rel) => {
                    if json {
                        println!("{}", json!({ "created": rel, "anchor": sym.qpath }));
                    } else {
                        println!("note added: {rel} -> {}", sym.qpath);
                    }
                    ExitCode::SUCCESS
                }
                Err(e) => {
                    eprintln!("ctx notes add: {e}");
                    ExitCode::FAILURE
                }
            }
        }
    }
}

fn note_json(n: &NoteRow) -> serde_json::Value {
    json!({
        "id": n.id,
        "anchor": n.anchor_path,
        "kind": n.kind,
        "fresh": n.fresh,
        "pending": n.pending,
        "file": n.file,
        "author": n.author,
        "created": n.created,
        "path": n.rel_path,
    })
}

/// One plain-text listing line: `<fresh|stale>\t<kind>\t<anchor>\t<id>`, with a
/// trailing `pending` column when the note carries an unwritten re-anchor (R13).
fn note_line(n: &NoteRow) -> String {
    let freshness = if n.fresh { "fresh" } else { "stale" };
    let kind = n.kind.as_deref().unwrap_or("-");
    let pending = if n.pending { "\tpending" } else { "" };
    format!("{freshness}\t{kind}\t{}\t{}{pending}", n.anchor_path, n.id)
}

fn list(
    kind: Option<String>,
    stale: bool,
    file: Option<String>,
    no_sync: bool,
    json: bool,
) -> ExitCode {
    let (_root, store) = match load_index(no_sync) {
        Ok(v) => v,
        Err(code) => return code,
    };
    let notes = match store.all_notes() {
        Ok(v) => v,
        Err(e) => {
            eprintln!("ctx notes list: {e}");
            return ExitCode::FAILURE;
        }
    };
    let selected: Vec<&NoteRow> = notes
        .iter()
        .filter(|n| {
            kind.as_deref().is_none_or(|k| n.kind.as_deref() == Some(k))
                && (!stale || !n.fresh)
                && file.as_deref().is_none_or(|f| n.file.as_deref() == Some(f))
        })
        .collect();

    if json {
        let arr: Vec<serde_json::Value> = selected.iter().map(|n| note_json(n)).collect();
        println!("{}", serde_json::Value::Array(arr));
    } else {
        for n in selected {
            println!("{}", note_line(n));
        }
    }
    ExitCode::SUCCESS
}

fn show(symbol: &str, no_sync: bool, json: bool) -> ExitCode {
    let (_root, store) = match load_index(no_sync) {
        Ok(v) => v,
        Err(code) => return code,
    };
    let symbols = match store.all_symbols() {
        Ok(v) => v,
        Err(e) => {
            eprintln!("ctx notes: {e}");
            return ExitCode::FAILURE;
        }
    };
    let qpath = match anchor::resolve(&symbols, symbol) {
        Resolution::None => {
            eprintln!("ctx notes: no symbol matches '{symbol}'");
            return ExitCode::from(EXIT_NO_MATCH);
        }
        Resolution::Ambiguous(candidates) => {
            eprintln!("ctx notes: '{symbol}' is ambiguous — candidates:");
            for s in candidates {
                println!("{}  {}", s.qpath, s.path);
            }
            return ExitCode::from(EXIT_AMBIGUOUS);
        }
        Resolution::Unique(sym) => sym.qpath.clone(),
    };

    let notes = match store.all_notes() {
        Ok(v) => v,
        Err(e) => {
            eprintln!("ctx notes: {e}");
            return ExitCode::FAILURE;
        }
    };
    let mine: Vec<&NoteRow> = notes.iter().filter(|n| n.anchor_path == qpath).collect();

    if json {
        let arr: Vec<serde_json::Value> = mine.iter().map(|n| note_json(n)).collect();
        println!("{}", serde_json::Value::Array(arr));
    } else {
        for n in mine {
            let freshness = if n.fresh { "fresh" } else { "stale" };
            let kind = n.kind.as_deref().unwrap_or("-");
            println!("{}  {freshness}  kind={kind}", n.id);
            if !n.body.trim().is_empty() {
                println!("{}", n.body.trim_end());
            }
        }
    }
    ExitCode::SUCCESS
}
