//! `ctx hooks install` / `ctx hooks uninstall` (R16): opt-in pre-warm and
//! pre-commit git hooks plus a printed PostToolUse snippet.
//!
//! Hook files are managed as delimited marked blocks: install appends a `ctx`
//! block to an existing hook (creating an executable file only when absent,
//! flagged with an in-block sentinel), preserving all other content; uninstall
//! removes exactly that block and deletes only files ctx itself created. Under
//! git, install also enables `core.fsmonitor` when the builtin monitor is
//! supported and the setting is not already configured, tracking that it did so
//! via a `ctx.hooksFsmonitorSet` config marker so uninstall reverts only
//! settings it set. The internal `ctx hooks pre-commit` step (invoked by the
//! installed hook) writes each pending anchor update whose re-anchored NEW
//! file is itself staged, staging the touched note files — a partial commit
//! that leaves the moved-to file unstaged leaves that update pending.

use crate::index::IndexStore;
use crate::notes;
use crate::project;
use crate::sync::{self, journal::Trigger, lock::AdvisoryLock};
use std::collections::{HashMap, HashSet};
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::{Command, ExitCode};

/// Markers delimiting the ctx-managed block inside a hook file.
const MANAGED_BEGIN: &str = "# >>> ctx hooks (managed block; do not edit) >>>";
const MANAGED_END: &str = "# <<< ctx hooks (managed block) <<<";
/// Present inside the block only when ctx created the whole hook file, so
/// uninstall knows to delete it rather than strip the block.
const CREATED_SENTINEL: &str = "# ctx-created-file (ctx hooks uninstall deletes this file)";
/// Git config marker recording that ctx (not the user) set `core.fsmonitor`.
const FSMONITOR_MARK: &str = "ctx.hooksFsmonitorSet";

const PREWARM_BODY: &str = include_str!("../hooks_templates/prewarm.sh");
const PRECOMMIT_BODY: &str = include_str!("../hooks_templates/precommit.sh");
const POSTTOOLUSE_SNIPPET: &str = include_str!("../hooks_templates/posttooluse.txt");

const PREWARM_HOOKS: &[&str] = &["post-checkout", "post-merge", "post-commit"];
const ALL_HOOKS: &[&str] = &["post-checkout", "post-merge", "post-commit", "pre-commit"];

/// Which `ctx hooks` form is being run.
pub enum Action {
    Install,
    Uninstall,
    /// Internal: the pre-commit anchor-write step, invoked by the installed hook.
    PreCommit,
}

pub struct Args {
    pub action: Action,
}

pub fn run(args: Args) -> ExitCode {
    match args.action {
        Action::Install => install(),
        Action::Uninstall => uninstall(),
        Action::PreCommit => pre_commit(),
    }
}

fn cwd_or_fail() -> Result<PathBuf, ExitCode> {
    std::env::current_dir().map_err(|e| {
        eprintln!("ctx: cannot read current directory: {e}");
        ExitCode::FAILURE
    })
}

/// Run a git subcommand in `root`, returning trimmed stdout on success.
fn git(root: &Path, args: &[&str]) -> Option<String> {
    let out = Command::new("git")
        .current_dir(root)
        .args(args)
        .output()
        .ok()?;
    if out.status.success() {
        Some(String::from_utf8_lossy(&out.stdout).trim().to_string())
    } else {
        None
    }
}

fn git_root(cwd: &Path) -> Option<PathBuf> {
    git(cwd, &["rev-parse", "--show-toplevel"]).map(PathBuf::from)
}

/// The git hooks directory, honoring `core.hooksPath`.
fn hooks_dir(root: &Path) -> Option<PathBuf> {
    let p = git(root, &["rev-parse", "--git-path", "hooks"])?;
    let pb = PathBuf::from(&p);
    Some(if pb.is_absolute() { pb } else { root.join(pb) })
}

/// The absolute path to the running `ctx` binary, baked into installed hooks so
/// they resolve without relying on `PATH`.
fn ctx_bin() -> String {
    std::env::current_exe()
        .ok()
        .map(|p| p.to_string_lossy().to_string())
        .unwrap_or_else(|| "ctx".to_string())
}

/// Assemble a managed block around `body`. `created` adds the sentinel line.
fn managed_block(body: &str, created: bool) -> String {
    let mut b = String::new();
    b.push_str(MANAGED_BEGIN);
    b.push('\n');
    if created {
        b.push_str(CREATED_SENTINEL);
        b.push('\n');
    }
    b.push_str(body);
    if !body.ends_with('\n') {
        b.push('\n');
    }
    b.push_str(MANAGED_END);
    b.push('\n');
    b
}

