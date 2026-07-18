//! LSP enrichment (R11): an optional, additive pass that upgrades `ctx refs`
//! results from `heuristic` to `precise` when a language server is configured.
//!
//! The enrichment is **self-contained**: it stores its results in a JSON sidecar
//! (`.context/cache/lsp-enrichment.json`), never a write into the shared SQLite
//! index (task 09 owns the only other in-flight change to that schema, and
//! keeping enrichment out of it avoids a second task touching the same file).
//! With no server configured the sidecar is simply absent and every query still
//! works from syntactic facts alone — enrichment never blocks, and is never
//! required for, any command.
//!
//! The pass is generic over a [`ReferenceResolver`] — the abstraction of "a
//! configured language server available". [`client::RustAnalyzerResolver`]
//! implements it against a live `rust-analyzer`; a test double implements it
//! deterministically. [`enrich`] runs a resolver over the indexed symbols and
//! writes the cache; [`EnrichmentCache::load`] + [`EnrichmentCache::is_precise`]
//! / [`EnrichmentCache::signature`] are the documented interface `cmd/refs.rs`
//! reads it through.

pub mod client;

use crate::sync::cache_dir;
use serde_json::{Value, json};
use std::collections::{HashMap, HashSet};
use std::io;
use std::path::Path;

/// Sidecar file name under the derived cache dir. Deliberately a separate file
/// from the SQLite index so enrichment never touches the shared schema.
const CACHE_FILE: &str = "lsp-enrichment.json";

/// A precise reference occurrence a language server confirmed: the referenced
/// `name`, its owning repo-relative `path`, and its 1-based `line`.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct PreciseRef {
    pub name: String,
    pub path: String,
    pub line: usize,
}

/// A definition the enrichment pass asks a resolver about: the symbol `name`,
/// the repo-relative `file` and 0-based (`line0`, `col0`) position of its
/// identifier, and the heuristic reference occurrences the syntactic index
/// already found for that name (`candidates`). A resolver returns the subset it
/// confirms as precise.
#[derive(Debug, Clone)]
pub struct ResolveTarget {
    pub name: String,
    pub qpath: String,
    pub file: String,
    pub line0: usize,
    pub col0: usize,
    pub candidates: Vec<PreciseRef>,
}

/// What a resolver returns for one [`ResolveTarget`]: the confirmed-precise
/// references and, optionally, a resolved signature for the definition.
#[derive(Debug, Clone, Default)]
pub struct Resolved {
    pub refs: Vec<PreciseRef>,
    pub signature: Option<String>,
}

/// A configured language server capable of precise resolution (R11). The
/// enrichment pass is generic over this trait so any server — or a test double —
/// can back it. An `Err` for a target means the server could not resolve it;
/// enrichment then leaves that target heuristic rather than failing the whole
/// pass, so a flaky or partial server never regresses syntactic results.
pub trait ReferenceResolver {
    fn resolve(&self, root: &Path, target: &ResolveTarget) -> io::Result<Resolved>;
}

/// The enrichment sidecar: the set of precise reference occurrences and the map
/// of qualified path to resolved signature. Absent file => `None` from
/// [`load`](EnrichmentCache::load), which is the "no server configured" case.
#[derive(Debug, Clone, Default)]
pub struct EnrichmentCache {
    precise: HashSet<PreciseRef>,
    signatures: HashMap<String, String>,
}

impl EnrichmentCache {
    /// Is the reference `name` at `path:line` (1-based) confirmed precise?
    pub fn is_precise(&self, name: &str, path: &str, line: usize) -> bool {
        self.precise.contains(&PreciseRef {
            name: name.to_string(),
            path: path.to_string(),
            line,
        })
    }

    /// The resolved signature for `qpath`, if the server produced one.
    pub fn signature(&self, qpath: &str) -> Option<&str> {
        self.signatures.get(qpath).map(String::as_str)
    }

    /// True when the pass confirmed no precise data — an empty cache reads the
    /// same as no cache to consumers.
    pub fn is_empty(&self) -> bool {
        self.precise.is_empty() && self.signatures.is_empty()
    }

