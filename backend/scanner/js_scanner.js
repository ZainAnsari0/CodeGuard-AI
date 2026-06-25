/**
 * CodeGuard AI - JavaScript AST Scanner
 * Uses acorn to parse JavaScript/TypeScript and detect vulnerability patterns.
 * Runs inside the ephemeral scanner Docker container.
 */

const acorn = require("acorn");
const fs = require("fs");
const path = require("path");

const DANGEROUS_PATTERNS = {
  eval_usage: {
    type: "Dangerous Function",
    severity: "critical",
    cwe_id: "CWE-94",
    description: "Use of eval() is dangerous and can lead to code injection.",
  },
  document_write: {
    type: "XSS",
    severity: "medium",
    cwe_id: "CWE-79",
    description: "document.write() can lead to XSS if used with untrusted input.",
  },
  innerHTML: {
    type: "XSS",
    severity: "high",
    cwe_id: "CWE-79",
    description: "Direct innerHTML assignment is vulnerable to XSS.",
  },
  setTimeout_string: {
    type: "Dangerous Function",
    severity: "high",
    cwe_id: "CWE-94",
    description: "setTimeout/setInterval with string argument acts like eval().",
  },
  hardcoded_secret: {
    type: "Hardcoded Secret",
    severity: "high",
    cwe_id: "CWE-798",
    description: "Hardcoded API key, password, or secret detected.",
  },
};

function scanFile(filePath) {
  const findings = [];

  try {
    const source = fs.readFileSync(filePath, "utf-8");
    const lines = source.split("\n");

    // AST-based checks
    let ast;
    try {
      ast = acorn.parse(source, {
        ecmaVersion: 2022,
        sourceType: "module",
        locations: true,
      });
    } catch (parseError) {
      // Try as script if module parse fails
      try {
        ast = acorn.parse(source, {
          ecmaVersion: 2022,
          sourceType: "script",
          locations: true,
        });
      } catch (e2) {
        console.error(`[js_scanner] Warning: Failed to parse ${filePath}: ${e2.message}`);
      }
    }

    if (ast) {
      // Walk AST manually (simple recursive walk)
      function walk(node, callback) {
        if (!node || typeof node !== "object") return;
        callback(node);
        for (const key of Object.keys(node)) {
          const child = node[key];
          if (child && typeof child === "object") {
            if (Array.isArray(child)) {
              child.forEach((item) => walk(item, callback));
            } else if (child.type) {
              walk(child, callback);
            }
          }
        }
      }

      walk(ast, (node) => {
        // Check eval() usage
        if (
          node.type === "CallExpression" &&
          node.callee.type === "Identifier" &&
          node.callee.name === "eval"
        ) {
          findings.push(makeFinding("eval_usage", filePath, node.loc?.start?.line || 0, getSnippet(lines, node.loc?.start?.line)));
        }

        // Check document.write()
        if (
          node.type === "CallExpression" &&
          node.callee.type === "MemberExpression" &&
          node.callee.object?.name === "document" &&
          node.callee.property?.name === "write"
        ) {
          findings.push(makeFinding("document_write", filePath, node.loc?.start?.line || 0, getSnippet(lines, node.loc?.start?.line)));
        }

        // Check innerHTML assignment
        if (
          node.type === "AssignmentExpression" &&
          node.left?.type === "MemberExpression" &&
          node.left.property?.name === "innerHTML"
        ) {
          findings.push(makeFinding("innerHTML", filePath, node.loc?.start?.line || 0, getSnippet(lines, node.loc?.start?.line)));
        }

        // Check setTimeout/setInterval with string arg
        if (
          node.type === "CallExpression" &&
          node.callee.type === "Identifier" &&
          (node.callee.name === "setTimeout" || node.callee.name === "setInterval") &&
          node.arguments[0]?.type === "Literal" &&
          typeof node.arguments[0]?.value === "string"
        ) {
          findings.push(makeFinding("setTimeout_string", filePath, node.loc?.start?.line || 0, getSnippet(lines, node.loc?.start?.line)));
        }

        // Check hardcoded secrets in member expressions
        if (
          node.type === "AssignmentExpression" &&
          node.left?.type === "MemberExpression" &&
          typeof node.right?.value === "string" &&
          node.left.property?.name
        ) {
          const propName = node.left.property.name.toLowerCase();
          const value = node.right.value;
          if (
            (propName.includes("password") || propName.includes("secret") || propName.includes("api_key") || propName.includes("apikey")) &&
            value.length > 5
          ) {
            findings.push(makeFinding("hardcoded_secret", filePath, node.loc?.start?.line || 0, getSnippet(lines, node.loc?.start?.line)));
          }
        }

        // Check variable assignments with secrets
        if (
          node.type === "VariableDeclarator" &&
          node.id?.type === "Identifier" &&
          node.init?.type === "Literal" &&
          typeof node.init?.value === "string"
        ) {
          const name = node.id.name.toLowerCase();
          const value = node.init.value;
          if (
            (name.includes("password") || name.includes("secret") || name.includes("api_key") || name.includes("apikey") || name.includes("token")) &&
            value.length > 5
          ) {
            findings.push(makeFinding("hardcoded_secret", filePath, node.loc?.start?.line || 0, getSnippet(lines, node.loc?.start?.line)));
          }
        }
      });
    }

    // Regex-based checks (always runs, even when AST parsing fails)
    lines.forEach((line, idx) => {
      // Hardcoded credential regex — exclude matches inside SQL/template literal contexts
      // where 'password = ${...}' or 'password = :var' are NOT actual hardcoded secrets.
      // Positive: const API_KEY = "sk-abc123def456"
      // Negative: AND password = '${password}'  (SQL injection, not hardcoded)
      // Negative: password = :password           (parameterized query placeholder)
      const hardcodedCredMatch = line.match(/(?:password|passwd|secret|api_key|apikey|token|auth_key)\s*[:=]\s*['"][^'"]{8,}['"]/i);
      if (hardcodedCredMatch) {
        const matchedText = hardcodedCredMatch[0];
        // Skip if the quoted value contains template expressions like ${...} — it's dynamic, not hardcoded
        if (/\$\{[^}]+\}/.test(matchedText)) return;
        // Skip if inside a SQL context (line contains SQL keywords near the match)
        const lineLower = line.toLowerCase();
        if (/\b(?:select|insert|update|delete|where|from|and|or)\b/i.test(line) &&
            /=\s*['"][^'"]*\$\{|=\s*['"][^'']*:\w/.test(line)) return;
        const lineNum = idx + 1;
        // Avoid duplicating AST findings
        const alreadyFound = findings.some(f => f.line_number === lineNum && f.vulnerability_type === "Hardcoded Secret");
        if (!alreadyFound) {
          findings.push(makeFinding("hardcoded_secret", filePath, lineNum, getSnippet(lines, lineNum)));
        }
      }
    });

  } catch (error) {
    // Skip files that can't be read
  }

  return findings;
}

