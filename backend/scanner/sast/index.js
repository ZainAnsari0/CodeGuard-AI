#!/usr/bin/env node
/**
 * CodeGuard AI - SAST Engine Entry Point
 *
 * Orchestrates the full AST-based vulnerability detection pipeline:
 *   Parse → Build Scopes → Detect Sources → Propagate Taint → Detect Sinks → Aggregate → Report
 *
 * Usage:
 *   node sast/index.js <file_path>           # Scan a single file
 *   node sast/index.js --stdin < file.js     # Read from stdin
 *   echo 'const code = ...' | node sast/index.js --stdin --file-path=app.js
 *
 * Output: JSON to stdout with findings array compatible with CodeGuard scan pipeline.
 */

const fs = require("fs");
const path = require("path");

const { parseSource } = require("./parser");
const { buildScopes } = require("./scope");
const { SourceDetector } = require("./sources");
const { SinkDetector } = require("./sinks");
const { TaintStore, propagateTaint } = require("./taint");
const { VulnerabilityAggregator } = require("./aggregator");
const { generateReport } = require("./report");

/**
 * Run the full SAST pipeline on a single file.
 *
 * @param {string} filePath - Path of the file (used in findings)
 * @param {string} sourceContent - Source code text
 * @returns {object} Report with findings array
 */
function scanFileSAST(filePath, sourceContent) {
  // Stage 1: Parse
  const { ast, parseMode, error: parseError } = parseSource(sourceContent, filePath);
  if (!ast) {
    return {
      scanner: "codeguard-sast-js",
      version: "2.0",
      file_path: filePath,
      scan_timestamp: new Date().toISOString(),
      error: `Parse failed: ${parseError}`,
      findings: [],
      summary: { total_findings: 0, by_severity: { critical: 0, high: 0, medium: 0, low: 0, info: 0 } },
    };
  }

  // Stage 2: Build scopes
  const scopeTree = buildScopes(ast);

  // Stage 3: Create taint store and detect sources
  const taintStore = new TaintStore(scopeTree);
  const sourceDetector = new SourceDetector(scopeTree);
  sourceDetector.detectSources(ast, taintStore);

  // Stage 4: Propagate taint
  propagateTaint(ast, taintStore, scopeTree);

  // Stage 5: Detect sinks
  const sinkDetector = new SinkDetector(taintStore, scopeTree, sourceContent);
  const rawFindings = sinkDetector.detectSinks(ast);

  // Also run AST-based pattern checks (legacy patterns that the taint
  // engine may not catch — hardcoded secrets, eval without user input, etc.)
  const patternFindings = _runPatternChecks(ast, filePath, sourceContent);

  // Combine all findings
  const allFindings = [...rawFindings, ...patternFindings];

  // Stage 6: Deduplicate
  const aggregator = new VulnerabilityAggregator();
  const dedupedFindings = aggregator.aggregate(allFindings);

  // Stage 7: Generate report
  const report = generateReport(dedupedFindings, filePath);

  // Add metadata
  report.parse_mode = parseMode;
  report.taint_sources_detected = taintStore.variableTaints.size;
  report.scopes_analyzed = scopeTree.scopes.size;

  return report;
}

/**
 * AST-based pattern checks for vulnerabilities that don't require taint tracking.
 * These catch things like hardcoded credentials, eval() without user input context, etc.
 */