/// Remove the managed block (BEGIN..END plus its trailing newline) from
/// `content`, preserving every other byte. A newline-terminated original is
/// restored byte-for-byte, since the block was appended after that terminator.
fn strip_block(content: &str) -> String {
    let Some(begin) = content.find(MANAGED_BEGIN) else {
        return content.to_string();
    };
    let Some(end_rel) = content[begin..].find(MANAGED_END) else {
        return content.to_string();
    };
    let mut cut_end = begin + end_rel + MANAGED_END.len();
    if content[cut_end..].starts_with('\n') {
        cut_end += 1;
    }
    format!("{}{}", &content[..begin], &content[cut_end..])
}

#[cfg(unix)]
fn set_executable(path: &Path) -> io::Result<()> {
    use std::os::unix::fs::PermissionsExt;
    let mut perms = fs::metadata(path)?.permissions();
    perms.set_mode(0o755);
    fs::set_permissions(path, perms)
}

#[cfg(not(unix))]
fn set_executable(_path: &Path) -> io::Result<()> {
    Ok(())
}

/// Install (or refresh) the ctx block in one hook file.
fn install_hook(path: &Path, body_template: &str) -> io::Result<()> {
    let body = body_template.replace("__CTX_BIN__", &ctx_bin());
    if path.exists() {
        let orig = fs::read_to_string(path)?;
        if orig.contains(CREATED_SENTINEL) {
            // ctx owns the whole file; rewrite it fresh.
            let block = managed_block(&body, true);
            fs::write(path, format!("#!/bin/sh\n{block}"))?;
        } else {
            let base = strip_block(&orig);
            let sep = if base.is_empty() || base.ends_with('\n') {
                ""
            } else {
                "\n"
            };
            let block = managed_block(&body, false);
            fs::write(path, format!("{base}{sep}{block}"))?;
        }
    } else {
        let block = managed_block(&body, true);
        fs::write(path, format!("#!/bin/sh\n{block}"))?;
    }
    set_executable(path)
}

/// Remove the ctx block from one hook file, deleting the file if ctx created it.
fn uninstall_hook(path: &Path) -> io::Result<()> {
    if !path.exists() {
        return Ok(());
    }
    let content = fs::read_to_string(path)?;
    if !content.contains(MANAGED_BEGIN) {
        return Ok(());
    }
    if content.contains(CREATED_SENTINEL) {
        fs::remove_file(path)
    } else {
        fs::write(path, strip_block(&content))
    }
}

/// Parse `git --version` into `(major, minor)`.
fn git_version(root: &Path) -> Option<(u32, u32)> {
    let v = git(root, &["--version"])?;
    let last = v.split_whitespace().next_back()?;
    let mut parts = last.split('.');
    let major = parts.next()?.parse().ok()?;
    let minor = parts.next().and_then(|s| s.parse().ok()).unwrap_or(0);
    Some((major, minor))
}

/// Enable `core.fsmonitor` when supported and not already set, returning the
/// one-line report of the decision.
fn install_fsmonitor(root: &Path) -> String {
    let Some((maj, min)) = git_version(root) else {
        return "fsmonitor: skipped (cannot determine git version)".to_string();
    };
    // The builtin fsmonitor daemon landed in git 2.37.
    if !(maj > 2 || (maj == 2 && min >= 37)) {
        return format!(
            "fsmonitor: skipped (git {maj}.{min} lacks the builtin monitor; needs >= 2.37)"
        );
    }
    if git(root, &["config", "--get", "core.fsmonitor"]).is_some() {
        return "fsmonitor: skipped (core.fsmonitor already configured)".to_string();
    }
    let _ = git(root, &["config", "core.fsmonitor", "true"]);
    let _ = git(root, &["config", FSMONITOR_MARK, "true"]);
    "fsmonitor: enabled".to_string()
}

/// Revert `core.fsmonitor` only when ctx itself set it.
fn uninstall_fsmonitor(root: &Path) {
    if git(root, &["config", "--get", FSMONITOR_MARK]).as_deref() == Some("true") {
        let _ = git(root, &["config", "--unset", "core.fsmonitor"]);
        let _ = git(root, &["config", "--unset", FSMONITOR_MARK]);
    }
}

fn print_snippet() {
    println!("\nPostToolUse hook snippet (edit-time note push):\n");
    print!("{POSTTOOLUSE_SNIPPET}");
}

fn install() -> ExitCode {
    let cwd = match cwd_or_fail() {
        Ok(c) => c,
        Err(code) => return code,
    };
    let Some(root) = git_root(&cwd) else {
        println!("ctx hooks: not a git repository — installing the PostToolUse snippet only.");
        print_snippet();
        return ExitCode::SUCCESS;
    };
    let Some(hooks) = hooks_dir(&root) else {
        eprintln!("ctx hooks install: cannot locate the git hooks directory");
        return ExitCode::FAILURE;
    };
    if let Err(e) = fs::create_dir_all(&hooks) {
        eprintln!("ctx hooks install: cannot create {}: {e}", hooks.display());
        return ExitCode::FAILURE;
    }
    for name in PREWARM_HOOKS {
        if let Err(e) = install_hook(&hooks.join(name), PREWARM_BODY) {
            eprintln!("ctx hooks install: cannot write {name}: {e}");
            return ExitCode::FAILURE;
        }
        println!("installed pre-warm hook: {name}");
    }
    if let Err(e) = install_hook(&hooks.join("pre-commit"), PRECOMMIT_BODY) {
        eprintln!("ctx hooks install: cannot write pre-commit: {e}");
        return ExitCode::FAILURE;
    }
    println!("installed pre-commit hook: pre-commit");
    println!("{}", install_fsmonitor(&root));
    print_snippet();
    ExitCode::SUCCESS
}

