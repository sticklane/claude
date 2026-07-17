//! C4 project-root discovery and `ctx init` scaffolding (R18 idempotent).

use std::fs;
use std::io;
use std::path::{Path, PathBuf};

pub const CONTEXT_DIR: &str = ".context";
const GITIGNORE_BODY: &str = "cache/\n";

/// C4: nearest ancestor (inclusive) containing a `.context/` directory.
pub fn find_root(start: &Path) -> Option<PathBuf> {
    let mut cur = Some(start);
    while let Some(dir) = cur {
        if dir.join(CONTEXT_DIR).is_dir() {
            return Some(dir.to_path_buf());
        }
        cur = dir.parent();
    }
    None
}

/// The git adapter's root: nearest ancestor (inclusive) containing `.git`.
/// Only `ctx init` consults this — to decide where to scaffold (C4).
pub fn git_root(start: &Path) -> Option<PathBuf> {
    let mut cur = Some(start);
    while let Some(dir) = cur {
        if dir.join(".git").exists() {
            return Some(dir.to_path_buf());
        }
        cur = dir.parent();
    }
    None
}

/// Scaffold the `.context/` layout per C4, idempotently (R18): `notes/`
/// (version-tracked), `cache/` (derived, ignored), and a managed
/// `.context/.gitignore` ignoring `cache/`. Re-running on an initialized root
/// changes nothing. Returns the root where scaffolding landed.
pub fn init(start: &Path) -> io::Result<PathBuf> {
    let root = find_root(start)
        .or_else(|| git_root(start))
        .unwrap_or_else(|| start.to_path_buf());
    let ctx = root.join(CONTEXT_DIR);
    fs::create_dir_all(ctx.join("notes"))?;
    fs::create_dir_all(ctx.join("cache"))?;

    // Only (re)write the managed .gitignore when absent or divergent, so an
    // idempotent re-run leaves the tree byte-for-byte unchanged.
    let gitignore = ctx.join(".gitignore");
    let needs_write = match fs::read_to_string(&gitignore) {
        Ok(existing) => existing != GITIGNORE_BODY,
        Err(_) => true,
    };
    if needs_write {
        fs::write(&gitignore, GITIGNORE_BODY)?;
    }
    Ok(root)
}
