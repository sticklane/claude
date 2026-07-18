//! R13 deterministic, layered re-anchoring. When a note's anchored symbol no
//! longer resolves, sync re-anchors it against the changed files' new symbols
//! in layer order:
//!
//! 1. **Qualified-name match** — a unique candidate sharing the old anchor's
//!    terminal name AND kind. Zero or multiple candidates fall through.
//! 2. **Body-hash match** (C2) — a candidate whose identifier-excised body hash
//!    equals the old anchor's (a pure rename preserves the hash, so this catches
//!    an in-file rename). Ties broken by lowest `(file, line)`.
//! 3. **Tree-diff match** — same-kind candidates scored by token overlap between
//!    identifier-excised body token sets (R1's persisted set); re-anchor to the
//!    highest scorer above [`TREE_DIFF_THRESHOLD`], ties broken by lowest
//!    `(file, line)`. No candidate above threshold → the note stays
//!    un-re-anchored and stale.
//!
//! The algorithm is pure: the sync engine (src/sync) captures the old anchor's
//! identity from the pre-reparse index, collects candidates from the reparsed
//! files, and applies [`reanchor`].

/// The tree-diff (layer 3) re-anchor threshold: a candidate must score strictly
/// above this token-overlap fraction to be eligible.
pub const TREE_DIFF_THRESHOLD: f64 = 0.6;

/// The identity of a note's anchored symbol as captured from the index BEFORE
/// this sync re-parsed the changed files — the driver of the layered match.
#[derive(Debug, Clone)]
pub struct OldAnchor {
    /// The symbol's terminal name (last C1 component, without any `#n`).
    pub name: String,
    pub kind: String,
    /// C2 identifier-excised body hash.
    pub body_hash: String,
    /// R1 identifier-excised body token set (sorted, de-duplicated).
    pub body_tokens: Vec<String>,
}

/// A candidate definition from a changed file's new tree (R13). Parse-failed
/// files contribute no candidates.
#[derive(Debug, Clone)]
pub struct Candidate {
    pub qpath: String,
    pub name: String,
    pub kind: String,
    pub body_hash: String,
    pub body_tokens: Vec<String>,
    pub file: String,
    /// 1-based line of the definition, for the lowest-`file:line` tie-break.
    pub row: usize,
}

/// Token overlap between two identifier-excised body token sets: the Jaccard
/// index `|A ∩ B| / |A ∪ B|`. Both inputs are sorted, de-duplicated sets. Two
/// empty sets overlap 0.0 (no shared evidence to anchor on).
pub fn token_overlap(a: &[String], b: &[String]) -> f64 {
    if a.is_empty() && b.is_empty() {
        return 0.0;
    }
    let bset: std::collections::HashSet<&str> = b.iter().map(String::as_str).collect();
    let aset: std::collections::HashSet<&str> = a.iter().map(String::as_str).collect();
    let inter = aset.iter().filter(|t| bset.contains(**t)).count();
    let union = aset.len() + bset.len() - inter;
    if union == 0 {
        0.0
    } else {
        inter as f64 / union as f64
    }
}

/// The `(file, line)` tie-break key: lowest file path, then lowest line.
fn tiebreak(c: &Candidate) -> (&str, usize) {
    (c.file.as_str(), c.row)
}

/// Apply the layered re-anchor algorithm, returning the new qualified path of
/// the winning candidate, or `None` when no layer resolves.
pub fn reanchor(old: &OldAnchor, candidates: &[Candidate]) -> Option<String> {
    // Layer 1: qualified-name match — unique candidate sharing name AND kind.
    let name_kind: Vec<&Candidate> = candidates
        .iter()
        .filter(|c| c.name == old.name && c.kind == old.kind)
        .collect();
    if name_kind.len() == 1 {
        return Some(name_kind[0].qpath.clone());
    }

    // Layer 2: body-hash match (C2) — a rename preserves the excised hash.
    let hash_match: Vec<&Candidate> = candidates
        .iter()
        .filter(|c| c.body_hash == old.body_hash)
        .collect();
    if let Some(best) = hash_match.iter().min_by_key(|c| tiebreak(c)) {
        return Some(best.qpath.clone());
    }

    // Layer 3: tree-diff — highest token overlap above threshold, same kind.
    let mut scored: Vec<(f64, &Candidate)> = candidates
        .iter()
        .filter(|c| c.kind == old.kind)
        .map(|c| (token_overlap(&old.body_tokens, &c.body_tokens), c))
        .filter(|(score, _)| *score > TREE_DIFF_THRESHOLD)
        .collect();
    // Highest score wins; ties broken by lowest (file, line).
    scored.sort_by(|(sa, ca), (sb, cb)| {
        sb.partial_cmp(sa)
            .unwrap_or(std::cmp::Ordering::Equal)
            .then_with(|| tiebreak(ca).cmp(&tiebreak(cb)))
    });
    scored.first().map(|(_, c)| c.qpath.clone())
}