    /// Load the sidecar for `root`, or `None` when it is absent or unreadable
    /// (enrichment is optional — a missing/corrupt sidecar degrades to
    /// heuristic-only, never an error).
    pub fn load(root: &Path) -> Option<EnrichmentCache> {
        let path = cache_dir(root).join(CACHE_FILE);
        let bytes = std::fs::read(path).ok()?;
        let v: Value = serde_json::from_slice(&bytes).ok()?;
        let mut cache = EnrichmentCache::default();
        for r in v.get("references")?.as_array()? {
            let name = r.get("name")?.as_str()?.to_string();
            let path = r.get("path")?.as_str()?.to_string();
            let line = r.get("line")?.as_u64()? as usize;
            cache.precise.insert(PreciseRef { name, path, line });
        }
        if let Some(sigs) = v.get("signatures").and_then(Value::as_object) {
            for (qpath, sig) in sigs {
                if let Some(s) = sig.as_str() {
                    cache.signatures.insert(qpath.clone(), s.to_string());
                }
            }
        }
        Some(cache)
    }

    /// Serialize to the sidecar under `root`'s derived cache dir.
    fn write(&self, root: &Path) -> io::Result<()> {
        let mut refs: Vec<&PreciseRef> = self.precise.iter().collect();
        refs.sort_by(|a, b| (&a.path, a.line, &a.name).cmp(&(&b.path, b.line, &b.name)));
        let references: Vec<Value> = refs
            .iter()
            .map(|r| json!({ "name": r.name, "path": r.path, "line": r.line }))
            .collect();
        let signatures: serde_json::Map<String, Value> = self
            .signatures
            .iter()
            .map(|(k, v)| (k.clone(), json!(v)))
            .collect();
        let doc = json!({ "references": references, "signatures": signatures });
        let dir = cache_dir(root);
        std::fs::create_dir_all(&dir)?;
        std::fs::write(dir.join(CACHE_FILE), serde_json::to_vec_pretty(&doc)?)
    }
}

/// 0-based (line, col) of `byte` within the file at `root/rel`. Falls back to
/// `(0, 0)` when the source can't be read.
fn line_col0(root: &Path, rel: &str, byte: usize) -> (usize, usize) {
    let Ok(bytes) = std::fs::read(root.join(rel)) else {
        return (0, 0);
    };
    let upto = &bytes[..byte.min(bytes.len())];
    let line = upto.iter().filter(|&&b| b == b'\n').count();
    let col = match upto.iter().rposition(|&b| b == b'\n') {
        Some(nl) => upto.len() - nl - 1,
        None => upto.len(),
    };
    (line, col)
}

/// Run `resolver` over every symbol in `root`'s index and write the enrichment
/// sidecar. Reads the index read-only to enumerate symbols and their heuristic
/// references; a resolver error on any single symbol is swallowed so the pass
/// still records whatever the server did resolve. The returned cache is also
/// persisted to disk.
pub fn enrich(root: &Path, resolver: &dyn ReferenceResolver) -> io::Result<EnrichmentCache> {
    // Sweep so we read current facts — `ctx init` only scaffolds; the index is
    // populated on the first query sweep.
    let store = crate::sync::query_sweep(root)?;
    let symbols = store
        .all_symbols()
        .map_err(|e| io::Error::other(e.to_string()))?;
    let all_refs = store
        .all_references()
        .map_err(|e| io::Error::other(e.to_string()))?;

    let mut cache = EnrichmentCache::default();
    for sym in &symbols {
        let candidates: Vec<PreciseRef> = all_refs
            .iter()
            .filter(|r| r.name == sym.name)
            .map(|r| PreciseRef {
                name: r.name.clone(),
                path: r.path.clone(),
                line: r.row + 1,
            })
            .collect();
        let (line0, col0) = line_col0(root, &sym.path, sym.ident_start_byte);
        let target = ResolveTarget {
            name: sym.name.clone(),
            qpath: sym.qpath.clone(),
            file: sym.path.clone(),
            line0,
            col0,
            candidates,
        };
        if let Ok(resolved) = resolver.resolve(root, &target) {
            for r in resolved.refs {
                cache.precise.insert(r);
            }
            if let Some(sig) = resolved.signature {
                cache.signatures.insert(sym.qpath.clone(), sig);
            }
        }
    }
    cache.write(root)?;
    Ok(cache)
}
