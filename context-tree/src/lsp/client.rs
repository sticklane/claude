//! A minimal LSP client (JSON-RPC over stdio) sufficient to ask "what are the
//! references to this symbol", and [`RustAnalyzerResolver`] — a
//! [`ReferenceResolver`](super::ReferenceResolver) backed by a live
//! `rust-analyzer`.
//!
//! It is deliberately minimal: enough of the protocol (`initialize`,
//! `initialized`, `textDocument/didOpen`, `textDocument/references`, `shutdown`,
//! `exit`) to confirm precise references for one file, and no more. The server
//! binary defaults to `rust-analyzer` and is overridable via the `CTX_LSP_SERVER`
//! environment variable. Any protocol or process error surfaces as an
//! `io::Error`, which the enrichment pass swallows per target so a missing or
//! flaky server never regresses syntactic results.

use super::{PreciseRef, ReferenceResolver, ResolveTarget, Resolved};
use serde_json::{Value, json};
use std::io::{self, BufReader, Read, Write};
use std::path::Path;
use std::process::{Child, Command, Stdio};
use std::time::{Duration, Instant};

/// A [`ReferenceResolver`] that shells out to a live `rust-analyzer` (or the
/// server named by `CTX_LSP_SERVER`). Spawns a fresh server per target, runs the
/// handshake, opens the target file, and returns the references the server
/// confirms. When the binary is absent this errors, and enrichment leaves that
/// target heuristic.
pub struct RustAnalyzerResolver;

impl RustAnalyzerResolver {
    /// The configured server binary name (`CTX_LSP_SERVER`, default
    /// `rust-analyzer`).
    pub fn server_binary() -> String {
        std::env::var("CTX_LSP_SERVER").unwrap_or_else(|_| "rust-analyzer".to_string())
    }

    /// Whether a configured language server is available on `PATH`. Used to gate
    /// the live path (and its test) — absent server => enrichment is a no-op.
    pub fn available() -> bool {
        let bin = Self::server_binary();
        Command::new(&bin)
            .arg("--version")
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status()
            .map(|s| s.success())
            .unwrap_or(false)
    }
}

impl ReferenceResolver for RustAnalyzerResolver {
    fn resolve(&self, root: &Path, target: &ResolveTarget) -> io::Result<Resolved> {
        let mut client = LspClient::spawn(root)?;
        client.initialize(root)?;
        let file_abs = root.join(&target.file);
        let text = std::fs::read_to_string(&file_abs)?;
        client.did_open(&file_abs, &text)?;
        let locations = client.references(&file_abs, target.line0, target.col0)?;
        let _ = client.shutdown();

        let mut refs = Vec::new();
        for loc in locations {
            if let Some(pr) = location_to_ref(root, &target.name, &loc) {
                refs.push(pr);
            }
        }
        Ok(Resolved {
            refs,
            signature: None,
        })
    }
}

/// Map an LSP `Location` to a repo-relative [`PreciseRef`] (1-based line). Drops
/// locations outside `root` (e.g. references in `std`).
fn location_to_ref(root: &Path, name: &str, loc: &Value) -> Option<PreciseRef> {
    let uri = loc.get("uri")?.as_str()?;
    let path = uri.strip_prefix("file://")?;
    let rel = Path::new(path).strip_prefix(root).ok()?;
    let line0 = loc.get("range")?.get("start")?.get("line")?.as_u64()?;
    Some(PreciseRef {
        name: name.to_string(),
        path: rel.to_string_lossy().replace('\\', "/"),
        line: line0 as usize + 1,
    })
}

/// A live JSON-RPC-over-stdio LSP session.
struct LspClient {
    child: Child,
    reader: BufReader<std::process::ChildStdout>,
    next_id: i64,
}

impl LspClient {
    fn spawn(root: &Path) -> io::Result<LspClient> {
        let mut child = Command::new(RustAnalyzerResolver::server_binary())
            .current_dir(root)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .spawn()?;
        let stdout = child
            .stdout
            .take()
            .ok_or_else(|| io::Error::new(io::ErrorKind::Other, "no server stdout"))?;
        Ok(LspClient {
            child,
            reader: BufReader::new(stdout),
            next_id: 1,
        })
    }

