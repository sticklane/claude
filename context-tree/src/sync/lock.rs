//! C6 advisory lock: concurrent syncs serialize on a filesystem lock, while a
//! query can non-blockingly observe whether a sync holds it and skip its own
//! staleness sweep.

use std::fs::{self, OpenOptions};
use std::io;
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant};

const LOCK_FILE: &str = ".sync.lock";

/// A held advisory lock. Released on drop.
pub struct AdvisoryLock {
    path: PathBuf,
}

impl AdvisoryLock {
    /// Non-blocking acquire: `Some(guard)` when the lock was free (the caller
    /// now holds it until drop), `None` when another holder has it.
    pub fn try_acquire(cache_dir: &Path) -> io::Result<Option<AdvisoryLock>> {
        fs::create_dir_all(cache_dir)?;
        let path = cache_dir.join(LOCK_FILE);
        match OpenOptions::new().write(true).create_new(true).open(&path) {
            Ok(_) => Ok(Some(AdvisoryLock { path })),
            Err(e) if e.kind() == io::ErrorKind::AlreadyExists => Ok(None),
            Err(e) => Err(e),
        }
    }

    /// Blocking acquire with a bounded wait — serializes concurrent syncs. A
    /// lock still held past the deadline is treated as stale (a crashed holder
    /// leaves the file behind) and stolen once.
    pub fn acquire(cache_dir: &Path) -> io::Result<AdvisoryLock> {
        let deadline = Instant::now() + Duration::from_secs(5);
        loop {
            if let Some(lock) = Self::try_acquire(cache_dir)? {
                return Ok(lock);
            }
            if Instant::now() >= deadline {
                let _ = fs::remove_file(cache_dir.join(LOCK_FILE));
                return Self::try_acquire(cache_dir)?.ok_or_else(|| {
                    io::Error::new(io::ErrorKind::WouldBlock, "sync advisory lock held")
                });
            }
            std::thread::sleep(Duration::from_millis(10));
        }
    }
}

impl Drop for AdvisoryLock {
    fn drop(&mut self) {
        let _ = fs::remove_file(&self.path);
    }
}