function _runPatternChecks(ast, filePath, sourceContent) {
  const findings = [];
  const lines = sourceContent ? sourceContent.split("\n") : [];
  const seenLines = new Set();

  function walk(node) {
    if (!node || typeof node !== "object" || !node.type) return;

    // ── eval() / Function() calls (always dangerous regardless of input) ──
    if (node.type === "CallExpression" && node.callee?.type === "Identifier" && node.callee.name === "eval") {
      const line = node.loc?.start?.line || 0;
      if (!seenLines.has(`eval:${line}`)) {
        seenLines.add(`eval:${line}`);
        findings.push({
          vulnerability_type: "Code Injection",
          severity: "critical",
          cwe_id: "CWE-94",
          title: "Use of eval()",
          description: "eval() executes arbitrary JavaScript code and is a security risk even without direct user input.",
          file_path: filePath,
          line_number: line,
          line_start: line,
          line_end: line,
          code_snippet: _getSnippet(lines, line),
          confidence: 0.95,
          analyzer_type: "sast-js",
          remediation: "Never use eval() with user-controlled input. Use JSON.parse() for data parsing or a safe expression evaluator.",
        });
      }
    }

    // ── document.write() ──
    if (node.type === "CallExpression" &&
        node.callee?.type === "MemberExpression" &&
        node.callee.object?.name === "document" &&
        node.callee.property?.name === "write") {
      const line = node.loc?.start?.line || 0;
      if (!seenLines.has(`docwrite:${line}`)) {
        seenLines.add(`docwrite:${line}`);
        findings.push({
          vulnerability_type: "Cross-Site Scripting (XSS)",
          severity: "medium",
          cwe_id: "CWE-79",
          title: "Use of document.write()",
          description: "document.write() can lead to XSS if used with untrusted input.",
          file_path: filePath,
          line_number: line,
          line_start: line,
          line_end: line,
          code_snippet: _getSnippet(lines, line),
          confidence: 0.80,
          analyzer_type: "sast-js",
          remediation: "Use DOM manipulation methods (createElement, textContent) instead of document.write().",
        });
      }
    }

    // ── innerHTML assignment (without taint — structural pattern) ──
    if (node.type === "AssignmentExpression" &&
        node.left?.type === "MemberExpression" &&
        node.left.property?.name === "innerHTML") {
      const line = node.loc?.start?.line || 0;
      if (!seenLines.has(`innerHTML:${line}`)) {
        seenLines.add(`innerHTML:${line}`);
        // Only add if not already caught by taint analysis
        const alreadyFound = findings.some(f => f.cwe_id === "CWE-79" && f.line_number === line && f.title?.includes("innerHTML"));
        if (!alreadyFound) {
          findings.push({
            vulnerability_type: "Cross-Site Scripting (XSS)",
            severity: "high",
            cwe_id: "CWE-79",
            title: "innerHTML assignment",
            description: "Direct innerHTML assignment is vulnerable to XSS if the value contains user input.",
            file_path: filePath,
            line_number: line,
            line_start: line,
            line_end: line,
            code_snippet: _getSnippet(lines, line),
            confidence: 0.70,
            analyzer_type: "sast-js",
            remediation: "Use textContent or innerText instead of innerHTML. If HTML is required, sanitize with DOMPurify.",
          });
        }
      }
    }

    // ── setTimeout/setInterval with string first arg ──
    if (node.type === "CallExpression" &&
        node.callee?.type === "Identifier" &&
        (node.callee.name === "setTimeout" || node.callee.name === "setInterval") &&
        node.arguments?.[0]?.type === "Literal" &&
        typeof node.arguments[0].value === "string") {
      const line = node.loc?.start?.line || 0;
      if (!seenLines.has(`timer:${line}`)) {
        seenLines.add(`timer:${line}`);
        findings.push({
          vulnerability_type: "Code Injection via setTimeout/setInterval",
          severity: "high",
          cwe_id: "CWE-94",
          title: `setTimeout/setInterval with string argument`,
          description: "setTimeout/setInterval with string argument acts like eval() and can lead to code injection.",
          file_path: filePath,
          line_number: line,
          line_start: line,
          line_end: line,
          code_snippet: _getSnippet(lines, line),
          confidence: 0.85,
          analyzer_type: "sast-js",
          remediation: "Pass a function reference instead of a string to setTimeout/setInterval.",
        });
      }
    }

    // ── Hardcoded secrets (variable = "literal") ──
    if (node.type === "VariableDeclarator" &&
        node.id?.type === "Identifier" &&
        node.init?.type === "Literal" &&
        typeof node.init.value === "string") {
      const name = node.id.name.toLowerCase();
      const value = node.init.value;
      if (_isSecretVariableName(name) && value.length > 5) {
        const line = node.loc?.start?.line || 0;
        if (!seenLines.has(`secret:${line}`)) {
          seenLines.add(`secret:${line}`);
          findings.push({
            vulnerability_type: "Hardcoded Credentials",
            severity: "high",
            cwe_id: "CWE-798",
            title: `Hardcoded secret: ${node.id.name}`,
            description: `Hardcoded secret '${node.id.name}' embedded in source code. Secrets should be stored in environment variables or a secrets manager.`,
            file_path: filePath,
            line_number: line,
            line_start: line,
            line_end: line,
            code_snippet: _getSnippet(lines, line),
            confidence: 0.90,
            analyzer_type: "sast-js",
            remediation: "Store secrets in environment variables (process.env) or a secrets manager. Never commit credentials to source control.",
          });
        }
      }
    }

    // ── Hardcoded secrets (member expression: obj.password = "literal") ──
    if (node.type === "AssignmentExpression" &&
        node.left?.type === "MemberExpression" &&
        node.left.property?.type === "Identifier" &&
        node.right?.type === "Literal" &&
        typeof node.right.value === "string") {
      const propName = node.left.property.name.toLowerCase();
      const value = node.right.value;
      if (_isSecretVariableName(propName) && value.length > 5) {
        const line = node.loc?.start?.line || 0;
        if (!seenLines.has(`secret_member:${line}`)) {
          seenLines.add(`secret_member:${line}`);
          findings.push({
            vulnerability_type: "Hardcoded Credentials",
            severity: "high",
            cwe_id: "CWE-798",
            title: `Hardcoded secret: ${node.left.property.name}`,
            description: `Hardcoded secret '${node.left.property.name}' embedded in source code.`,
            file_path: filePath,
            line_number: line,
            line_start: line,
            line_end: line,
            code_snippet: _getSnippet(lines, line),
            confidence: 0.90,
            analyzer_type: "sast-js",
            remediation: "Store secrets in environment variables or a secrets manager.",
          });
        }
      }
    }

    // ── Regex-based hardcoded credential check (catches what AST misses) ──
    // Already handled in the legacy js_scanner.js — don't duplicate here.
    // The SAST engine focuses on taint-based findings + AST structural patterns.

    // Recurse
    for (const key of Object.keys(node)) {
      if (key === "type" || key === "start" || key === "end" || key === "loc" || key === "raw") continue;
      const child = node[key];
      if (Array.isArray(child)) {
        for (const item of child) walk(item);
      } else if (child && typeof child === "object" && child.type) {
        walk(child);
      }
    }
  }

  walk(ast);
  return findings;
}

