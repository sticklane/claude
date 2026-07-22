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
//! configured language server available". [`client::RustAnalyzerResolver`],
//! [`client::GoplsResolver`], and [`client::TypeScriptResolver`] implement it
//! against a live server each; a test double implements it deterministically.
//! [`enrich`] runs ONE resolver over every indexed symbol; [`enrich_exact`]
//! (task 01 / R2 / F1(i), `ctx refs --exact`'s on-demand trigger) instead
//! dispatches per symbol via [`client::resolver_for_extension`], so a
//! mixed-language repo gets each symbol resolved by its own language's
//! server. Both write the cache stamped with the index's current
//! [`generation`]; [`EnrichmentCache::load`] + [`EnrichmentCache::is_precise`]
//! / [`EnrichmentCache::precise_def`] / [`EnrichmentCache::signature`] are the
//! documented interface `cmd/refs.rs` reads it through.

pub mod client;

use crate::index::{IndexStore, SymbolRow};
use crate::sync::cache_dir;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::collections::{HashMap, HashSet};
use std::io;
use std::path::Path;

/// Sidecar file name under the derived cache dir. Deliberately a separate file
/// from the SQLite index so enrichment never touches the shared schema.
const CACHE_FILE: &str = "lsp-enrichment.json";

/// A precise reference occurrence a language server confirmed: the referenced
/// `name`, its owning repo-relative `path`, its 1-based `line`, and the
/// qualified path of the DEFINITION whose resolver call confirmed it
/// (task 01 / R2 — disambiguates two same-named symbols, e.g. the
/// `main.rodSpecs`-in-two-packages case, by attributing each reference to
/// the specific definition an LSP server resolved it against rather than to
/// "this name" generically).
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct PreciseRef {
    pub name: String,
    pub path: String,
    pub line: usize,
    pub def_qpath: String,
}

/// A generation stamp derived from the index's current symbol content — the
/// enrichment cache's invalidation key (task 01 / R2's "cached ... with a
/// generation stamp that invalidates when the index changes"). Built from
/// each symbol's C2 body hash rather than the index's `last_sync` timestamp,
/// so a no-op sync tick (nothing actually changed) does not spuriously
/// invalidate a warm cache — only a real content change does.
pub fn generation(symbols: &[SymbolRow]) -> i64 {
    let mut parts: Vec<(&str, &str)> = symbols
        .iter()
        .map(|s| (s.path.as_str(), s.body_hash.as_str()))
        .collect();
    parts.sort_unstable();
    let mut hasher = Sha256::new();
    for (path, hash) in parts {
        hasher.update(path.as_bytes());
        hasher.update(b"\0");
        hasher.update(hash.as_bytes());
        hasher.update(b"\n");
    }
    let digest = hasher.finalize();
    i64::from_be_bytes(digest[..8].try_into().unwrap())
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
    generation: i64,
}

impl EnrichmentCache {
    /// Is the reference `name` at `path:line` (1-based) confirmed precise by
    /// SOME definition's resolution?
    pub fn is_precise(&self, name: &str, path: &str, line: usize) -> bool {
        self.precise_def(name, path, line).is_some()
    }

