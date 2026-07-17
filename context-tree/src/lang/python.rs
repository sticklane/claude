//! Python extractor: definitions (function/method/class), C1 dotted-module
//! paths, C8 docstrings, references, module-level import edges, and
//! locals-query scope facts.
//!
//! tree-sitter-python ships no locals query, so [`LOCALS_QUERY`] is authored
//! here (function/lambda scopes; assignment/parameter/for-target bindings) to
//! satisfy R10's scope-aware requirement.

use crate::extract::{ExtractResult, ExtractorRegistration, LanguageExtractor};
use crate::facts::{Import, Location, Point, RefKind, Reference, Scope, Span, Symbol, SymbolKind};
use crate::hash;
use crate::path;
use tree_sitter::{Node, Parser, Query, QueryCursor, StreamingIterator};

/// Locals query (see module docs). Function and lambda bodies are lexical
/// scopes; a binding whose innermost enclosing scope is one of these is a
/// function-local, distinct from a same-named global.
const LOCALS_QUERY: &str = r#"
(function_definition) @local.scope
(lambda) @local.scope
(assignment left: (identifier) @local.definition)
(parameters (identifier) @local.definition)
(for_statement left: (identifier) @local.definition)
"#;

pub struct PythonExtractor {
    language: tree_sitter::Language,
}

impl PythonExtractor {
    pub fn new() -> Self {
        Self {
            language: tree_sitter_python::LANGUAGE.into(),
        }
    }
}

impl Default for PythonExtractor {
    fn default() -> Self {
        Self::new()
    }
}

inventory::submit! {
    ExtractorRegistration {
        language: "python",
        extensions: &["py"],
        make: || Box::new(PythonExtractor::new()),
    }
}

fn point_of(node: Node) -> Point {
    let p = node.start_position();
    Point {
        row: p.row,
        column: p.column,
    }
}

fn span_of(node: Node) -> Span {
    let s = node.start_position();
    let e = node.end_position();
    Span {
        start: Point {
            row: s.row,
            column: s.column,
        },
        end: Point {
            row: e.row,
            column: e.column,
        },
        start_byte: node.start_byte(),
        end_byte: node.end_byte(),
    }
}

fn location_of(node: Node) -> Location {
    Location {
        point: point_of(node),
        byte: node.start_byte(),
    }
}

fn text<'a>(node: Node, source: &'a [u8]) -> &'a str {
    node.utf8_text(source).unwrap_or("")
}

/// Visit every node (named and anonymous) depth-first.
fn each_node(node: Node, f: &mut impl FnMut(Node)) {
    f(node);
    let mut cursor = node.walk();
    for child in node.children(&mut cursor) {
        each_node(child, f);
    }
}

/// C8 docstring: the content of a string literal that is the first statement of
/// `body`, or empty when there is none.
fn docstring(body: Node, source: &[u8]) -> String {
    let mut cursor = body.walk();
    let Some(first) = body.named_children(&mut cursor).next() else {
        return String::new();
    };
    if first.kind() != "expression_statement" {
        return String::new();
    }
    let Some(inner) = first.named_child(0) else {
        return String::new();
    };
    if inner.kind() != "string" {
        return String::new();
    }
    let mut c2 = inner.walk();
    for part in inner.named_children(&mut c2) {
        if part.kind() == "string_content" {
            return text(part, source).to_string();
        }
    }
    String::new()
}

