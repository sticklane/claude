//! `.ctxzones` config layer (spec `ctx-dead-code-zones`, task 01). Loads a
//! repo-root `.ctxzones` file — `<label>: <glob>` per line, reusing the
//! `.ctxignore` matcher verbatim (`crate::vcs::ctxignore_matches`, promoted
//! `pub(crate)` for this reuse) — and resolves a relative path to at most one
//! zone label. This module ships the config/resolver layer only; no command
//! output or CLI flag wires into it yet (later tasks in the same spec).

use crate::vcs::ctxignore_matches;
use std::fs;
use std::path::Path;

/// Ordered `(label, glob)` entries parsed from `.ctxzones`, in declaration
/// order. Zero file present → zero entries → every lookup behaves as if no
/// zones exist.
pub struct ZoneConfig {
    entries: Vec<(String, String)>,
}

impl ZoneConfig {
    /// Load `.ctxzones` from `root`. A missing file yields an empty config,
    /// never an error — the caller treats "no zones declared" as the normal,
    /// common case.
    pub fn load(root: &Path) -> Self {
        let text = match fs::read_to_string(root.join(".ctxzones")) {
            Ok(t) => t,
            Err(_) => {
                return ZoneConfig {
                    entries: Vec::new(),
                };
            }
        };

        let mut entries = Vec::new();
        for line in text.lines() {
            let line = line.trim();
            if line.is_empty() || line.starts_with('#') {
                continue;
            }
            // A malformed line — no `:` separator, or a label outside the
            // pinned `[a-z0-9-]+` charset — is skipped rather than aborting
            // the whole load, so one bad line never takes the rest of the
            // file's declarations down with it.
            let Some((label, glob)) = line.split_once(':') else {
                continue;
            };
            let label = label.trim();
            let glob = glob.trim();
            if label.is_empty()
                || glob.is_empty()
                || !label
                    .chars()
                    .all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || c == '-')
            {
                continue;
            }
            entries.push((label.to_string(), glob.to_string()));
        }
        ZoneConfig { entries }
    }

    /// The zone label whose glob matches `rel`, first-match-wins in
    /// declaration order (a path carries a single tag). Reuses
    /// `.ctxignore`'s basename-vs-full-path matcher unchanged: a
    /// directory glob (trailing `/`) matches a path prefix, a glob
    /// containing `/` matches the full path, and a bare glob matches the
    /// basename.
    pub fn zone_of(&self, rel: &str) -> Option<&str> {
        self.entries
            .iter()
            .find(|(_, glob)| ctxignore_matches(std::slice::from_ref(glob), rel))
            .map(|(label, _)| label.as_str())
    }

    /// Every declared label, deduped, in first-declaration order.
    pub fn declared_labels(&self) -> Vec<&str> {
        let mut labels: Vec<&str> = Vec::new();
        for (label, _) in &self.entries {
            if !labels.contains(&label.as_str()) {
                labels.push(label.as_str());
            }
        }
        labels
    }
}