    fn write_message(&mut self, msg: &Value) -> io::Result<()> {
        let body = serde_json::to_vec(msg)?;
        let stdin = self
            .child
            .stdin
            .as_mut()
            .ok_or_else(|| io::Error::new(io::ErrorKind::Other, "no server stdin"))?;
        write!(stdin, "Content-Length: {}\r\n\r\n", body.len())?;
        stdin.write_all(&body)?;
        stdin.flush()
    }

    /// Read one framed message.
    fn read_message(&mut self) -> io::Result<Value> {
        let mut content_length: Option<usize> = None;
        let mut header = Vec::new();
        loop {
            let mut byte = [0u8; 1];
            self.reader.read_exact(&mut byte)?;
            header.push(byte[0]);
            if header.ends_with(b"\r\n\r\n") {
                break;
            }
        }
        for line in String::from_utf8_lossy(&header).split("\r\n") {
            if let Some(v) = line.strip_prefix("Content-Length:") {
                content_length = v.trim().parse().ok();
            }
        }
        let len = content_length
            .ok_or_else(|| io::Error::new(io::ErrorKind::Other, "no Content-Length"))?;
        let mut body = vec![0u8; len];
        self.reader.read_exact(&mut body)?;
        serde_json::from_slice(&body)
            .map_err(|e| io::Error::new(io::ErrorKind::InvalidData, e.to_string()))
    }

    /// Send a request and return the matching response `result`, draining
    /// notifications and server-to-client requests in between.
    fn request(&mut self, method: &str, params: Value) -> io::Result<Value> {
        let id = self.next_id;
        self.next_id += 1;
        self.write_message(&json!({
            "jsonrpc": "2.0", "id": id, "method": method, "params": params,
        }))?;
        loop {
            let msg = self.read_message()?;
            if msg.get("id").and_then(Value::as_i64) == Some(id) && msg.get("method").is_none() {
                if let Some(err) = msg.get("error") {
                    return Err(io::Error::new(
                        io::ErrorKind::Other,
                        format!("lsp error: {err}"),
                    ));
                }
                return Ok(msg.get("result").cloned().unwrap_or(Value::Null));
            }
            // Server-to-client request (e.g. workspace/configuration): reply
            // with null so the server does not block waiting on us.
            if msg.get("method").is_some() {
                if let Some(req_id) = msg.get("id") {
                    self.write_message(&json!({
                        "jsonrpc": "2.0", "id": req_id, "result": Value::Null,
                    }))?;
                }
            }
        }
    }

    fn notify(&mut self, method: &str, params: Value) -> io::Result<()> {
        self.write_message(&json!({
            "jsonrpc": "2.0", "method": method, "params": params,
        }))
    }

    fn initialize(&mut self, root: &Path) -> io::Result<()> {
        let root_uri = format!("file://{}", root.display());
        self.request(
            "initialize",
            json!({
                "processId": std::process::id(),
                "rootUri": root_uri,
                "capabilities": {},
            }),
        )?;
        self.notify("initialized", json!({}))
    }

    fn did_open(&mut self, file: &Path, text: &str) -> io::Result<()> {
        self.notify(
            "textDocument/didOpen",
            json!({
                "textDocument": {
                    "uri": format!("file://{}", file.display()),
                    "languageId": "rust",
                    "version": 1,
                    "text": text,
                },
            }),
        )
    }

    /// Ask for references at `(line0, col0)`, retrying until the server returns
    /// a non-empty set or a ~30s budget elapses (rust-analyzer resolves nothing
    /// until its initial workspace load finishes).
    fn references(&mut self, file: &Path, line0: usize, col0: usize) -> io::Result<Vec<Value>> {
        let deadline = Instant::now() + Duration::from_secs(30);
        loop {
            let result = self.request(
                "textDocument/references",
                json!({
                    "textDocument": { "uri": format!("file://{}", file.display()) },
                    "position": { "line": line0, "character": col0 },
                    "context": { "includeDeclaration": false },
                }),
            )?;
            if let Some(arr) = result.as_array() {
                if !arr.is_empty() {
                    return Ok(arr.clone());
                }
            }
            if Instant::now() >= deadline {
                return Ok(Vec::new());
            }
            std::thread::sleep(Duration::from_millis(300));
        }
    }

    fn shutdown(&mut self) -> io::Result<()> {
        let _ = self.request("shutdown", Value::Null);
        let _ = self.notify("exit", Value::Null);
        let _ = self.child.wait();
        Ok(())
    }
}

impl Drop for LspClient {
    fn drop(&mut self) {
        let _ = self.child.kill();
        let _ = self.child.wait();
    }
}
