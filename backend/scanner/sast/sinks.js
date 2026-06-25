/**
 * CodeGuard AI - Sink Detection Module
 * Identifies dangerous call sites where tainted data may cause vulnerabilities.
 */

// ─── Dangerous Sink Definitions ──────────────────────────────────────

const DANGEROUS_SINKS = {
  // ═══ Code Execution ════════════════════════════════════════════════
  "eval": {
    category: "code_execution", vulnerability_type: "Code Injection", cwe_id: "CWE-94",
    severity: "critical", description: "eval() executes arbitrary JavaScript code",
    taint_arg: 0,
  },
  "Function": {
    category: "code_execution", vulnerability_type: "Code Injection", cwe_id: "CWE-94",
    severity: "critical", description: "Function constructor executes code from strings",
    taint_arg: -1, // last argument
  },
  "setTimeout": {
    category: "code_execution", vulnerability_type: "Code Injection via setTimeout", cwe_id: "CWE-94",
    severity: "high", description: "setTimeout with string argument acts as eval()",
    taint_arg: 0, string_only: true,
  },
  "setInterval": {
    category: "code_execution", vulnerability_type: "Code Injection via setInterval", cwe_id: "CWE-94",
    severity: "high", description: "setInterval with string argument acts as eval()",
    taint_arg: 0, string_only: true,
  },

  // ═══ Command Execution ══════════════════════════════════════════════
  "exec": {
    category: "command_execution", vulnerability_type: "Command Injection", cwe_id: "CWE-78",
    severity: "critical", description: "child_process.exec() executes shell commands",
    taint_arg: 0,
  },
  "execSync": {
    category: "command_execution", vulnerability_type: "Command Injection", cwe_id: "CWE-78",
    severity: "critical", description: "child_process.execSync() executes shell commands synchronously",
    taint_arg: 0,
  },
  "spawn": {
    category: "command_execution", vulnerability_type: "Command Injection", cwe_id: "CWE-78",
    severity: "high", description: "child_process.spawn() launches a process",
    taint_arg: 0,
  },
  "execFile": {
    category: "command_execution", vulnerability_type: "Command Injection", cwe_id: "CWE-78",
    severity: "high", description: "child_process.execFile() executes a file",
    taint_arg: 1,
  },

  // ═══ SQL Injection ══════════════════════════════════════════════════
  "db.query": {
    category: "sql_injection", vulnerability_type: "SQL Injection", cwe_id: "CWE-89",
    severity: "critical", description: "Database query with unsanitized input",
    taint_arg: 0,
  },
  "db.run": {
    category: "sql_injection", vulnerability_type: "SQL Injection", cwe_id: "CWE-89",
    severity: "critical", description: "Database run with unsanitized input (sqlite3)",
    taint_arg: 0,
  },
  "db.get": {
    category: "sql_injection", vulnerability_type: "SQL Injection", cwe_id: "CWE-89",
    severity: "critical", description: "Database get with unsanitized input (sqlite3)",
    taint_arg: 0,
  },
  "db.all": {
    category: "sql_injection", vulnerability_type: "SQL Injection", cwe_id: "CWE-89",
    severity: "critical", description: "Database all with unsanitized input (sqlite3)",
    taint_arg: 0,
  },
  "connection.query": {
    category: "sql_injection", vulnerability_type: "SQL Injection", cwe_id: "CWE-89",
    severity: "critical", description: "MySQL/PostgreSQL query with unsanitized input",
    taint_arg: 0,
  },
  "pool.query": {
    category: "sql_injection", vulnerability_type: "SQL Injection", cwe_id: "CWE-89",
    severity: "critical", description: "Connection pool query with unsanitized input",
    taint_arg: 0,
  },
  // Generic method-name matches for any variable.query/.run/.get/.all/.exec
  ".query": {
    category: "sql_injection", vulnerability_type: "SQL Injection", cwe_id: "CWE-89",
    severity: "critical", description: "Potential SQL query with unsanitized input",
    taint_arg: 0, isMethodOnly: true,
  },

  // ═══ Path Traversal ══════════════════════════════════════════════════
  "fs.readFile": {
    category: "path_traversal", vulnerability_type: "Path Traversal", cwe_id: "CWE-22",
    severity: "high", description: "Reading file with user-controlled path",
    taint_arg: 0,
  },
  "fs.readFileSync": {
    category: "path_traversal", vulnerability_type: "Path Traversal", cwe_id: "CWE-22",
    severity: "high", description: "Synchronous read with user-controlled path",
    taint_arg: 0,
  },
  "fs.writeFile": {
    category: "path_traversal", vulnerability_type: "Path Traversal", cwe_id: "CWE-22",
    severity: "high", description: "Writing file with user-controlled path",
    taint_arg: 0,
  },
  "fs.writeFileSync": {
    category: "path_traversal", vulnerability_type: "Path Traversal", cwe_id: "CWE-22",
    severity: "high", description: "Synchronous write with user-controlled path",
    taint_arg: 0,
  },
  "fs.unlink": {
    category: "path_traversal", vulnerability_type: "Path Traversal", cwe_id: "CWE-22",
    severity: "critical", description: "Deleting file with user-controlled path",
    taint_arg: 0,
  },
  "fs.unlinkSync": {
    category: "path_traversal", vulnerability_type: "Path Traversal", cwe_id: "CWE-22",
    severity: "critical", description: "Synchronous delete with user-controlled path",
    taint_arg: 0,
  },
  "fs.createReadStream": {
    category: "path_traversal", vulnerability_type: "Path Traversal", cwe_id: "CWE-22",
    severity: "high", description: "Stream read with user-controlled path",
    taint_arg: 0,
  },
  "fs.createWriteStream": {
    category: "path_traversal", vulnerability_type: "Path Traversal", cwe_id: "CWE-22",
    severity: "high", description: "Stream write with user-controlled path",
    taint_arg: 0,
  },

  // ═══ SSRF ═══════════════════════════════════════════════════════════
  "fetch": {
    category: "ssrf", vulnerability_type: "Server-Side Request Forgery", cwe_id: "CWE-918",
    severity: "high", description: "HTTP request with user-controlled URL",
    taint_arg: 0,
  },
  "axios.get": {
    category: "ssrf", vulnerability_type: "SSRF", cwe_id: "CWE-918",
    severity: "high", description: "Axios GET with user-controlled URL",
    taint_arg: 0,
  },
  "axios.post": {
    category: "ssrf", vulnerability_type: "SSRF", cwe_id: "CWE-918",
    severity: "high", description: "Axios POST with user-controlled URL",
    taint_arg: 0,
  },
  "axios.put": {
    category: "ssrf", vulnerability_type: "SSRF", cwe_id: "CWE-918",
    severity: "high", description: "Axios PUT with user-controlled URL",
    taint_arg: 0,
  },
  "axios.delete": {
    category: "ssrf", vulnerability_type: "SSRF", cwe_id: "CWE-918",
    severity: "high", description: "Axios DELETE with user-controlled URL",
    taint_arg: 0,
  },
  "http.get": {
    category: "ssrf", vulnerability_type: "SSRF", cwe_id: "CWE-918",
    severity: "high", description: "Node.js http.get with user-controlled URL",
    taint_arg: 0,
  },
  "http.request": {
    category: "ssrf", vulnerability_type: "SSRF", cwe_id: "CWE-918",
    severity: "high", description: "Node.js http.request with user-controlled URL",
    taint_arg: 0,
  },
  "https.get": {
    category: "ssrf", vulnerability_type: "SSRF", cwe_id: "CWE-918",
    severity: "high", description: "Node.js https.get with user-controlled URL",
    taint_arg: 0,
  },
  "https.request": {
    category: "ssrf", vulnerability_type: "SSRF", cwe_id: "CWE-918",
    severity: "high", description: "Node.js https.request with user-controlled URL",
    taint_arg: 0,
  },

  // ═══ XSS ════════════════════════════════════════════════════════════
  "res.send": {
    category: "xss", vulnerability_type: "Cross-Site Scripting (XSS)", cwe_id: "CWE-79",
    severity: "high", description: "Sending unsanitized HTML response",
    taint_arg: 0,
  },
  "res.write": {
    category: "xss", vulnerability_type: "XSS", cwe_id: "CWE-79",
    severity: "high", description: "Writing unsanitized content to HTTP response",
    taint_arg: 0,
  },
  "res.end": {
    category: "xss", vulnerability_type: "XSS", cwe_id: "CWE-79",
    severity: "medium", description: "Ending response with unsanitized data",
    taint_arg: 0,
  },
  "res.json": {
    category: "xss", vulnerability_type: "XSS (JSON-based)", cwe_id: "CWE-79",
    severity: "medium", description: "JSON response — lower XSS risk",
    taint_arg: 0,
  },
  "innerHTML": {
    category: "xss", vulnerability_type: "DOM-based XSS", cwe_id: "CWE-79",
    severity: "high", description: "innerHTML assignment with user-controlled content",
    taint_arg: "right",
  },
  "document.write": {
    category: "xss", vulnerability_type: "DOM-based XSS", cwe_id: "CWE-79",
    severity: "high", description: "document.write with user-controlled content",
    taint_arg: 0,
  },

  // ═══ Open Redirect ══════════════════════════════════════════════════
  "res.redirect": {
    category: "open_redirect", vulnerability_type: "Open Redirect", cwe_id: "CWE-601",
    severity: "medium", description: "Redirect to user-controlled URL",
    taint_arg: 0,
  },
  "res.location": {
    category: "open_redirect", vulnerability_type: "Open Redirect", cwe_id: "CWE-601",
    severity: "medium", description: "Setting Location header to user-controlled URL",
    taint_arg: 0,
  },

  // ═══ Header Injection ═══════════════════════════════════════════════
  "res.setHeader": {
    category: "header_injection", vulnerability_type: "HTTP Header Injection", cwe_id: "CWE-113",
    severity: "medium", description: "Setting response header with user-controlled value",
    taint_arg: 1,
  },
  "res.append": {
    category: "header_injection", vulnerability_type: "Header Injection", cwe_id: "CWE-113",
    severity: "medium", description: "Appending to response header with user-controlled value",
    taint_arg: 1,
  },

  // ═══ Prototype Pollution ═════════════════════════════════════════════
  "merge": {
    category: "prototype_pollution", vulnerability_type: "Prototype Pollution", cwe_id: "CWE-1321",
    severity: "high", description: "Deep merge of user-controlled objects can pollute prototype",
    taint_arg: 0,
  },
  "defaultsDeep": {
    category: "prototype_pollution", vulnerability_type: "Prototype Pollution", cwe_id: "CWE-1321",
    severity: "high", description: "lodash.defaultsDeep with user-controlled source",
    taint_arg: 0,
  },
};

