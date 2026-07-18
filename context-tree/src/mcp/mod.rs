//! `ctx mcp` (R15): a stdio MCP server exposing the query verbs (tree, sig,
//! map, deps, refs, at) and note verbs (notes add/show/list) as typed tools.
//!
//! Every tool is a thin wrapper: it builds the same `cmd::*::Args` the CLI
//! builds and calls the matching `cmd::*::render`, so the query and note logic
//! is never reimplemented. `render` returns the exact stdout the CLI prints as a
//! `String`, which becomes the tool's text result — the printing `cmd::*::run`
//! is never called here, since its stdout would corrupt the JSON-RPC channel.

use crate::cmd;
use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::{ServerCapabilities, ServerInfo};
use rmcp::transport::stdio;
use rmcp::{ServerHandler, ServiceExt, schemars, tool, tool_handler, tool_router};
use std::process::ExitCode;

#[derive(Debug, serde::Deserialize, schemars::JsonSchema)]
struct TreeParams {
    /// Path (file or directory prefix) to outline; defaults to ".".
    path: Option<String>,
    /// Cap the containment depth shown (top-level is depth 1).
    depth: Option<usize>,
    /// Cap the number of symbols shown before a truncation line (default 200).
    limit: Option<usize>,
    /// Append each symbol's first docstring line.
    doc: Option<bool>,
}

#[derive(Debug, serde::Deserialize, schemars::JsonSchema)]
struct SigParams {
    /// Symbol name or qualified-path suffix (C3).
    symbol: String,
    /// Print the full docstring rather than only its first line.
    doc: Option<bool>,
}

#[derive(Debug, serde::Deserialize, schemars::JsonSchema)]
struct MapParams {
    /// Token budget for the output (C7); defaults to 1000.
    tokens: Option<usize>,
    /// Append each symbol's first docstring line, counted within the budget.
    doc: Option<bool>,
}

#[derive(Debug, serde::Deserialize, schemars::JsonSchema)]
struct DepsParams {
    /// Path whose import edges to show; defaults to ".".
    path: Option<String>,
    /// Show edges INTO the path (importers) rather than OUT of it.
    reverse: Option<bool>,
}

#[derive(Debug, serde::Deserialize, schemars::JsonSchema)]
struct RefsParams {
    /// Symbol name or qualified-path suffix (C3).
    symbol: String,
    /// Cap on results shown per direction (default 50).
    limit: Option<usize>,
}

#[derive(Debug, serde::Deserialize, schemars::JsonSchema)]
struct AtParams {
    /// Position as `<file>:<line>` (1-based line).
    position: String,
}

#[derive(Debug, serde::Deserialize, schemars::JsonSchema)]
struct NotesAddParams {
    /// Symbol name or qualified-path suffix to anchor the note to (C3).
    symbol: String,
    /// Note body text.
    text: Option<String>,
    /// Note kind (e.g. gotcha, invariant, rationale, todo).
    kind: Option<String>,
    /// Read the body from a file path instead of `text`.
    file: Option<String>,
}

#[derive(Debug, serde::Deserialize, schemars::JsonSchema)]
struct NotesShowParams {
    /// Symbol name or qualified-path suffix whose notes to show (C3).
    symbol: String,
}

#[derive(Debug, serde::Deserialize, schemars::JsonSchema)]
struct NotesListParams {
    /// Show only notes of this kind.
    kind: Option<String>,
    /// Show only stale notes.
    stale: Option<bool>,
    /// Show only notes anchored to symbols in this file.
    file: Option<String>,
}

/// The MCP server. `#[tool_router]` generates the `Self::tool_router()` the
/// `#[tool_handler]` impl dispatches through; every tool delegates to a
/// `cmd::*::render` core.
#[derive(Clone, Default)]
pub struct CtxServer;

#[tool_router]
impl CtxServer {
    #[tool(description = "Containment outline (JSON) for a path subtree.")]
    fn tree(&self, Parameters(p): Parameters<TreeParams>) -> String {
        cmd::tree::render(&cmd::tree::Args {
            path: p.path.unwrap_or_else(|| ".".to_string()),
            depth: p.depth,
            limit: p.limit.unwrap_or(200),
            doc: p.doc.unwrap_or(false),
            json: true,
            no_sync: false,
        })
        .0
    }

