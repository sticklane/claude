//! C5 sync journal: every sync appends one JSON line to
//! `.context/cache/sync-journal.jsonl` — the synchronization point for
//! observing background syncs.

use std::fs::OpenOptions;
use std::io::{self, Write};
use std::path::Path;
use std::time::{SystemTime, UNIX_EPOCH};

/// What kicked off a sync (C5's `trigger` field).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Trigger {
    /// A query's staleness sweep.
    Query,
    /// An explicit `ctx sync` invocation.
    Cli,
    /// A VCS hook (task 10).
    Hook,
}

impl Trigger {
    pub fn as_str(self) -> &'static str {
        match self {
            Trigger::Query => "query",
            Trigger::Cli => "cli",
            Trigger::Hook => "hook",
        }
    }
}

/// One C5 journal record. `pending_reanchors` is stubbed at 0 until task 10's
/// R13 phase-2 anchor updates populate it.
pub struct JournalRecord {
    pub trigger: Trigger,
    pub scanned: usize,
    pub hashed: usize,
    pub parsed: usize,
    pub pending_reanchors: usize,
}

/// Append one JSON line to `<cache_dir>/sync-journal.jsonl`. The record has no
/// user-controlled string fields, so a hand-built object needs no escaping.
pub fn append(cache_dir: &Path, rec: &JournalRecord) -> io::Result<()> {
    let line = format!(
        "{{\"timestamp\":\"{}\",\"trigger\":\"{}\",\"scanned\":{},\"hashed\":{},\"parsed\":{},\"pending_reanchors\":{}}}\n",
        now_utc_rfc3339(),
        rec.trigger.as_str(),
        rec.scanned,
        rec.hashed,
        rec.parsed,
        rec.pending_reanchors,
    );
    let mut file = OpenOptions::new()
        .create(true)
        .append(true)
        .open(cache_dir.join("sync-journal.jsonl"))?;
    file.write_all(line.as_bytes())
}

/// The current UTC time as an RFC 3339 / ISO 8601 string (`...Z`), built from
/// `SystemTime` without a date-library dependency.
pub fn now_utc_rfc3339() -> String {
    let secs = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs() as i64)
        .unwrap_or(0);
    format_rfc3339(secs)
}

fn format_rfc3339(epoch_secs: i64) -> String {
    let days = epoch_secs.div_euclid(86_400);
    let secs_of_day = epoch_secs.rem_euclid(86_400);
    let (y, m, d) = civil_from_days(days);
    let (hh, mm, ss) = (
        secs_of_day / 3600,
        (secs_of_day % 3600) / 60,
        secs_of_day % 60,
    );
    format!("{y:04}-{m:02}-{d:02}T{hh:02}:{mm:02}:{ss:02}Z")
}

/// Howard Hinnant's `civil_from_days`: convert a day count since the Unix epoch
/// to a `(year, month, day)` civil date.
fn civil_from_days(z: i64) -> (i64, u32, u32) {
    let z = z + 719_468;
    let era = if z >= 0 { z } else { z - 146_096 } / 146_097;
    let doe = z - era * 146_097; // [0, 146096]
    let yoe = (doe - doe / 1460 + doe / 36_524 - doe / 146_096) / 365; // [0, 399]
    let y = yoe + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100); // [0, 365]
    let mp = (5 * doy + 2) / 153; // [0, 11]
    let d = (doy - (153 * mp + 2) / 5 + 1) as u32; // [1, 31]
    let m = if mp < 10 { mp + 3 } else { mp - 9 } as u32; // [1, 12]
    (if m <= 2 { y + 1 } else { y }, m, d)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn format_rfc3339_renders_a_known_epoch() {
        // 2021-01-01T00:00:00Z is 1609459200 seconds since the epoch.
        assert_eq!(format_rfc3339(1_609_459_200), "2021-01-01T00:00:00Z");
    }

    #[test]
    fn format_rfc3339_renders_time_of_day() {
        // 2021-01-01T01:02:03Z.
        assert_eq!(format_rfc3339(1_609_459_200 + 3723), "2021-01-01T01:02:03Z");
    }
}