// Method names that are SQL-like when called on a variable (any .query, .run, .get, .all, .exec)
const SQL_METHOD_NAMES = new Set(["query", "run", "get", "all", "exec", "execute"]);

// ─── Sink Detector ───────────────────────────────────────────────────

class SinkDetector {
  constructor(taintStore, scopeTree, sourceCode) {
    this.taintStore = taintStore;
    this.scopeTree = scopeTree;
    this.sourceCode = sourceCode;
    this.lines = sourceCode ? sourceCode.split("\n") : [];
    this.rawFindings = [];
  }

  /** Detect sinks in the AST and check for tainted arguments */
  detectSinks(ast) {
    const self = this;

    function walk(node, scopeId) {
      if (!node || typeof node !== "object" || !node.type) return;

      // ── CallExpression: check for dangerous sinks ──
      if (node.type === "CallExpression") {
        const sinkInfo = self._identifySink(node);
        if (sinkInfo) {
          self._checkSinkArgs(node, sinkInfo, scopeId);
        }
      }

      // ── NewExpression: check for new Function() ──
      if (node.type === "NewExpression") {
        if (node.callee?.type === "Identifier" && node.callee.name === "Function") {
          const lastArg = node.arguments?.[node.arguments.length - 1];
          if (lastArg) {
            const taint = self._resolveArgTaint(lastArg, scopeId);
            if (taint) {
              self._emitFinding(DANGEROUS_SINKS["Function"], node, taint, scopeId);
            }
          }
        }
      }

      // ── AssignmentExpression: check innerHTML ──
      if (node.type === "AssignmentExpression") {
        if (node.left?.type === "MemberExpression" && node.left.property?.name === "innerHTML") {
          const taint = self._resolveArgTaint(node.right, scopeId);
          if (taint) {
            self._emitFinding(DANGEROUS_SINKS.innerHTML, node, taint, scopeId);
          }
        }
        // outerHTML too
        if (node.left?.type === "MemberExpression" && node.left.property?.name === "outerHTML") {
          const taint = self._resolveArgTaint(node.right, scopeId);
          if (taint) {
            self._emitFinding(DANGEROUS_SINKS.innerHTML, node, taint, scopeId);
          }
        }
      }

      // Recurse, tracking scope changes
      let childScopeId = scopeId;
      // If this node created a new scope, find it
      if (node.type === "FunctionDeclaration" || node.type === "FunctionExpression" || node.type === "ArrowFunctionExpression") {
        const funcScope = self._findScopeForNode(node);
        if (funcScope) childScopeId = funcScope.id;
      }

      for (const key of Object.keys(node)) {
        if (key === "type" || key === "start" || key === "end" || key === "loc" || key === "raw") continue;
        const child = node[key];
        if (Array.isArray(child)) {
          for (const item of child) walk(item, childScopeId);
        } else if (child && typeof child === "object" && child.type) {
          walk(child, childScopeId);
        }
      }
    }

    walk(ast, this.scopeTree.root.id);
    return this.rawFindings;
  }