/// Recursively collect definition symbols, tracking the enclosing container
/// chain for C1 paths and method-vs-function classification.
fn collect_defs(
    node: Node,
    module: &str,
    containers: &mut Vec<String>,
    parent_is_class: bool,
    source: &[u8],
    out: &mut Vec<Symbol>,
) {
    let mut cursor = node.walk();
    for child in node.children(&mut cursor) {
        let kind = match child.kind() {
            "class_definition" => Some(SymbolKind::Class),
            "function_definition" => Some(if parent_is_class {
                SymbolKind::Method
            } else {
                SymbolKind::Function
            }),
            _ => None,
        };
        let Some(sym_kind) = kind else {
            collect_defs(child, module, containers, parent_is_class, source, out);
            continue;
        };
        let Some(name_node) = child.child_by_field_name("name") else {
            // Unnamed/broken def — descend for recoverable nested defs.
            collect_defs(child, module, containers, parent_is_class, source, out);
            continue;
        };
        let name = text(name_node, source).to_string();
        let qpath = path::build_qpath(module, containers, &name);
        let body = child.child_by_field_name("body");
        let signature = match body {
            Some(b) => String::from_utf8_lossy(&source[child.start_byte()..b.start_byte()])
                .trim()
                .to_string(),
            None => text(child, source).trim().to_string(),
        };
        let doc = body.map(|b| docstring(b, source)).unwrap_or_default();
        let full = (child.start_byte(), child.end_byte());
        let ident = (name_node.start_byte(), name_node.end_byte());
        let parent = if containers.is_empty() {
            None
        } else {
            Some(path::build_qpath(module, containers, ""))
        };
        out.push(Symbol {
            kind: sym_kind,
            name: name.clone(),
            qpath,
            signature,
            docstring: doc,
            full_span: span_of(child),
            ident_span: span_of(name_node),
            parent,
            body_hash: hash::body_hash(source, full, ident),
            body_tokens: hash::body_tokens(source, full, ident),
        });

        containers.push(name);
        collect_defs(
            child,
            module,
            containers,
            matches!(sym_kind, SymbolKind::Class),
            source,
            out,
        );
        containers.pop();
    }
}

/// The terminal callee name + location for a `call` node's function field.
fn callee(func: Node, source: &[u8]) -> Option<(String, Location)> {
    match func.kind() {
        "identifier" => Some((text(func, source).to_string(), location_of(func))),
        "attribute" => {
            let attr = func.child_by_field_name("attribute")?;
            Some((text(attr, source).to_string(), location_of(attr)))
        }
        _ => None,
    }
}

/// Classify an `identifier` occurrence as a read/write reference, or `None`
/// when it is a binding/definition/import/keyword position (not a reference).
fn classify_identifier(node: Node) -> Option<RefKind> {
    let parent = node.parent()?;
    let pk = parent.kind();
    let is_field = |field: &str| parent.child_by_field_name(field) == Some(node);
    match pk {
        "function_definition" | "class_definition" if is_field("name") => None,
        "parameters"
        | "typed_parameter"
        | "default_parameter"
        | "typed_default_parameter"
        | "list_splat_pattern"
        | "dictionary_splat_pattern" => None,
        "keyword_argument" if is_field("name") => None,
        "dotted_name"
        | "aliased_import"
        | "import_statement"
        | "import_from_statement"
        | "relative_import" => None,
        "attribute" if is_field("attribute") => None,
        "call" if is_field("function") => None,
        "assignment" if is_field("left") => Some(RefKind::Write),
        _ => Some(RefKind::Read),
    }
}