function getSnippet(lines, lineNum, context = 2) {
  if (lineNum === null || lineNum === undefined || !lines) return "";
  const start = Math.max(0, lineNum - context - 1);
  const end = Math.min(lines.length, lineNum + context);
  return lines.slice(start, end).join("\n");
}

function makeFinding(patternKey, filePath, line, snippet) {
  const pattern = DANGEROUS_PATTERNS[patternKey];
  return {
    vulnerability_type: pattern.type,
    severity: pattern.severity,
    cwe_id: pattern.cwe_id,
    file_path: filePath,
    line_number: line,
    code_snippet: snippet || "",
    description: pattern.description,
    confidence: pattern.severity === "critical" ? 0.95 : pattern.severity === "high" ? 0.85 : 0.7,
    analyzer_type: "js_ast",
  };
}

function scanDirectory(dir) {
  const findings = [];
  const extensions = [".js", ".jsx", ".ts", ".tsx", ".mjs"];

  function walkDir(currentDir) {
    let entries;
    try {
      entries = fs.readdirSync(currentDir, { withFileTypes: true });
    } catch (err) {
      console.error(`[js_scanner] Warning: Cannot read directory ${currentDir}: ${err.message}`);
      return;
    }
    for (const entry of entries) {
      const fullPath = path.join(currentDir, entry.name);
      if (entry.isDirectory() && !entry.name.startsWith(".") && entry.name !== "node_modules") {
        walkDir(fullPath);
      } else if (entry.isFile()) {
        const ext = path.extname(entry.name).toLowerCase();
        if (extensions.includes(ext)) {
          findings.push(...scanFile(fullPath));
        }
      }
    }
  }

  walkDir(dir);
  return findings;
}

// Main
const target = process.argv[2] || "/code";
const results = scanDirectory(target);
console.log(JSON.stringify({ findings: results, total_findings: results.length }, null, 2));