  /** Identify what kind of sink a CallExpression is */
  _identifySink(node) {
    // Pattern 1: Direct call — eval(x), setTimeout(x)
    if (node.callee?.type === "Identifier") {
      const name = node.callee.name;
      if (DANGEROUS_SINKS[name]) return DANGEROUS_SINKS[name];
    }

    // Pattern 2: Member call — db.query(x), fs.readFile(x), res.send(x)
    if (node.callee?.type === "MemberExpression") {
      const methodName = node.callee.property?.name;
      const objectName = this._getIdentifierName(node.callee.object);
      const fullKey = objectName ? `${objectName}.${methodName}` : null;

      // Full key match: fs.readFile, db.query, res.send, etc.
      if (fullKey && DANGEROUS_SINKS[fullKey]) return DANGEROUS_SINKS[fullKey];

      // Method-only match for SQL methods: .query, .run, .get, .all
      if (methodName && SQL_METHOD_NAMES.has(methodName)) {
        // Only treat as SQL sink if the first argument looks like a SQL string
        // or if the method is called on a known DB-like variable
        const firstArg = node.arguments?.[0];
        if (firstArg && this._looksLikeSql(firstArg)) {
          return DANGEROUS_SINKS[".query"] || {
            category: "sql_injection",
            vulnerability_type: "SQL Injection",
            cwe_id: "CWE-89",
            severity: "high",
            description: `Possible SQL injection via ${methodName}()`,
            taint_arg: 0,
          };
        }
      }

      // Method-only match for other sinks: setTimeout, setInterval
      if (methodName && DANGEROUS_SINKS[methodName]) return DANGEROUS_SINKS[methodName];
    }

    return null;
  }