impl LanguageExtractor for PythonExtractor {
    fn language(&self) -> &'static str {
        "python"
    }

    fn extensions(&self) -> &'static [&'static str] {
        &["py"]
    }

    fn extract(&self, rel_path: &str, source: &[u8]) -> ExtractResult {
        let module = path::python_module(rel_path);
        let mut parser = Parser::new();
        if parser.set_language(&self.language).is_err() {
            return ExtractResult {
                parse_failed: true,
                ..Default::default()
            };
        }
        let Some(tree) = parser.parse(source, None) else {
            return ExtractResult {
                parse_failed: true,
                ..Default::default()
            };
        };
        let root = tree.root_node();
        let parse_failed = root.has_error();

        // Definitions.
        let mut symbols = Vec::new();
        let mut containers = Vec::new();
        collect_defs(root, &module, &mut containers, false, source, &mut symbols);
        let qpaths: Vec<String> = symbols.iter().map(|s| s.qpath.clone()).collect();
        let disambiguated = path::disambiguate(&qpaths);
        for (sym, q) in symbols.iter_mut().zip(disambiguated) {
            sym.qpath = q;
        }

        // References and imports.
        let mut references = Vec::new();
        let mut imports = Vec::new();
        each_node(root, &mut |n| match n.kind() {
            "call" => {
                if let Some(func) = n.child_by_field_name("function")
                    && let Some((name, location)) = callee(func, source)
                {
                    references.push(Reference {
                        name,
                        location,
                        kind: RefKind::Call,
                    });
                }
            }
            "identifier" => {
                if let Some(kind) = classify_identifier(n) {
                    references.push(Reference {
                        name: text(n, source).to_string(),
                        location: location_of(n),
                        kind,
                    });
                }
            }
            "import_statement" => {
                let mut c = n.walk();
                for item in n.named_children(&mut c) {
                    let module_node = match item.kind() {
                        "dotted_name" => Some(item),
                        "aliased_import" => item.child_by_field_name("name"),
                        _ => None,
                    };
                    if let Some(mn) = module_node {
                        imports.push(Import {
                            source: module.clone(),
                            module: text(mn, source).to_string(),
                            name: None,
                            location: location_of(item),
                        });
                    }
                }
            }
            "import_from_statement" => {
                let module_name = n
                    .child_by_field_name("module_name")
                    .map(|m| text(m, source).to_string())
                    .unwrap_or_default();
                let mut c = n.walk();
                for item in n.named_children(&mut c) {
                    // Skip the module_name child itself; the rest are imports.
                    if Some(item) == n.child_by_field_name("module_name") {
                        continue;
                    }
                    let name = match item.kind() {
                        "dotted_name" | "identifier" => Some(text(item, source).to_string()),
                        "aliased_import" => item
                            .child_by_field_name("name")
                            .map(|nm| text(nm, source).to_string()),
                        "wildcard_import" => Some("*".to_string()),
                        _ => None,
                    };
                    if let Some(name) = name {
                        imports.push(Import {
                            source: module.clone(),
                            module: module_name.clone(),
                            name: Some(name),
                            location: location_of(item),
                        });
                    }
                }
            }
            _ => {}
        });

        // Locals-query scopes (R10).
        let scopes = extract_scopes(&self.language, root, source);

        ExtractResult {
            symbols,
            references,
            imports,
            scopes,
            parse_failed,
        }
    }
}

/// Run the locals query, then bind each `@local.definition` to its innermost
/// enclosing `@local.scope`, yielding [`Scope`] facts. A binding with no
/// enclosing function/lambda scope is a global — it produces no scope fact, so
/// scope facts always mark true function-locals.
fn extract_scopes(language: &tree_sitter::Language, root: Node, source: &[u8]) -> Vec<Scope> {
    let Ok(query) = Query::new(language, LOCALS_QUERY) else {
        return Vec::new();
    };
    let names = query.capture_names();
    let mut scope_spans: Vec<Span> = Vec::new();
    let mut defs: Vec<(String, Location, usize)> = Vec::new();
    let mut cursor = QueryCursor::new();
    let mut matches = cursor.matches(&query, root, source);
    while let Some(m) = matches.next() {
        for cap in m.captures {
            match names[cap.index as usize] {
                "local.scope" => scope_spans.push(span_of(cap.node)),
                "local.definition" => defs.push((
                    text(cap.node, source).to_string(),
                    location_of(cap.node),
                    cap.node.start_byte(),
                )),
                _ => {}
            }
        }
    }
    let mut out = Vec::new();
    for (name, def_location, byte) in defs {
        // Innermost enclosing scope = the containing span with the largest start.
        let innermost = scope_spans
            .iter()
            .filter(|s| byte >= s.start_byte && byte < s.end_byte)
            .max_by_key(|s| s.start_byte);
        if let Some(scope) = innermost {
            out.push(Scope {
                name,
                def_location,
                scope: *scope,
            });
        }
    }
    out
}
