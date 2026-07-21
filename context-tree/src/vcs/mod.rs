//! R5 VCS adapter: isolates change feeds, ignore rules, snapshot identity,
//! user identity, and hook points behind one trait. v1 ships a [`GitAdapter`]
//! and a [`NoVcsBaseline`] (a plain directory that never saw version control).

use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::Command;

/// The interface every sync runs through. The default methods make the
/// change-feed/snapshot/identity/hook surface optional, so the baseline only
/// implements the ignore + file-listing it actually has.
pub trait VcsAdapter {
    /// Adapter name for diagnostics (`"git"` / `"none"`).
    fn name(&self) -> &'static str;

    /// Repo-relative paths of every non-ignored file under `root` (R4/R5). The
    /// `.context/` subtree is always excluded by the caller regardless.
    fn list_files(&self, root: &Path) -> io::Result<Vec<String>>;

    /// R4: is this repo-relative path ignored?
    fn is_ignored(&self, root: &Path, rel: &str) -> bool;

    /// R2 change feed: changed paths since the last snapshot, or `None` when
    /// the adapter offers none and the caller falls back to a full mtime scan.
    fn change_feed(&self, _root: &Path) -> Option<Vec<String>> {
        None
    }

    /// Snapshot identity (e.g. a commit SHA); `None` when unavailable.
    fn snapshot_id(&self, _root: &Path) -> Option<String> {
        None
    }

    /// User identity (e.g. committer email); `None` when unknown.
    fn user_identity(&self, _root: &Path) -> Option<String> {
        None
    }

    /// Where this VCS's hooks live; `None` for the baseline.
    fn hook_dir(&self, _root: &Path) -> Option<PathBuf> {
        None
    }
}

/// Select the adapter for `root`: the git adapter when a `.git` is present at
/// or above `root`, else the no-VCS baseline (R5). Every non-baseline adapter
/// is wrapped in the [`CtxignoreOverlay`] so `.ctxignore` is honored under any
/// VCS; the baseline already applies `.ctxignore` internally and is returned
/// unwrapped, never double-subtracted.
pub fn detect(root: &Path) -> Box<dyn VcsAdapter> {
    if crate::project::git_root(root).is_some() {
        Box::new(CtxignoreOverlay {
            inner: Box::new(GitAdapter),
        })
    } else {
        Box::new(NoVcsBaseline)
    }
}

/// A VCS-independent `.ctxignore` exclusion overlay wrapping any non-baseline
/// adapter. It is purely subtractive: file lists drop `.ctxignore` matches and
/// `is_ignored` ORs the overlay in, so a `.ctxignore` entry can only remove
/// paths, never re-include what the inner VCS already ignores. Every other
/// `VcsAdapter` method delegates verbatim to the inner adapter, so change
/// feeds, snapshot identity, user identity, and hook location are unchanged.
struct CtxignoreOverlay {
    inner: Box<dyn VcsAdapter>,
}

impl VcsAdapter for CtxignoreOverlay {
    fn name(&self) -> &'static str {
        self.inner.name()
    }

    fn list_files(&self, root: &Path) -> io::Result<Vec<String>> {
        let patterns = load_ctxignore(root);
        let mut files = self.inner.list_files(root)?;
        files.retain(|rel| !ctxignore_matches(&patterns, rel));
        Ok(files)
    }

    fn is_ignored(&self, root: &Path, rel: &str) -> bool {
        self.inner.is_ignored(root, rel) || ctxignore_matches(&load_ctxignore(root), rel)
    }

    fn change_feed(&self, root: &Path) -> Option<Vec<String>> {
        self.inner.change_feed(root)
    }

    fn snapshot_id(&self, root: &Path) -> Option<String> {
        self.inner.snapshot_id(root)
    }

    fn user_identity(&self, root: &Path) -> Option<String> {
        self.inner.user_identity(root)
    }

    fn hook_dir(&self, root: &Path) -> Option<PathBuf> {
        self.inner.hook_dir(root)
    }
}

/// Git-backed adapter. Ignore rules and file enumeration come from git itself,
/// so `.gitignore`, `.git/info/exclude`, and global excludes are all honored.
pub struct GitAdapter;