  /** Check if an expression looks like it contains SQL */
  _looksLikeSql(node) {
    if (!node) return false;
    // Template literal with SQL keywords
    if (node.type === "TemplateLiteral") {
      const quasis = node.quasis || [];
      const text = quasis.map(q => q.value?.raw || "").join(" ");
      return /\b(?:SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|FROM|WHERE)\b/i.test(text);
    }
    // String literal with SQL keywords
    if (node.type === "Literal" && typeof node.value === "string") {
      return /\b(?:SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|FROM|WHERE)\b/i.test(node.value);
    }
    // Binary expression (concat) — likely SQL
    if (node.type === "BinaryExpression" && node.operator === "+") {
      return this._looksLikeSql(node.left) || this._looksLikeSql(node.right);
    }
    // Identifier — check if the variable name suggests SQL
    if (node.type === "Identifier") {
      return /^(?:sql|query|stmt|command)/i.test(node.name);
    }
    return false;
  }

  /** Check arguments to a sink for taint */
  _checkSinkArgs(node, sinkInfo, scopeId) {
    const args = node.arguments || [];
    const taintArgIndex = sinkInfo.taint_arg;

    // Special: setTimeout/setInterval only dangerous with string first arg
    if (sinkInfo.string_only && args[0]?.type === "Literal" && typeof args[0].value === "string") {
      // It IS a string arg — check for taint
      const taint = this._resolveArgTaint(args[0], scopeId);
      if (taint) this._emitFinding(sinkInfo, node, taint, scopeId);
      return;
    }
    if (sinkInfo.string_only && args[0]?.type !== "Literal") {
      // Not a string first arg — safe (it's a function reference)
      return;
    }

    // Check specific argument index
    for (let i = 0; i < args.length; i++) {
      const taint = this._resolveArgTaint(args[i], scopeId);
      if (!taint) continue;

      if (taintArgIndex === -1 && i === args.length - 1) {
        // Last arg (new Function)
        this._emitFinding(sinkInfo, node, taint, scopeId);
      } else if (taintArgIndex === i) {
        this._emitFinding(sinkInfo, node, taint, scopeId);
      } else if (taintArgIndex === "right") {
        // innerHTML — handled separately
      } else if (taintArgIndex === 0 && i === 0) {
        this._emitFinding(sinkInfo, node, taint, scopeId);
      }
    }
  }