fn uninstall() -> ExitCode {
    let cwd = match cwd_or_fail() {
        Ok(c) => c,
        Err(code) => return code,
    };
    let Some(root) = git_root(&cwd) else {
        println!("ctx hooks: not a git repository — nothing to uninstall.");
        return ExitCode::SUCCESS;
    };
    let Some(hooks) = hooks_dir(&root) else {
        eprintln!("ctx hooks uninstall: cannot locate the git hooks directory");
        return ExitCode::FAILURE;
    };
    for name in ALL_HOOKS {
        if let Err(e) = uninstall_hook(&hooks.join(name)) {
            eprintln!("ctx hooks uninstall: cannot update {name}: {e}");
            return ExitCode::FAILURE;
        }
    }
    uninstall_fsmonitor(&root);
    println!("ctx hooks uninstalled");
    ExitCode::SUCCESS
}

/// The pre-commit anchor-write step (invoked by the installed hook). Writes each
/// pending anchor update whose re-anchored NEW file is in the git staged set and
/// stages the touched note file; leaves the rest pending. Best-effort — always
/// exits success so a ctx hiccup never blocks the commit.
fn pre_commit() -> ExitCode {
    let cwd = match cwd_or_fail() {
        Ok(c) => c,
        Err(code) => return code,
    };
    let Some(root) = project::find_root(&cwd) else {
        return ExitCode::SUCCESS;
    };
    // Phase 1: recompute pending re-anchors against the working tree.
    if let Err(e) = sync::run_sync(&root, Trigger::Hook) {
        eprintln!("ctx hooks pre-commit: sync failed: {e}");
        return ExitCode::SUCCESS;
    }
    let cache = sync::cache_dir(&root);
    let _lock = AdvisoryLock::acquire(&cache).ok();
    let store = match IndexStore::open(&cache) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("ctx hooks pre-commit: cannot open index: {e}");
            return ExitCode::SUCCESS;
        }
    };
    let pending = store.pending_reanchors().unwrap_or_default();
    if pending.is_empty() {
        return ExitCode::SUCCESS;
    }
    // Resolve each new qualified path to its current file.
    let symbols = store.all_symbols().unwrap_or_default();
    let file_of: HashMap<&str, &str> = symbols
        .iter()
        .map(|s| (s.qpath.as_str(), s.path.as_str()))
        .collect();
    // The git staged set (repo-relative paths).
    let staged: HashSet<String> = git(&root, &["diff", "--cached", "--name-only"])
        .map(|s| s.lines().map(str::to_string).collect())
        .unwrap_or_default();
    let (all_notes, _) = notes::load_all(&root);
    let note_path: HashMap<&str, &str> = all_notes
        .iter()
        .map(|n| (n.id.as_str(), n.rel_path.as_str()))
        .collect();

    let mut remaining: HashMap<String, String> = HashMap::new();
    for (note_id, new_qpath) in &pending {
        let staged_new = file_of
            .get(new_qpath.as_str())
            .is_some_and(|f| staged.contains(*f));
        if staged_new
            && let Some(rel) = note_path.get(note_id.as_str())
            && notes::rewrite_anchor_path(&root, rel, new_qpath).is_ok()
        {
            let _ = git(&root, &["add", "--", rel]);
            continue; // written and staged; drop from pending
        }
        // Moved-to file not staged (or note missing): leave the update pending.
        remaining.insert(note_id.clone(), new_qpath.clone());
    }
    let _ = store.replace_pending_reanchors(&remaining);
    ExitCode::SUCCESS
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn strip_block_restores_newline_terminated_original() {
        let orig = "#!/bin/sh\necho hi\n";
        let block = managed_block("do-thing\n", false);
        let installed = format!("{orig}{block}");
        assert_eq!(strip_block(&installed), orig);
    }

    #[test]
    fn strip_block_is_noop_without_a_block() {
        let plain = "#!/bin/sh\necho hi\n";
        assert_eq!(strip_block(plain), plain);
    }

    #[test]
    fn managed_block_created_carries_the_sentinel() {
        let block = managed_block("cmd\n", true);
        assert!(block.contains(CREATED_SENTINEL));
        assert!(block.starts_with(MANAGED_BEGIN));
        assert!(block.trim_end().ends_with(MANAGED_END));
    }
}