function _isSecretVariableName(name) {
  const secretPatterns = ["password", "passwd", "secret", "api_key", "apikey", "token", "auth_key", "db_pass", "private_key", "access_key", "secret_key"];
  return secretPatterns.some(p => name.includes(p));
}

function _getSnippet(lines, lineNum, context = 2) {
  if (!lineNum || !lines.length) return "";
  const start = Math.max(0, lineNum - context - 1);
  const end = Math.min(lines.length, lineNum + context);
  return lines.slice(start, end).join("\n");
}

// ─── CLI interface ────────────────────────────────────────────────────

function main() {
  const args = process.argv.slice(2);

  if (args.length === 0 || args.includes("--help") || args.includes("-h")) {
    console.error("Usage: node sast/index.js <file_path>");
    console.error("       node sast/index.js --stdin [--file-path=path.js] < file.js");
    process.exit(1);
  }

  let filePath = "";
  let sourceContent = "";

  if (args[0] === "--stdin") {
    // Read from stdin
    filePath = args.find(a => a.startsWith("--file-path="))?.split("=")[1] || "stdin.js";
    sourceContent = fs.readFileSync(0, "utf-8"); // fd 0 = stdin
  } else {
    filePath = args[0];
    if (!fs.existsSync(filePath)) {
      console.error(`File not found: ${filePath}`);
      process.exit(1);
    }
    sourceContent = fs.readFileSync(filePath, "utf-8");
  }

  const report = scanFileSAST(filePath, sourceContent);
  console.log(JSON.stringify(report, null, 2));
}

// Run CLI if executed directly
if (require.main === module) {
  main();
}

module.exports = { scanFileSAST };