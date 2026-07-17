//! Per-file symbol facts (R1) and the cross-cutting fact types the extractor
//! produces: [`Symbol`] definitions, [`Reference`] occurrences (R1/R10),
//! [`Import`] edges (R9), and [`Scope`] locals-query bindings (R10).

use std::fmt;

/// A 0-based source position (tree-sitter point convention: row, column).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Point {
    pub row: usize,
    pub column: usize,
}

impl fmt::Display for Point {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        // Render as 1-based line:col for human-facing output.
        write!(f, "{}:{}", self.row + 1, self.column + 1)
    }
}

/// A source span: start/end points plus the underlying byte range.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Span {
    pub start: Point,
    pub end: Point,
    pub start_byte: usize,
    pub end_byte: usize,
}

/// A named occurrence's location (the file is tracked alongside the fact set).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Location {
    pub point: Point,
    pub byte: usize,
}

/// Small closed taxonomy of definition kinds (R1). Universal across languages;
/// each extractor maps its grammar's constructs onto this set.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SymbolKind {
    Module,
    Class,
    Function,
    Method,
    Struct,
    Enum,
    Interface,
    Trait,
    Constant,
    Variable,
    TypeAlias,
}

impl SymbolKind {
    pub fn as_str(self) -> &'static str {
        match self {
            SymbolKind::Module => "module",
            SymbolKind::Class => "class",
            SymbolKind::Function => "function",
            SymbolKind::Method => "method",
            SymbolKind::Struct => "struct",
            SymbolKind::Enum => "enum",
            SymbolKind::Interface => "interface",
            SymbolKind::Trait => "trait",
            SymbolKind::Constant => "constant",
            SymbolKind::Variable => "variable",
            SymbolKind::TypeAlias => "type_alias",
        }
    }
}

/// A definition fact (R1): the full symbol record keyed by its C1 qualified
/// path and C2 body hash.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Symbol {
    pub kind: SymbolKind,
    pub name: String,
    /// C1 qualified path.
    pub qpath: String,
    /// Syntactic signature text (declaration head).
    pub signature: String,
    /// C8 docstring; empty string when the symbol has none.
    pub docstring: String,
    pub full_span: Span,
    pub ident_span: Span,
    /// Enclosing symbol's qualified path (containment), if any.
    pub parent: Option<String>,
    /// C2 body content hash (hex SHA-256 over the identifier-excised full span).
    pub body_hash: String,
    /// Identifier-excised body token set (C2's byte basis, tokenized) — the
    /// R13 tree-diff score input, persisted even though nothing consumes it yet.
    pub body_tokens: Vec<String>,
}

/// The kind of a reference occurrence (R1/R10) — the use, not the definition.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RefKind {
    Call,
    Read,
    Write,
}

impl RefKind {
    pub fn as_str(self) -> &'static str {
        match self {
            RefKind::Call => "call",
            RefKind::Read => "read",
            RefKind::Write => "write",
        }
    }
}

/// A reference occurrence: a name used at a location, with its use kind.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Reference {
    pub name: String,
    pub location: Location,
    pub kind: RefKind,
}

/// A module-level import edge (R9's raw material).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Import {
    /// The importing file's module/path component.
    pub source: String,
    /// The module imported from (e.g. `os`, `a.b`).
    pub module: String,
    /// The specific imported symbol for `from ... import name`; `None` for a
    /// bare `import module`.
    pub name: Option<String>,
    pub location: Location,
}

/// A locals-query scope binding (R10): a name bound locally within a lexical
/// scope span. A reference inside `scope` to `name` is a local, distinct from a
/// same-named global — the raw material scope-aware `ctx refs` consumes.
/// Populated only for grammars shipping (or given) a locals query.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Scope {
    pub name: String,
    pub def_location: Location,
    /// The enclosing `@local.scope` span containing the local definition.
    pub scope: Span,
}

impl Scope {
    /// True when `point` falls within this scope's span (half-open on the end
    /// byte is unnecessary — spans come from whole nodes).
    pub fn contains_byte(&self, byte: usize) -> bool {
        byte >= self.scope.start_byte && byte < self.scope.end_byte
    }
}
