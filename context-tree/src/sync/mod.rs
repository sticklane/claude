//! R2 sync engine: incrementally updates the SQLite index. (STUB — the scan
//! algorithm lands in the GREEN step.)

pub mod journal;
pub mod lock;

use crate::index::IndexStore;
use journal::Trigger;
use std::io;
use std::path::{Path, PathBuf};

/// `ctx sync --stats` counts (R2).
#[derive(Debug, Default, Clone, Copy, PartialEq, Eq)]
pub struct SyncStats {
    pub scanned: usize,
    pub hashed: usize,
    pub parsed: usize,
}

/// The derived-index cache directory for a project root.
pub fn cache_dir(root: &Path) -> PathBuf {
    root.join(crate::project::CONTEXT_DIR).join("cache")
}

fn to_io(e: rusqlite::Error) -> io::Error {
    io::Error::other(e.to_string())
}

/// Incrementally sync the index under `root`. (STUB.)
pub fn run_sync(root: &Path, _trigger: Trigger) -> io::Result<SyncStats> {
    std::fs::create_dir_all(cache_dir(root))?;
    Ok(SyncStats::default())
}

/// A query's staleness sweep (C6). (STUB.)
pub fn query_sweep(root: &Path) -> io::Result<IndexStore> {
    IndexStore::open(&cache_dir(root)).map_err(to_io)
}