    /// The qualified path of the DEFINITION whose resolver call confirmed the
    /// reference `name` at `path:line` (1-based) as precise, if any — the
    /// disambiguation `cmd/refs.rs`'s `--exact` path reads to attribute a
    /// reference to the correct one of several same-named definitions.
    pub fn precise_def(&self, name: &str, path: &str, line: usize) -> Option<&str> {
        self.precise
            .iter()
            .find(|r| r.name == name && r.path == path && r.line == line)
            .map(|r| r.def_qpath.as_str())
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

    /// Load the sidecar for `root`, or `None` when it is absent, unreadable,
    /// or STALE — its recorded [`generation`] no longer matches the index's
    /// current content (enrichment is optional and the cache is a pure
    /// accelerator: a missing/corrupt/stale sidecar degrades to
    /// heuristic-only, never an error).
    pub fn load(root: &Path) -> Option<EnrichmentCache> {
        let cache = Self::load_raw(root)?;
        let store = IndexStore::open(&cache_dir(root)).ok()?;
        let symbols = store.all_symbols().ok()?;
        if cache.generation != generation(&symbols) {
            return None;
        }
        Some(cache)
    }

    fn load_raw(root: &Path) -> Option<EnrichmentCache> {
        let path = cache_dir(root).join(CACHE_FILE);
        let bytes = std::fs::read(path).ok()?;
        let v: Value = serde_json::from_slice(&bytes).ok()?;
        let mut cache = EnrichmentCache {
            generation: v.get("generation").and_then(Value::as_i64).unwrap_or(0),
            ..Default::default()
        };
        for r in v.get("references")?.as_array()? {
            let name = r.get("name")?.as_str()?.to_string();
            let path = r.get("path")?.as_str()?.to_string();
            let line = r.get("line")?.as_u64()? as usize;
            let def_qpath = r
                .get("def_qpath")
                .and_then(Value::as_str)
                .unwrap_or("")
                .to_string();
            cache.precise.insert(PreciseRef {
                name,
                path,
                line,
                def_qpath,
            });
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
            .map(|r| json!({ "name": r.name, "path": r.path, "line": r.line, "def_qpath": r.def_qpath }))
            .collect();
        let signatures: serde_json::Map<String, Value> = self
            .signatures
            .iter()
            .map(|(k, v)| (k.clone(), json!(v)))
            .collect();
        let doc = json!({
            "generation": self.generation,
            "references": references,
            "signatures": signatures,
        });
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
    enrich_with(root, |_sym| Some(resolver))
}

/// Task 01 / R2 / F1(i): per-language resolver dispatch. For every indexed
/// symbol, picks the resolver matching its file's language (via
/// [`client::resolver_for_extension`]) and skips symbols whose language has no
/// available server binary — those stay heuristic, never erroring the pass.
/// This is what `cmd/refs.rs`'s `--exact` path calls on demand when no
/// current-generation cache exists.
pub fn enrich_exact(root: &Path) -> io::Result<EnrichmentCache> {
    enrich_with(root, |sym| {
        let ext = Path::new(&sym.path)
            .extension()
            .and_then(|e| e.to_str())
            .unwrap_or("");
        client::resolver_for_extension(ext)
    })
}

/// Shared enrichment loop: `pick` selects the resolver for each symbol (a
/// constant resolver for [`enrich`], per-language dispatch for
/// [`enrich_exact`]); `None` leaves that symbol heuristic. Stamps the written
/// cache with the index's current [`generation`] so a later [`EnrichmentCache::load`]
/// can tell a stale cache from a fresh one.
fn enrich_with<'a>(
    root: &Path,
    pick: impl Fn(&SymbolRow) -> Option<&'a dyn ReferenceResolver>,
) -> io::Result<EnrichmentCache> {
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
        let Some(resolver) = pick(sym) else {
            continue;
        };
        let candidates: Vec<PreciseRef> = all_refs
            .iter()
            .filter(|r| r.name == sym.name)
            .map(|r| PreciseRef {
                name: r.name.clone(),
                path: r.path.clone(),
                line: r.row + 1,
                def_qpath: sym.qpath.clone(),
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
                // The resolver confirms candidates by (name, path, line) only;
                // attribute each to THIS definition regardless of what it
                // echoed back, so two same-named definitions never bleed into
                // each other's attribution.
                cache.precise.insert(PreciseRef {
                    def_qpath: sym.qpath.clone(),
                    ..r
                });
            }
            if let Some(sig) = resolved.signature {
                cache.signatures.insert(sym.qpath.clone(), sig);
            }
        }
    }
    cache.generation = generation(&symbols);
    cache.write(root)?;
    Ok(cache)
}