  /** Resolve taint of an argument expression */
  _resolveArgTaint(node, scopeId) {
    if (!node) return null;

    // Identifier — look up in taint store
    if (node.type === "Identifier") {
      return this.taintStore.getVariableTaint(scopeId, node.name);
    }

    // MemberExpression — check expression taint then object taint
    if (node.type === "MemberExpression") {
      const exprTaint = this.taintStore.getExpressionTaint(node, scopeId);
      if (exprTaint) return exprTaint;

      // Check if the object is tainted
      const objName = this._getIdentifierName(node.object);
      if (objName) {
        const objTaint = this.taintStore.getVariableTaint(scopeId, objName);
        if (objTaint) return objTaint;
      }

      // Recursively check the object
      return this._resolveArgTaint(node.object, scopeId);
    }

    // Template literal — check embedded expressions
    if (node.type === "TemplateLiteral") {
      for (const expr of node.expressions || []) {
        const t = this._resolveArgTaint(expr, scopeId);
        if (t) return t;
      }
      return null;
    }

    // Binary expression (string concat) — check both sides
    if (node.type === "BinaryExpression" && node.operator === "+") {
      return this._resolveArgTaint(node.left, scopeId) ||
             this._resolveArgTaint(node.right, scopeId);
    }

    // Call expression — check if it's a sanitizer or returns tainted data
    if (node.type === "CallExpression") {
      const { SANITIZERS } = require("./sanitizers");
      const calleeName = this._getCalleeName(node);
      if (calleeName && SANITIZERS[calleeName]) {
        const san = SANITIZERS[calleeName];
        if (san.strength === "strong") return null; // Taint removed
      }
      // Check arguments for taint (function might pass through)
      for (const arg of node.arguments || []) {
        const t = this._resolveArgTaint(arg, scopeId);
        if (t) return t;
      }
      return null;
    }

    return null;
  }

