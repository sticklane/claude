//! CLI surface (clap). Future tasks extend the [`Command`] enum with query and
//! note subcommands; task 01 ships `--version` and `ctx init`.

use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = "ctx", version, about = "Codebase context tree")]
pub struct Cli {
    #[command(subcommand)]
    pub command: Option<Command>,
}

#[derive(Subcommand)]
pub enum Command {
    /// Scaffold `.context/` at the project (or VCS) root; idempotent.
    Init,
    /// Incrementally update the index for the current project (R2).
    Sync {
        /// Print machine-readable `scanned=.. hashed=.. parsed=..` counts.
        #[arg(long)]
        stats: bool,
    },
    /// Containment outline for a path subtree (R6).
    Tree {
        /// Path (file or directory prefix) to outline.
        path: String,
        /// Cap the containment depth shown (top-level is depth 1).
        #[arg(long)]
        depth: Option<usize>,
        /// Cap the number of symbols shown before a truncation line.
        #[arg(long, default_value_t = 200)]
        limit: usize,
        /// Append each symbol's first docstring line.
        #[arg(long)]
        doc: bool,
        /// Emit JSON instead of plain text.
        #[arg(long)]
        json: bool,
        /// Skip the R3 staleness sweep and read the current snapshot.
        #[arg(long = "no-sync")]
        no_sync: bool,
    },
    /// Signature (and docstring) for a symbol, resolved by C3 suffix (R7).
    Sig {
        /// Symbol name or qualified-path suffix.
        symbol: String,
        /// Print the full docstring rather than only its first line.
        #[arg(long)]
        doc: bool,
        /// Emit JSON instead of plain text.
        #[arg(long)]
        json: bool,
        /// Skip the R3 staleness sweep and read the current snapshot.
        #[arg(long = "no-sync")]
        no_sync: bool,
    },
    /// Module-level import edges into or out of a path (R9).
    Deps {
        /// Path (file or directory prefix) whose import edges to show.
        path: String,
        /// Show edges INTO the path (importers) rather than OUT of it.
        #[arg(long)]
        reverse: bool,
        /// Emit JSON instead of plain text.
        #[arg(long)]
        json: bool,
        /// Skip the R3 staleness sweep and read the current snapshot.
        #[arg(long = "no-sync")]
        no_sync: bool,
    },
    /// Definitions and references for a symbol, resolved by C3 suffix (R10).
    Refs {
        /// Symbol name or qualified-path suffix.
        symbol: String,
        /// Cap on results shown per direction before a truncation line.
        #[arg(long, default_value_t = 50)]
        limit: usize,
        /// Emit JSON instead of plain text.
        #[arg(long)]
        json: bool,
        /// Skip the R3 staleness sweep and read the current snapshot.
        #[arg(long = "no-sync")]
        no_sync: bool,
    },
    /// Innermost enclosing symbol + containment chain for a `file:line` (R19).
    At {
        /// Position as `<file>:<line>` (1-based line).
        position: String,
        /// Emit JSON instead of plain text.
        #[arg(long)]
        json: bool,
        /// Skip the R3 staleness sweep and read the current snapshot.
        #[arg(long = "no-sync")]
        no_sync: bool,
    },
    /// Ranked project overview by reference-graph importance (R8).
    Map {
        /// Token budget for the output (C7: ceil(bytes/4)).
        #[arg(long, default_value_t = 1000)]
        tokens: usize,
        /// Append each symbol's first docstring line, counted within the budget.
        #[arg(long)]
        doc: bool,
        /// Emit JSON instead of plain text.
        #[arg(long)]
        json: bool,
        /// Skip the R3 staleness sweep and read the current snapshot.
        #[arg(long = "no-sync")]
        no_sync: bool,
    },
}
