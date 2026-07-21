//! Shared no-match boundary output for `ctx refs`/`sig` (specs/ctx-absence-check).
//!
//! A `ctx refs`/`sig` no-match means symbol resolution failed — object fields,
//! JSON keys, and string literals are NOT indexed, so a missing symbol is not
//! evidence a name is absent from the code. This module builds the boundary
//! note plus a bounded `grep` the calling agent can run to check text presence.
//! ctx prints the command; it never runs a whole-tree scan itself.

use crate::extract;

/// The boundary note: what a no-match does (and does not) prove. Kept to a
/// single line so the text-mode output is exactly three parts (no-match line,
/// this note, suggested command).
pub const BOUNDARY_NOTE: &str = "only definitions and references are indexed — \
object fields, JSON keys, and string literals are not. Absence of a symbol is \
not absence from code. To check text presence (bounded), run the command below.";

/// POSIX single-quote-escape `s` for safe literal inclusion in a shell command:
/// wrap in single quotes and rewrite each embedded `'` as `'\''`. `$` and other
/// metacharacters are literal inside single quotes, so this handles them too.
fn shell_single_quote(s: &str) -> String {
    let mut out = String::with_capacity(s.len() + 2);
    out.push('\'');
    for c in s.chars() {
        if c == '\'' {
            out.push_str("'\\''");
        } else {
            out.push(c);
        }
    }
    out.push('\'');
    out
}

/// The sorted, deduped extension union across every registered extractor — the
/// languages ctx indexes. Sorted for deterministic output across builds.
fn indexed_extensions() -> Vec<&'static str> {
    let mut exts: Vec<&'static str> = extract::registrations()
        .flat_map(|r| r.extensions.iter().copied())
        .collect();
    exts.sort_unstable();
    exts.dedup();
    exts
}

/// The bounded `grep` to check whether `symbol` appears as text (not just as an
/// indexed symbol): one repeated `--include='*.<ext>'` flag per indexed
/// extension — never a brace pattern, which grep's fnmatch does not expand —
/// the shell-escaped literal, and a `| head -20` bound.
pub fn suggested_check(symbol: &str) -> String {
    let includes = indexed_extensions()
        .iter()
        .map(|ext| format!("--include='*.{ext}'"))
        .collect::<Vec<_>>()
        .join(" ");
    format!(
        "grep -rl {includes} {} . | head -20",
        shell_single_quote(symbol)
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn suggested_check_extensions_are_the_registration_union() {
        let cmd = suggested_check("needle");

        let mut expected: Vec<&str> = extract::registrations()
            .flat_map(|r| r.extensions.iter().copied())
            .collect();
        expected.sort_unstable();
        expected.dedup();
        assert!(!expected.is_empty(), "some language is registered");

        // Exactly one repeated --include flag per extension in the union.
        for ext in &expected {
            let flag = format!("--include='*.{ext}'");
            assert_eq!(
                cmd.matches(&flag).count(),
                1,
                "one `--include` per extension {ext}: {cmd}"
            );
        }
        assert_eq!(
            cmd.matches("--include=").count(),
            expected.len(),
            "no extra `--include` flags beyond the union: {cmd}"
        );

        // Never a brace pattern (grep's fnmatch would match nothing).
        assert!(!cmd.contains('{'), "no brace pattern in the command: {cmd}");
        assert!(cmd.contains("| head -20"), "bounded by `head -20`: {cmd}");
    }

    #[test]
    fn suggested_check_shell_escapes_quotes_and_dollars() {
        // `a$b'c` -> '' wrapping with the inner ' rewritten as '\'' .
        assert!(
            suggested_check("a$b'c").contains("'a$b'\\''c'"),
            "a `$`/`'` symbol is single-quote escaped"
        );
        // A plain symbol is simply single-quoted.
        assert!(suggested_check("plain").contains("'plain'"));
    }
}
