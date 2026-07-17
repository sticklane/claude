//! `context-tree` core library. The `ctx` binary is a thin shell over
//! [`run`]; query/note logic added by later tasks lives behind the same core
//! so the MCP wrapper (R15) never reimplements it.

pub mod cli;
pub mod cmd;
pub mod extract;
pub mod facts;
pub mod hash;
pub mod index;
pub mod lang;
pub mod path;
pub mod project;
pub mod sync;
pub mod vcs;

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
        Some(cli::Command::Sync { stats }) => {
            let cwd = match std::env::current_dir() {
                Ok(d) => d,
                Err(e) => {
                    eprintln!("ctx: cannot read current directory: {e}");
                    return ExitCode::FAILURE;
                }
            };
            let root = project::find_root(&cwd).unwrap_or(cwd);
            match sync::run_sync(&root, sync::journal::Trigger::Cli) {
                Ok(s) => {
                    if stats {
                        println!(
                            "scanned={} hashed={} parsed={}",
                            s.scanned, s.hashed, s.parsed
                        );
                    } else {
                        println!(
                            "sync: {} scanned, {} hashed, {} parsed",
                            s.scanned, s.hashed, s.parsed
                        );
                    }
                    ExitCode::SUCCESS
                }
                Err(e) => {
                    eprintln!("ctx sync failed: {e}");
                    ExitCode::FAILURE
                }
            }
        }
        Some(cli::Command::Tree {
            path,
            depth,
            limit,
            doc,
            json,
            no_sync,
        }) => cmd::tree::run(cmd::tree::Args {
            path,
            depth,
            limit,
            doc,
            json,
            no_sync,
        }),
        Some(cli::Command::Sig {
            symbol,
            doc,
            json,
            no_sync,
        }) => cmd::sig::run(cmd::sig::Args {
            symbol,
            doc,
            json,
            no_sync,
        }),
        Some(cli::Command::Deps {
            path,
            reverse,
            json,
            no_sync,
        }) => cmd::deps::run(cmd::deps::Args {
            path,
            reverse,
            json,
            no_sync,
        }),
        Some(cli::Command::Refs {
            symbol,
            limit,
            json,
            no_sync,
        }) => cmd::refs::run(cmd::refs::Args {
            symbol,
            limit,
            json,
            no_sync,
        }),
        Some(cli::Command::At {
            position,
            json,
            no_sync,
        }) => cmd::at::run(cmd::at::Args {
            position,
            json,
            no_sync,
        }),
        Some(cli::Command::Map {
            tokens,
            doc,
            json,
            no_sync,
        }) => cmd::map::run(cmd::map::Args {
            tokens,
            doc,
            json,
            no_sync,
        }),
        None => {
            println!("ctx — run `ctx --help` for usage");
            ExitCode::SUCCESS
        }
    }
}