#[cfg(test)]
mod tree_diff_scorer {
    use super::*;

    fn toks(words: &[&str]) -> Vec<String> {
        let mut v: Vec<String> = words.iter().map(|s| s.to_string()).collect();
        v.sort();
        v.dedup();
        v
    }

    fn cand(
        qpath: &str,
        name: &str,
        kind: &str,
        hash: &str,
        words: &[&str],
        file: &str,
        row: usize,
    ) -> Candidate {
        Candidate {
            qpath: qpath.into(),
            name: name.into(),
            kind: kind.into(),
            body_hash: hash.into(),
            body_tokens: toks(words),
            file: file.into(),
            row,
        }
    }

    #[test]
    fn token_overlap_identical_sets_is_one() {
        assert_eq!(
            token_overlap(&toks(&["a", "b", "c"]), &toks(&["a", "b", "c"])),
            1.0
        );
    }

    #[test]
    fn token_overlap_disjoint_sets_is_zero() {
        assert_eq!(token_overlap(&toks(&["a", "b"]), &toks(&["c", "d"])), 0.0);
    }

    #[test]
    fn token_overlap_two_empty_sets_is_zero() {
        assert_eq!(token_overlap(&[], &[]), 0.0);
    }

    #[test]
    fn token_overlap_is_jaccard_fraction() {
        // {a,b,c,d} ∩ {a,b,c,e} = 3; ∪ = 5 → 0.6.
        let s = token_overlap(&toks(&["a", "b", "c", "d"]), &toks(&["a", "b", "c", "e"]));
        assert!((s - 0.6).abs() < 1e-9, "expected 0.6, got {s}");
    }

    #[test]
    fn layer1_unique_name_and_kind_wins() {
        let old = OldAnchor {
            name: "foo".into(),
            kind: "function".into(),
            body_hash: "OLD".into(),
            body_tokens: toks(&["x"]),
        };
        let cands = vec![
            cand("b.foo", "foo", "function", "NEW", &["y"], "b.c", 1),
            cand("b.bar", "bar", "function", "Z", &["z"], "b.c", 5),
        ];
        assert_eq!(reanchor(&old, &cands), Some("b.foo".into()));
    }

    #[test]
    fn layer1_falls_through_when_multiple_name_kind_candidates() {
        // Two candidates share name+kind → layer 1 ambiguous; hash breaks it.
        let old = OldAnchor {
            name: "foo".into(),
            kind: "function".into(),
            body_hash: "H".into(),
            body_tokens: toks(&["x"]),
        };
        let cands = vec![
            cand("a.foo", "foo", "function", "OTHER", &["p"], "a.c", 1),
            cand("b.foo", "foo", "function", "H", &["x"], "b.c", 1),
        ];
        // Layer 1 has two name+kind hits → falls through to layer 2 (body-hash).
        assert_eq!(reanchor(&old, &cands), Some("b.foo".into()));
    }

    #[test]
    fn layer2_body_hash_matches_a_rename() {
        // Rename: name changed, but excised body hash preserved (C2).
        let old = OldAnchor {
            name: "foo".into(),
            kind: "function".into(),
            body_hash: "SAME".into(),
            body_tokens: toks(&["x", "y"]),
        };
        let cands = vec![cand(
            "m.bar",
            "bar",
            "function",
            "SAME",
            &["x", "y"],
            "m.py",
            3,
        )];
        assert_eq!(reanchor(&old, &cands), Some("m.bar".into()));
    }