impl VcsAdapter for GitAdapter {
    fn name(&self) -> &'static str {
        "git"
    }

    fn list_files(&self, root: &Path) -> io::Result<Vec<String>> {
        // Tracked + untracked-but-not-ignored, NUL-delimited so paths with
        // spaces/newlines survive.
        let out = Command::new("git")
            .current_dir(root)
            .args([
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "-z",
            ])
            .output()?;
        if !out.status.success() {
            return Err(io::Error::other("git ls-files failed"));
        }
        let mut files: Vec<String> = out
            .stdout
            .split(|&b| b == 0)
            .filter(|s| !s.is_empty())
            .filter_map(|s| std::str::from_utf8(s).ok().map(str::to_string))
            .collect();
        files.sort();
        files.dedup();
        Ok(files)
    }

    fn is_ignored(&self, root: &Path, rel: &str) -> bool {
        Command::new("git")
            .current_dir(root)
            .args(["check-ignore", "-q", "--", rel])
            .status()
            .map(|s| s.success())
            .unwrap_or(false)
    }

    fn snapshot_id(&self, root: &Path) -> Option<String> {
        let out = Command::new("git")
            .current_dir(root)
            .args(["rev-parse", "HEAD"])
            .output()
            .ok()?;
        if !out.status.success() {
            return None;
        }
        let s = String::from_utf8_lossy(&out.stdout).trim().to_string();
        (!s.is_empty()).then_some(s)
    }

    fn user_identity(&self, root: &Path) -> Option<String> {
        let out = Command::new("git")
            .current_dir(root)
            .args(["config", "user.email"])
            .output()
            .ok()?;
        if !out.status.success() {
            return None;
        }
        let s = String::from_utf8_lossy(&out.stdout).trim().to_string();
        (!s.is_empty()).then_some(s)
    }

    fn hook_dir(&self, root: &Path) -> Option<PathBuf> {
        crate::project::git_root(root).map(|g| g.join(".git").join("hooks"))
    }
}

/// No-VCS baseline: a plain-directory walk honoring `.ctxignore` (R4/R5).
pub struct NoVcsBaseline;

impl VcsAdapter for NoVcsBaseline {
    fn name(&self) -> &'static str {
        "none"
    }

    fn list_files(&self, root: &Path) -> io::Result<Vec<String>> {
        let patterns = load_ctxignore(root);
        let mut out = Vec::new();
        walk(root, root, &patterns, &mut out)?;
        out.sort();
        Ok(out)
    }

    fn is_ignored(&self, root: &Path, rel: &str) -> bool {
        ctxignore_matches(&load_ctxignore(root), rel)
    }
}

fn load_ctxignore(root: &Path) -> Vec<String> {
    match fs::read_to_string(root.join(".ctxignore")) {
        Ok(text) => text
            .lines()
            .map(str::trim)
            .filter(|l| !l.is_empty() && !l.starts_with('#'))
            .map(str::to_string)
            .collect(),
        Err(_) => Vec::new(),
    }
}

fn walk(root: &Path, dir: &Path, patterns: &[String], out: &mut Vec<String>) -> io::Result<()> {
    for entry in fs::read_dir(dir)? {
        let entry = entry?;
        let name = entry.file_name();
        let name = name.to_string_lossy();
        // The VCS metadata dir and the derived cache/notes tree are never
        // indexed (R4), independent of any ignore entry.
        if name == ".git" || name == crate::project::CONTEXT_DIR {
            continue;
        }
        let path = entry.path();
        let rel = path
            .strip_prefix(root)
            .unwrap_or(&path)
            .to_string_lossy()
            .replace('\\', "/");
        let ty = entry.file_type()?;
        if ty.is_dir() {
            if ctxignore_matches(patterns, &rel) || ctxignore_matches(patterns, &format!("{rel}/"))
            {
                continue;
            }
            walk(root, &path, patterns, out)?;
        } else if ty.is_file() {
            if ctxignore_matches(patterns, &rel) {
                continue;
            }
            out.push(rel);
        }
    }
    Ok(())
}

/// Minimal `.gitignore`-style matcher for the no-VCS baseline: blank/`#` lines
/// are dropped by the loader; a trailing `/` marks a directory prefix; a
/// pattern without `/` matches the basename; otherwise the whole path. `*` and
/// `?` are the supported wildcards.
fn ctxignore_matches(patterns: &[String], rel: &str) -> bool {
    let base = rel.rsplit('/').next().unwrap_or(rel);
    for p in patterns {
        if let Some(dir) = p.strip_suffix('/') {
            if rel == dir || rel.starts_with(&format!("{dir}/")) {
                return true;
            }
        } else if p.contains('/') {
            if glob_match(p, rel) {
                return true;
            }
        } else if glob_match(p, base) {
            return true;
        }
    }
    false
}

/// Wildcard match supporting `*` (any run) and `?` (one char), with linear
/// backtracking.
fn glob_match(pat: &str, text: &str) -> bool {
    let p: Vec<char> = pat.chars().collect();
    let t: Vec<char> = text.chars().collect();
    let (mut i, mut j) = (0usize, 0usize);
    let mut star: Option<usize> = None;
    let mut mark = 0usize;
    while j < t.len() {
        if i < p.len() && (p[i] == '?' || p[i] == t[j]) {
            i += 1;
            j += 1;
        } else if i < p.len() && p[i] == '*' {
            star = Some(i);
            mark = j;
            i += 1;
        } else if let Some(s) = star {
            i = s + 1;
            mark += 1;
            j = mark;
        } else {
            return false;
        }
    }
    while i < p.len() && p[i] == '*' {
        i += 1;
    }
    i == p.len()
}
