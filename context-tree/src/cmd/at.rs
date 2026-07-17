//! `ctx at <file>:<line>` — resolve a position to its innermost enclosing symbol
//! and print the containment chain (module → … → innermost) with each symbol's
//! kind, C1 path, signature first line, first docstring line, and C10 marker
//! (R19). A position enclosed by no definition falls back to the file's module
//! symbol. An ignored, unsupported-extension, or nonexistent file prints one
//! line naming the reason and exits 4.

use crate::cmd::{EXIT_BAD_POSITION, first_doc_line, format_note_marker, load_index, note_value};
use crate::extract;
use crate::index::SymbolRow;
use crate::vcs;
use serde_json::json;
use std::collections::HashMap;
use std::process::ExitCode;

/// Parsed `ctx at` arguments.
pub struct Args {
    pub position: String,
    pub json: bool,
    pub no_sync: bool,
}

/// The file's dotted module component (extension dropped, separators → `.`) —
/// the C1 module surface the chain always opens on.
fn module_component(rel: &str) -> String {
    let no_ext = match rel.rsplit_once('.') {
        Some((stem, _)) => stem,
        None => rel,
    };
    no_ext.replace(['/', '\\'], ".")
}

/// Byte offset of the 1-based `line`'s first byte; clamped to the source length
/// when the line runs past EOF (an out-of-range line resolves to the module).
fn line_start_byte(src: &[u8], line: usize) -> usize {
    if line <= 1 {
        return 0;
    }
    let mut newlines = 0usize;
    for (i, &b) in src.iter().enumerate() {
        if b == b'\n' {
            newlines += 1;
            if newlines == line - 1 {
                return i + 1;
            }
        }
    }
    src.len()
}

/// First line of a signature, trimmed.
fn sig_first_line(signature: &str) -> Option<&str> {
    signature.lines().map(str::trim).find(|l| !l.is_empty())
}

fn fail(json: bool, reason: &str) -> ExitCode {
    if json {
        println!("{}", json!({ "error": reason }));
    } else {
        eprintln!("ctx at: {reason}");
    }
    ExitCode::from(EXIT_BAD_POSITION)
}

pub fn run(args: Args) -> ExitCode {
    // Parse `<file>:<line>` from the right so paths may contain no colon.
    let Some((file, line_str)) = args.position.rsplit_once(':') else {
        return fail(args.json, &format!("invalid position '{}'", args.position));
    };
    let Ok(line) = line_str.parse::<usize>() else {
        return fail(args.json, &format!("invalid line in '{}'", args.position));
    };
    let rel = file.strip_prefix("./").unwrap_or(file).to_string();

    let (root, store) = match load_index(args.no_sync) {
        Ok(v) => v,
        Err(code) => return code,
    };

    let abs = root.join(&rel);
    if !abs.is_file() {
        return fail(args.json, &format!("no such file: {rel}"));
    }
    let ext = abs.extension().and_then(|e| e.to_str()).unwrap_or("");
    if extract::for_extension(ext).is_none() {
        return fail(args.json, &format!("unsupported extension: {rel}"));
    }
    if vcs::detect(&root).is_ignored(&root, &rel) {
        return fail(args.json, &format!("ignored file: {rel}"));
    }

    let src = std::fs::read(&abs).unwrap_or_default();
    // The queried line's byte range. A definition's `full_start_byte` begins at
    // its first token (after indentation), so containment is tested as span/line
    // OVERLAP rather than start-byte containment — otherwise pointing at a
    // nested symbol's own signature line would resolve to its parent.
    let line_start = line_start_byte(&src, line);
    let line_end = line_start_byte(&src, line + 1).max(line_start);
    let module_qpath = module_component(&rel);

    let all = match store.all_symbols() {
        Ok(v) => v,
        Err(e) => {
            eprintln!("ctx at: {e}");
            return ExitCode::FAILURE;
        }
    };
    let file_syms: Vec<&SymbolRow> = all.iter().filter(|s| s.path == rel).collect();
    let by_qpath: HashMap<&str, &SymbolRow> =
        file_syms.iter().map(|s| (s.qpath.as_str(), *s)).collect();

    // Innermost enclosing symbol: the deepest span overlapping the queried line.
    let innermost = file_syms
        .iter()
        .filter(|s| s.full_start_byte < line_end && s.full_end_byte > line_start)
        .max_by_key(|s| s.full_start_byte)
        .copied();

    // Walk the C1 parent chain up from the innermost symbol, then reverse to
    // render outermost → innermost.
    let mut chain: Vec<&SymbolRow> = Vec::new();
    let mut cursor = innermost;
    let mut guard = 0;
    while let Some(sym) = cursor {
        chain.push(sym);
        guard += 1;
        if guard > 256 {
            break;
        }
        cursor = sym.parent.as_deref().and_then(|p| by_qpath.get(p).copied());
    }
    chain.reverse();
    // A synthesized module surface always opens the chain; drop only the
    // extractor's file-level module symbol (its qpath is the file module) so it
    // is not rendered twice. Nested modules (Rust `mod`, TS `namespace`) are
    // real containers and stay in the chain.
    chain.retain(|s| !(s.kind == "module" && s.qpath == module_qpath));

    if args.json {
        let mut entries = vec![json!({
            "kind": "module",
            "qpath": module_qpath,
            "signature": "",
            "docstring": "",
            "notes": serde_json::Value::Null,
        })];
        for s in &chain {
            entries.push(json!({
                "kind": s.kind,
                "qpath": s.qpath,
                "signature": sig_first_line(&s.signature).unwrap_or(""),
                "docstring": first_doc_line(&s.docstring).unwrap_or(""),
                "notes": note_value(&store, s.id),
            }));
        }
        println!("{}", json!({ "file": rel, "line": line, "chain": entries }));
        return ExitCode::SUCCESS;
    }

    let mut out = format!("module {module_qpath}\n");
    for (depth, s) in chain.iter().enumerate() {
        let indent = "  ".repeat(depth + 1);
        let mut line = format!(
            "{indent}{} {}{}",
            s.kind,
            s.qpath,
            format_note_marker(store.note_marker(s.id)),
        );
        if let Some(sig) = sig_first_line(&s.signature) {
            line.push_str(" — ");
            line.push_str(sig);
        }
        if let Some(doc) = first_doc_line(&s.docstring) {
            line.push_str(" · ");
            line.push_str(doc);
        }
        out.push_str(&line);
        out.push('\n');
    }
    print!("{out}");
    ExitCode::SUCCESS
}
