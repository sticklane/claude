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
/// indexed symbol): `-F` so the symbol is matched as a fixed string, not a regex
/// (a symbol with `[`/`$`/`(` etc. would otherwise error or silently mismatch —
/// the false-"absent" verdict this module exists to prevent); one repeated
/// `--include='*.<ext>'` flag per indexed extension — never a brace pattern,
/// which grep's fnmatch does not expand — the shell-escaped literal, and a
/// `| head -20` bound.
pub fn suggested_check(symbol: &str) -> String {
    let includes = indexed_extensions()
        .iter()
        .map(|ext| format!("--include='*.{ext}'"))
        .collect::<Vec<_>>()
        .join(" ");
    format!(
        "grep -rlF {includes} {} . | head -20",
        shell_single_quote(symbol)
    )
}

/// Maximum "did you mean" candidates listed before the boundary note (R4).
const MAX_DID_YOU_MEAN: usize = 5;

/// Up to `MAX_DID_YOU_MEAN` near-miss candidates for `query`, drawn from the
/// symbol names in `names`: a name qualifies when, case-folded, it contains the
/// query or the query contains it — so a case variant (`figureBboxes` for a
/// `FigureBboxes` query) or a near-substring is caught. Deduped and sorted for a
/// stable, deterministic list; empty when nothing is close. Symbol-table lookup
/// only — no tree work.
pub fn did_you_mean<'a>(query: &str, names: impl IntoIterator<Item = &'a str>) -> Vec<String> {
    let q = query.to_lowercase();
    if q.is_empty() {
        return Vec::new();
    }
    let mut cands: Vec<String> = names
        .into_iter()
        .filter(|name| {
            let n = name.to_lowercase();
            !n.is_empty() && (n.contains(&q) || q.contains(&n))
        })
        .map(str::to_string)
        .collect();
    cands.sort_unstable();
    cands.dedup();
    cands.truncate(MAX_DID_YOU_MEAN);
    cands
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

    /// Regression: a symbol containing regex metacharacters must be matched
    /// LITERALLY by the suggested command. Without fixed-string matching, grep
    /// reads the symbol as a regex — `a[b` errors (unbalanced bracket) and a
    /// mid-pattern anchor can mismatch — so the file that literally contains the
    /// symbol is reported ABSENT: the exact "absence is not absence" fallacy this
    /// module exists to prevent. Runs the produced command and asserts it finds a
    /// file whose text is the literal symbol.
    #[test]
    fn suggested_check_matches_regex_metacharacter_symbols_literally() {
        for symbol in ["a[b", "a$b'c"] {
            let dir = tempfile::tempdir().unwrap();
            // `.rs` is an indexed extension, so the suggested command's
            // `--include` set covers this probe file.
            std::fs::write(
                dir.path().join("probe.rs"),
                format!("let v = {symbol:?};\n"),
            )
            .unwrap();

            let cmd = suggested_check(symbol);
            let output = std::process::Command::new("sh")
                .arg("-c")
                .arg(&cmd)
                .current_dir(dir.path())
                .output()
                .expect("run the suggested grep command");
            let stdout = String::from_utf8_lossy(&output.stdout);
            assert!(
                stdout.contains("probe.rs"),
                "suggested command must literally match symbol {symbol:?}: \
                 cmd=`{cmd}` stdout={stdout:?} stderr={:?}",
                String::from_utf8_lossy(&output.stderr)
            );
        }
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

    #[test]
    fn did_you_mean_catches_case_variants_and_ignores_the_unrelated() {
        let names = ["figureBboxes", "unrelated"];
        assert_eq!(
            did_you_mean("FigureBboxes", names.iter().copied()),
            vec!["figureBboxes".to_string()],
            "a case variant is offered as a candidate"
        );
        assert!(
            did_you_mean("zzz_nothing_close", names.iter().copied()).is_empty(),
            "nothing close yields no candidates"
        );
    }

    #[test]
    fn did_you_mean_caps_at_five_in_sorted_order() {
        let names = ["conf_f", "conf_a", "conf_c", "conf_e", "conf_b", "conf_d"];
        let got = did_you_mean("conf", names.iter().copied());
        assert_eq!(
            got,
            ["conf_a", "conf_b", "conf_c", "conf_d", "conf_e"],
            "capped at five in a stable sorted order: {got:?}"
        );
    }
}