  /** Emit a raw finding */
  _emitFinding(sinkInfo, node, taintLabel, scopeId) {
    // Check for parameterized queries (SQL-specific safe pattern)
    if (sinkInfo.category === "sql_injection" && node.type === "CallExpression") {
      if (this._isParameterizedQuery(node)) {
        return; // Safe — parameterized query
      }
    }

    // Check for safe patterns
    if (this._isSafePattern(sinkInfo, node)) {
      return;
    }

    const line = node.loc?.start?.line || 0;
    const snippet = this._getSnippet(line);

    // Build data flow trace
    const dataFlow = this._buildDataFlow(taintLabel, node);

    // Calculate confidence
    const confidence = this._calculateConfidence(sinkInfo, taintLabel, node);

    // Build title
    const title = `${sinkInfo.vulnerability_type} via ${taintLabel.sourceType}`;

    this.rawFindings.push({
      vulnerability_type: sinkInfo.vulnerability_type,
      severity: sinkInfo.severity,
      cwe_id: sinkInfo.cwe_id,
      title,
      description: sinkInfo.description,
      file_path: "", // Will be set by caller
      line_number: line,
      line_start: line,
      line_end: line,
      code_snippet: snippet,
      confidence,
      analyzer_type: "sast-js",
      data_flow: dataFlow,
      remediation: this._getRemediation(sinkInfo.cwe_id),
      finding_metadata: {
        sink_category: sinkInfo.category,
        taint_source: taintLabel.sourceType,
        taint_path: taintLabel.propagationPath,
        sanitizers: taintLabel.sanitizers || [],
      },
    });
  }

  /** Check if a database call uses parameterized queries */
  _isParameterizedQuery(node) {
    const args = node.arguments || [];
    const sqlArg = args[0];
    const paramsArg = args[1];

    // If there's a second argument (params), it's likely parameterized
    if (paramsArg) {
      if (sqlArg?.type === "Literal" && typeof sqlArg.value === "string") {
        if (sqlArg.value.includes("?") || sqlArg.value.includes("$1") || sqlArg.value.includes(":1")) {
          return true;
        }
      }
      if (sqlArg?.type === "TemplateLiteral" && (sqlArg.expressions || []).length === 0 && paramsArg) {
        return true;
      }
      // Object params: { id: userId }
      if (paramsArg.type === "ObjectExpression" && sqlArg?.type === "Literal") {
        if (sqlArg.value.includes(":") || sqlArg.value.includes("$1")) {
          return true;
        }
      }
    }
    return false;
  }

  /** Check for known safe patterns that suppress the finding */
  _isSafePattern(sinkInfo, node) {
    // res.json() with non-string literal
    if (sinkInfo.category === "xss" && node.arguments?.[0]?.type === "Literal") {
      const val = node.arguments[0].value;
      if (typeof val === "number" || typeof val === "boolean") return true;
    }

    // res.redirect with fixed internal path
    if (sinkInfo.category === "open_redirect" && node.arguments?.[0]?.type === "Literal") {
      const val = node.arguments[0].value;
      if (typeof val === "string" && val.startsWith("/") && !val.includes("//")) return true;
    }

    // fs.readFile with hardcoded path literal
    if (sinkInfo.category === "path_traversal" && node.arguments?.[0]?.type === "Literal") {
      return typeof node.arguments[0].value === "string";
    }

    return false;
  }

  /** Build a data flow trace from source to sink */
  _buildDataFlow(taintLabel, sinkNode) {
    return {
      source: {
        type: taintLabel.sourceType,
        line: taintLabel.sourceLine,
        code: this._getSnippet(taintLabel.sourceLine),
      },
      propagation: (taintLabel.propagationPath || []).map((step, i) => ({
        variable: step,
        line: taintLabel.sourceLine + i, // Approximate
        code: this._getSnippet(taintLabel.sourceLine + i),
        operation: i === 0 ? "source_access" : "assignment",
      })),
      sink: {
        type: this._getCalleeName(sinkNode) || "unknown",
        line: sinkNode.loc?.start?.line || 0,
        code: this._getSnippet(sinkNode.loc?.start?.line || 0),
      },
    };
  }

