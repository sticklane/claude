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
}