    #[tool(description = "Signature and docstring (JSON) for a symbol (C3 suffix).")]
    fn sig(&self, Parameters(p): Parameters<SigParams>) -> String {
        cmd::sig::render(&cmd::sig::Args {
            symbol: p.symbol,
            doc: p.doc.unwrap_or(false),
            json: true,
            no_sync: false,
        })
        .0
    }

    #[tool(description = "Ranked project overview (JSON) by reference-graph importance.")]
    fn map(&self, Parameters(p): Parameters<MapParams>) -> String {
        cmd::map::render(&cmd::map::Args {
            tokens: p.tokens.unwrap_or(1000),
            doc: p.doc.unwrap_or(false),
            json: true,
            no_sync: false,
        })
        .0
    }

    #[tool(description = "Module-level import edges (JSON) into or out of a path.")]
    fn deps(&self, Parameters(p): Parameters<DepsParams>) -> String {
        cmd::deps::render(&cmd::deps::Args {
            path: p.path.unwrap_or_else(|| ".".to_string()),
            reverse: p.reverse.unwrap_or(false),
            json: true,
            no_sync: false,
        })
        .0
    }

    #[tool(description = "Definitions and references (JSON) for a symbol (C3 suffix).")]
    fn refs(&self, Parameters(p): Parameters<RefsParams>) -> String {
        cmd::refs::render(&cmd::refs::Args {
            symbol: p.symbol,
            limit: p.limit.unwrap_or(50),
            json: true,
            no_sync: false,
        })
        .0
    }

    #[tool(description = "Innermost enclosing symbol + containment chain (JSON) for a file:line.")]
    fn at(&self, Parameters(p): Parameters<AtParams>) -> String {
        cmd::at::render(&cmd::at::Args {
            position: p.position,
            json: true,
            no_sync: false,
        })
        .0
    }

    #[tool(
        name = "notes_add",
        description = "Anchor a note to a symbol (C3 suffix)."
    )]
    fn notes_add(&self, Parameters(p): Parameters<NotesAddParams>) -> String {
        cmd::notes::render(&cmd::notes::Args {
            action: cmd::notes::Action::Add {
                symbol: p.symbol,
                text: p.text,
                kind: p.kind,
                file: p.file,
            },
            json: true,
            no_sync: false,
        })
        .0
    }

    #[tool(
        name = "notes",
        description = "Show a symbol's notes with derived freshness (JSON)."
    )]
    fn notes(&self, Parameters(p): Parameters<NotesShowParams>) -> String {
        cmd::notes::render(&cmd::notes::Args {
            action: cmd::notes::Action::Show { symbol: p.symbol },
            json: true,
            no_sync: false,
        })
        .0
    }

    #[tool(
        name = "notes_list",
        description = "List notes filtered by kind, staleness, or file (JSON)."
    )]
    fn notes_list(&self, Parameters(p): Parameters<NotesListParams>) -> String {
        cmd::notes::render(&cmd::notes::Args {
            action: cmd::notes::Action::List {
                kind: p.kind,
                stale: p.stale.unwrap_or(false),
                file: p.file,
            },
            json: true,
            no_sync: false,
        })
        .0
    }
}

#[tool_handler]
impl ServerHandler for CtxServer {
    fn get_info(&self) -> ServerInfo {
        let mut info = ServerInfo::default();
        info.instructions = Some(
            "context-tree query (tree, sig, map, deps, refs, at) and note \
             (notes_add, notes, notes_list) tools."
                .to_string(),
        );
        info.capabilities = ServerCapabilities::builder().enable_tools().build();
        info
    }
}

/// Start the stdio MCP server, blocking until the client disconnects.
pub fn serve() -> ExitCode {
    let runtime = match tokio::runtime::Runtime::new() {
        Ok(r) => r,
        Err(e) => {
            eprintln!("ctx mcp: cannot start async runtime: {e}");
            return ExitCode::FAILURE;
        }
    };
    let result: Result<(), Box<dyn std::error::Error>> = runtime.block_on(async {
        let service = CtxServer.serve(stdio()).await?;
        service.waiting().await?;
        Ok(())
    });
    match result {
        Ok(()) => ExitCode::SUCCESS,
        Err(e) => {
            eprintln!("ctx mcp: {e}");
            ExitCode::FAILURE
        }
    }
}