    #[test]
    fn layer2_ties_break_by_lowest_file_line() {
        let old = OldAnchor {
            name: "foo".into(),
            kind: "function".into(),
            body_hash: "SAME".into(),
            body_tokens: toks(&["x"]),
        };
        let cands = vec![
            cand("z.bar", "bar", "function", "SAME", &["x"], "z.py", 9),
            cand("a.baz", "baz", "function", "SAME", &["x"], "a.py", 2),
        ];
        assert_eq!(reanchor(&old, &cands), Some("a.baz".into()));
    }

    #[test]
    fn layer3_tree_diff_above_threshold_wins() {
        // name changed AND hash changed → only tree-diff can resolve.
        let old = OldAnchor {
            name: "foo".into(),
            kind: "function".into(),
            body_hash: "OLD".into(),
            body_tokens: toks(&["alpha", "beta", "gamma", "delta"]),
        };
        let cands = vec![
            // overlap {alpha,beta,gamma}/{alpha,beta,gamma,delta,eps} = 3/5 = 0.6 → NOT > 0.6
            cand(
                "m.low",
                "low",
                "function",
                "N1",
                &["alpha", "beta", "gamma", "eps"],
                "m.py",
                1,
            ),
            // overlap {alpha,beta,gamma,delta}/{...,zeta} = 4/5 = 0.8 → > 0.6
            cand(
                "m.high",
                "high",
                "function",
                "N2",
                &["alpha", "beta", "gamma", "delta", "zeta"],
                "m.py",
                8,
            ),
        ];
        assert_eq!(reanchor(&old, &cands), Some("m.high".into()));
    }

    #[test]
    fn layer3_threshold_is_strict_at_point_six() {
        // Exactly 0.6 is NOT above threshold → no re-anchor.
        let old = OldAnchor {
            name: "foo".into(),
            kind: "function".into(),
            body_hash: "OLD".into(),
            body_tokens: toks(&["alpha", "beta", "gamma", "delta"]),
        };
        let cands = vec![cand(
            "m.mid",
            "mid",
            "function",
            "N",
            &["alpha", "beta", "gamma", "eps"],
            "m.py",
            1,
        )];
        assert_eq!(reanchor(&old, &cands), None);
    }

    #[test]
    fn layer3_ties_break_by_lowest_file_line() {
        let old = OldAnchor {
            name: "foo".into(),
            kind: "function".into(),
            body_hash: "OLD".into(),
            body_tokens: toks(&["a", "b", "c", "d"]),
        };
        // Both score 0.8 (4/5); lowest (file,line) wins.
        let cands = vec![
            cand(
                "z.hi",
                "hi",
                "function",
                "N1",
                &["a", "b", "c", "d", "z"],
                "z.py",
                1,
            ),
            cand(
                "a.hi",
                "hi",
                "function",
                "N2",
                &["a", "b", "c", "d", "w"],
                "a.py",
                1,
            ),
        ];
        assert_eq!(reanchor(&old, &cands), Some("a.hi".into()));
    }

    #[test]
    fn no_candidate_yields_none() {
        let old = OldAnchor {
            name: "foo".into(),
            kind: "function".into(),
            body_hash: "H".into(),
            body_tokens: toks(&["x"]),
        };
        assert_eq!(reanchor(&old, &[]), None);
    }

    #[test]
    fn different_kind_blocks_all_layers() {
        // Same name and even same hash, but a different kind — layer 1 needs
        // kind, layer 3 needs kind; layer 2 is hash-only so it still matches.
        let old = OldAnchor {
            name: "foo".into(),
            kind: "function".into(),
            body_hash: "OTHER".into(),
            body_tokens: toks(&["x", "y", "z"]),
        };
        let cands = vec![cand(
            "m.foo",
            "foo",
            "class",
            "N",
            &["x", "y", "z"],
            "m.py",
            1,
        )];
        // name matches but kind differs (L1 no), hash differs (L2 no), kind differs (L3 no).
        assert_eq!(reanchor(&old, &cands), None);
    }
}
