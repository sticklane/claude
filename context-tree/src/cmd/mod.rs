//! Query subcommands (`ctx tree`/`ctx sig`/`ctx map`) and the shared
//! pre-command machinery they run: the C4 root guard, the R3 staleness sweep,
//! the C7 token count, and the C10 note-marker grammar.

pub mod at;
pub mod deps;
pub mod map;
pub mod refs;
pub mod sig;
pub mod tree;

use crate::index::IndexStore;
use crate::{project, sync};
use std::path::PathBuf;
use std::process::ExitCode;

/// Exit code for a no-match query (`ctx sig` with no resolvable symbol).
pub const EXIT_NO_MATCH: u8 = 1;
/// Exit code for the C4 root guard: no `.context/` ancestor exists.
pub const EXIT_NO_ROOT: u8 = 2;
/// Exit code for an ambiguous query (`ctx sig` matching several symbols).
pub const EXIT_AMBIGUOUS: u8 = 3;
/// Exit code for `ctx at` on an unresolvable position: an ignored, unsupported,
/// or nonexistent file (R19).
pub const EXIT_BAD_POSITION: u8 = 4;

/// The C10 note marker for a symbol's note tuple: `[notes:<count>]`, or
/// `[notes:<count>!]` when any note is stale. Empty when the symbol has no
/// notes — the `None` the store returns until task 09 populates notes.
pub fn format_note_marker(marker: Option<(usize, bool)>) -> String {
    match marker {
        Some((count, stale)) => format!(" [notes:{count}{}]", if stale { "!" } else { "" }),
        None => String::new(),
    }
}

/// C7 token count: `ceil(bytes / 4)`.
pub fn tokens_for_bytes(bytes: usize) -> usize {
    bytes.div_ceil(4)
}

/// C4 root guard + R3 staleness sweep. Returns the project root and an index
/// snapshot. On no `.context/` ancestor it prints a `ctx init` pointer and
/// returns [`EXIT_NO_ROOT`]; `no_sync` skips the sweep and opens the current
/// snapshot directly.
pub fn load_index(no_sync: bool) -> Result<(PathBuf, IndexStore), ExitCode> {
    let cwd = std::env::current_dir().map_err(|e| {
        eprintln!("ctx: cannot read current directory: {e}");
        ExitCode::FAILURE
    })?;
    let Some(root) = project::find_root(&cwd) else {
        eprintln!("ctx: no .context/ in this directory or any parent — run `ctx init` first");
        return Err(ExitCode::from(EXIT_NO_ROOT));
    };
    let store = if no_sync {
        IndexStore::open(&sync::cache_dir(&root)).map_err(|e| {
            eprintln!("ctx: cannot open index: {e}");
            ExitCode::FAILURE
        })?
    } else {
        sync::query_sweep(&root).map_err(|e| {
            eprintln!("ctx: sync failed: {e}");
            ExitCode::FAILURE
        })?
    };
    Ok((root, store))
}

/// The first non-empty line of a docstring (the compact-mode docstring slice
/// shared by every verb), trimmed of surrounding whitespace.
pub fn first_doc_line(docstring: &str) -> Option<&str> {
    docstring.lines().map(str::trim).find(|l| !l.is_empty())
}

/// A symbol's C10 note tuple as JSON: `null` until task 09 populates notes,
/// otherwise `{"count":<n>,"stale":<bool>}`.
pub fn note_value(store: &IndexStore, symbol_id: i64) -> serde_json::Value {
    match store.note_marker(symbol_id) {
        Some((count, stale)) => serde_json::json!({ "count": count, "stale": stale }),
        None => serde_json::Value::Null,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn format_note_marker_renders_c10_grammar() {
        assert_eq!(format_note_marker(None), "");
        assert_eq!(format_note_marker(Some((0, false))), " [notes:0]");
        assert_eq!(format_note_marker(Some((3, false))), " [notes:3]");
        assert_eq!(format_note_marker(Some((2, true))), " [notes:2!]");
    }

    #[test]
    fn tokens_for_bytes_rounds_up() {
        assert_eq!(tokens_for_bytes(0), 0);
        assert_eq!(tokens_for_bytes(1), 1);
        assert_eq!(tokens_for_bytes(4), 1);
        assert_eq!(tokens_for_bytes(5), 2);
    }

    #[test]
    fn first_doc_line_skips_leading_blank_lines() {
        assert_eq!(first_doc_line(""), None);
        assert_eq!(first_doc_line("First.\nSecond."), Some("First."));
        assert_eq!(first_doc_line("\n\n  Indented.\nmore"), Some("Indented."));
    }
}
