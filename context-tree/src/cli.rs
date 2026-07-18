//! CLI surface (clap). Future tasks extend the [`Command`] enum with query and
//! note subcommands; task 01 ships `--version` and `ctx init`.

use clap::{Args, Parser, Subcommand, ValueEnum};

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
        /// Persist pending re-anchor path updates into note frontmatter (R13
        /// phase 2) — the only write the system makes to a note file.
        #[arg(long = "write-anchors")]
        write_anchors: bool,
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
    /// Add, list, or show a symbol's notes with derived freshness (R12).
    Notes(NotesArgs),
}

/// `ctx notes …` arguments: a subcommand (`add`/`list`), or the bare
/// `ctx notes <symbol>` show form. The subcommand and the bare `<symbol>` are
/// mutually exclusive.
#[derive(Args)]
#[command(args_conflicts_with_subcommands = true)]
pub struct NotesArgs {
    #[command(subcommand)]
    pub action: Option<NotesAction>,
    /// Bare form `ctx notes <symbol>`: show that symbol's notes (C3 suffix).
    pub symbol: Option<String>,
    /// Emit JSON instead of plain text.
    #[arg(long)]
    pub json: bool,
    /// Skip the R3 staleness sweep and read the current snapshot.
    #[arg(long = "no-sync")]
    pub no_sync: bool,
}

#[derive(Subcommand)]
pub enum NotesAction {
    /// Anchor a note to a symbol (R12). Body from the positional text,
    /// `--file <path>`, or stdin via `--file -`.
    Add {
        /// Symbol name or qualified-path suffix (C3).
        symbol: String,
        /// Note body; omit to read from `--file <path>` or stdin (`--file -`).
        text: Option<String>,
        /// Note kind.
        #[arg(long, value_enum)]
        kind: Option<NoteKind>,
        /// Read the body from a file, or from stdin when the path is `-`.
        #[arg(long)]
        file: Option<String>,
        /// Emit JSON instead of plain text.
        #[arg(long)]
        json: bool,
        /// Skip the R3 staleness sweep and read the current snapshot.
        #[arg(long = "no-sync")]
        no_sync: bool,
    },
    /// List notes, filtered by kind, staleness, or the anchoring file (R12).
    List {
        /// Show only notes of this kind.
        #[arg(long, value_enum)]
        kind: Option<NoteKind>,
        /// Show only stale notes.
        #[arg(long)]
        stale: bool,
        /// Show only notes anchored to symbols in this file.
        #[arg(long)]
        file: Option<String>,
        /// Emit JSON instead of plain text.
        #[arg(long)]
        json: bool,
        /// Skip the R3 staleness sweep and read the current snapshot.
        #[arg(long = "no-sync")]
        no_sync: bool,
    },
}

/// The closed set of note kinds (R12).
#[derive(Clone, Copy, ValueEnum)]
pub enum NoteKind {
    Gotcha,
    Invariant,
    Rationale,
    Todo,
}

impl NoteKind {
    pub fn as_str(self) -> &'static str {
        match self {
            NoteKind::Gotcha => "gotcha",
            NoteKind::Invariant => "invariant",
            NoteKind::Rationale => "rationale",
            NoteKind::Todo => "todo",
        }
    }
}
