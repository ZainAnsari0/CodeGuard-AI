/**
 * CodeGuard AI - Sanitizer Recognition
 * Identifies known sanitizer functions and their effectiveness at removing taint.
 */

const SANITIZERS = {
  // ─── XSS Sanitizers ───────────────────────────────────────────────
  "escapeHtml":           { removes: ["xss"],              strength: "strong" },
  "escape":               { removes: ["xss"],              strength: "strong" },
  "encodeURI":            { removes: ["xss"],              strength: "partial" },
  "encodeURIComponent":   { removes: ["xss"],              strength: "strong" },
  "DOMPurify.sanitize":   { removes: ["xss"],              strength: "strong" },
  "sanitizeHtml":         { removes: ["xss"],              strength: "strong" },
  "xss":                  { removes: ["xss"],              strength: "strong" },  // xss library
  "validator.escape":     { removes: ["xss"],              strength: "strong" },
  "he.encode":            { removes: ["xss"],              strength: "strong" },
  "sanitize":             { removes: ["xss"],              strength: "partial" },

  // ─── SQL Sanitizers (WEAK — escaping is not a reliable defense) ───
  "mysql.escape":          { removes: ["sql_injection"],   strength: "weak" },
  "mysql.escapeId":        { removes: ["sql_injection"],   strength: "weak" },
  "connection.escape":     { removes: ["sql_injection"],   strength: "weak" },
  "pg.escapeLiteral":      { removes: ["sql_injection"],   strength: "weak" },
  "escapeString":          { removes: ["sql_injection"],   strength: "weak" },

  // ─── Path Sanitizers ───────────────────────────────────────────────
  "path.resolve":          { removes: ["path_traversal"],  strength: "partial" },
  "path.normalize":        { removes: ["path_traversal"],  strength: "partial" },
  "path.basename":         { removes: ["path_traversal"],  strength: "strong" },

  // ─── Command Sanitizers (effectively none exist) ─────────────────
  "shellEscape":           { removes: ["command_injection"], strength: "weak" },
  "escapeshellarg":        { removes: ["command_injection"], strength: "weak" },

  // ─── General-purpose type coercion (removes injection risk) ──────
  "parseInt":               { removes: ["xss", "sql_injection", "command_injection"], strength: "strong" },
  "Number":                 { removes: ["xss", "sql_injection", "command_injection"], strength: "strong" },
  "Boolean":                { removes: ["xss", "sql_injection", "command_injection"], strength: "strong" },
  "JSON.stringify":         { removes: ["xss"],             strength: "partial" },
  "JSON.parse":             { removes: [],                  strength: "none" }, // parsing doesn't sanitize
};

module.exports = { SANITIZERS };