  /** Calculate confidence score */
  _calculateConfidence(sinkInfo, taintLabel, node) {
    let confidence = 0.90;

    // Weak sanitizer present
    const weakSans = (taintLabel.sanitizers || []).filter(s => s.strength === "weak");
    if (weakSans.length > 0) confidence -= 0.15;

    // Strong sanitizer present — should have been filtered already, but just in case
    const strongSans = (taintLabel.sanitizers || []).filter(s => s.strength === "strong");
    if (strongSans.length > 0) return 0;

    // Long propagation chain
    const chainLen = (taintLabel.propagationPath || []).length;
    if (chainLen > 5) confidence -= 0.10;
    else if (chainLen > 3) confidence -= 0.05;

    // Environment source — less risky
    if (taintLabel.category === "environment") confidence -= 0.30;

    return Math.max(0.1, Math.min(1.0, confidence));
  }

  /** Get remediation advice for a CWE */
  _getRemediation(cweId) {
    const remediations = {
      "CWE-89": "Use parameterized queries (prepared statements) instead of string concatenation. For Node.js with sqlite3: db.get('SELECT * FROM users WHERE id = ?', [id]). For mysql2: connection.query('SELECT * FROM users WHERE id = ?', [id]).",
      "CWE-78": "Never pass user input directly to shell commands. Use execFile() with argument arrays instead of exec() with string concatenation. Validate and allowlist all inputs.",
      "CWE-94": "Never use eval() with user-controlled input. Use JSON.parse() for data parsing. For dynamic code, use Function constructors with strict allowlisting.",
      "CWE-79": "Escape all user-supplied data before rendering in HTML. Use textContent instead of innerHTML. Apply Content Security Policy headers. Use DOMPurify for HTML sanitization.",
      "CWE-22": "Validate and normalize file paths using path.resolve() and path.normalize(). Restrict file access to a known-safe base directory using startsWith() checks. Never pass user input directly to filesystem APIs.",
      "CWE-918": "Validate URLs against an allowlist of permitted domains/schemes. Block requests to internal/private IP ranges. Use a dedicated HTTP client with URL validation.",
      "CWE-601": "Validate redirect targets against an allowlist of permitted paths. Only allow relative URLs starting with '/'. Never redirect to user-supplied absolute URLs.",
      "CWE-113": "Validate all header values for CRLF sequences (\\r\\n). Use framework-provided header setting methods. Never pass user input directly to setHeader().",
      "CWE-1321": "Use Object.freeze(Object.prototype) or __proto__-safe merge implementations. Validate object keys before merging. Avoid deep merge of user-controlled objects.",
    };
    return remediations[cweId] || "Review the identified code and apply security best practices.";
  }

  // ─── Utility methods ────────────────────────────────────────────────

  _getIdentifierName(node) {
    if (!node) return null;
    if (node.type === "Identifier") return node.name;
    if (node.type === "MemberExpression") return this._getIdentifierName(node.object);
    return null;
  }

  _getCalleeName(node) {
    if (!node?.callee) return null;
    if (node.callee.type === "Identifier") return node.callee.name;
    if (node.callee.type === "MemberExpression") {
      const obj = this._getIdentifierName(node.callee.object);
      const prop = node.callee.property?.name;
      if (obj && prop) return `${obj}.${prop}`;
      if (prop) return prop;
    }
    return null;
  }

  _getSnippet(lineNum, context = 2) {
    if (!lineNum || !this.lines.length) return "";
    const start = Math.max(0, lineNum - context - 1);
    const end = Math.min(this.lines.length, lineNum + context);
    return this.lines.slice(start, end).join("\n");
  }

  _findScopeForNode(node) {
    for (const [, scope] of this.scopeTree.scopes) {
      if (scope.node === node) return scope;
    }
    return null;
  }
}

module.exports = { DANGEROUS_SINKS, SinkDetector };