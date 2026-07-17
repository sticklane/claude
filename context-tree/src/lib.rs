//! `context-tree` core library. The `ctx` binary is a thin shell over
//! [`run`]; query/note logic added by later tasks lives behind the same core
//! so the MCP wrapper (R15) never reimplements it.

pub mod cli;
pub mod extract;
pub mod facts;
pub mod hash;
pub mod lang;
pub mod path;
pub mod project;

use clap::Parser;
use std::process::ExitCode;

/// Parse argv and dispatch. Returns the process exit code.
pub fn run() -> ExitCode {
    let cli = cli::Cli::parse();
    match cli.command {
        Some(cli::Command::Init) => {
            let cwd = match std::env::current_dir() {
                Ok(d) => d,
                Err(e) => {
                    eprintln!("ctx: cannot read current directory: {e}");
                    return ExitCode::FAILURE;
                }
            };
            match project::init(&cwd) {
                Ok(root) => {
                    println!("initialized .context/ at {}", root.display());
                    ExitCode::SUCCESS
                }
                Err(e) => {
                    eprintln!("ctx init failed: {e}");
                    ExitCode::FAILURE
                }
            }
        }
        None => {
            println!("ctx — run `ctx --help` for usage");
            ExitCode::SUCCESS
        }
    }
}
