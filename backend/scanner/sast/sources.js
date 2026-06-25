/**
 * CodeGuard AI - Source Detection Module
 * Identifies untrusted input sources (taint origins) in Express.js / Node.js code.
 */

// ─── Taint Source Definitions ────────────────────────────────────────

const TAINT_SOURCES = {
  // Express.js request properties
  "req.query":      { category: "http_request", description: "URL query parameters", severity_base: "high" },
  "req.body":       { category: "http_request", description: "HTTP request body", severity_base: "high" },
  "req.params":     { category: "http_request", description: "URL path parameters", severity_base: "high" },
  "req.headers":    { category: "http_request", description: "HTTP request headers", severity_base: "medium" },
  "req.cookies":    { category: "http_request", description: "Request cookies", severity_base: "medium" },
  "req.url":        { category: "http_request", description: "Request URL", severity_base: "medium" },
  "req.path":       { category: "http_request", description: "Request path", severity_base: "medium" },
  "req.originalUrl":{ category: "http_request", description: "Original request URL", severity_base: "medium" },
  "req.ip":         { category: "http_request", description: "Client IP (spoofable)", severity_base: "low" },
  "req.files":      { category: "file_upload",   description: "Uploaded files", severity_base: "high" },
  "req.file":       { category: "file_upload",   description: "Single uploaded file", severity_base: "high" },
  "req.signedCookies": { category: "http_request", description: "Signed cookies", severity_base: "medium" },
  "req.fresh":      { category: "http_request", description: "Cache freshness (header-derived)", severity_base: "low" },
  "req.stale":      { category: "http_request", description: "Cache staleness (header-derived)", severity_base: "low" },
  "req.xhr":        { category: "http_request", description: "XHR flag (header-derived)", severity_base: "low" },
  "req.protocol":   { category: "http_request", description: "Request protocol (header-derived)", severity_base: "low" },
  "req.host":       { category: "http_request", description: "Host header (spoofable)", severity_base: "medium" },
  "req.hostname":   { category: "http_request", description: "Hostname from Host header", severity_base: "medium" },
  "req.subdomains": { category: "http_request", description: "Subdomains from Host header", severity_base: "medium" },
  "req.acceptedLanguages": { category: "http_request", description: "Accept-Language header", severity_base: "low" },

  // Aliased patterns (e.g., `request` instead of `req`)
  "request.query":      { alias_for: "req.query" },
  "request.body":       { alias_for: "req.body" },
  "request.params":     { alias_for: "req.params" },
  "request.headers":    { alias_for: "req.headers" },
  "request.cookies":    { alias_for: "req.cookies" },
  "request.url":        { alias_for: "req.url" },
  "request.originalUrl":{ alias_for: "req.originalUrl" },

  // CLI input sources
  "process.argv":   { category: "cli_input", description: "Command-line arguments", severity_base: "medium" },
  "process.stdin":  { category: "cli_input", description: "Standard input", severity_base: "high" },
};

// Express route handler patterns — when detected, the first callback
// parameter (conventionally `req`) is a taint source
const EXPRESS_ROUTE_PATTERNS = [
  "app.get", "app.post", "app.put", "app.patch", "app.delete", "app.all", "app.use",
  "router.get", "router.post", "router.put", "router.patch", "router.delete", "router.all", "router.use",
];

// ─── Source Detector ─────────────────────────────────────────────────

class SourceDetector {
  constructor(scopeTree) {
    this.scopeTree = scopeTree;
    this.taintStore = null; // set by detectSources
    this._reqAliases = new Map(); // scopeId → Set of variable names that are `req`
  }

  /**
   * Walk the AST, identify taint sources, and populate the TaintStore.
   * @param {object} ast - ESTree AST
   * @param {object} taintStore - TaintStore instance (from taint.js)
   * @returns {object} The populated TaintStore
   */
  detectSources(ast, taintStore) {
    this.taintStore = taintStore;
    const { ASTTraversal } = require("./traversal");
    const traversal = new ASTTraversal(ast);

    // Phase 1: Detect Express route handlers to identify `req` aliases
    this._detectExpressHandlers(ast, traversal);

    // Phase 2: Walk all MemberExpressions and VariableDeclarators
    this._walkForSources(ast);

    return this.taintStore;
  }

  /** Detect Express route handler callbacks and register `req` as a taint source */
  _detectExpressHandlers(ast, traversal) {
    // We need to find patterns like: app.get("/path", (req, res) => { ... })
    // or: router.post("/path", function(req, res) { ... })
    const self = this;

    function walkForRoutes(node) {
      if (!node || typeof node !== "object" || !node.type) return;

      if (node.type === "CallExpression" &&
          node.callee?.type === "MemberExpression") {
        const methodName = node.callee.property?.name;
        const objectName = self._getIdentifierName(node.callee.object);

        if (objectName && methodName && EXPRESS_ROUTE_PATTERNS.includes(`${objectName}.${methodName}`)) {
          // The last argument that is a function is the route handler
          const handlerArg = self._findHandlerArg(node.arguments);
          if (handlerArg) {
            self._registerReqFromHandler(handlerArg);
          }
        }
      }

      // Recurse
      for (const key of Object.keys(node)) {
        if (key === "type" || key === "start" || key === "end" || key === "loc" || key === "raw") continue;
        const child = node[key];
        if (Array.isArray(child)) {
          for (const item of child) walkForRoutes(item);
        } else if (child && typeof child === "object" && child.type) {
          walkForRoutes(child);
        }
      }
    }

    walkForRoutes(ast);
  }

  /** Find the handler function argument in an Express route call */
  _findHandlerArg(args) {
    if (!args || args.length === 0) return null;
    // The handler is usually the last function argument (after middleware)
    for (let i = args.length - 1; i >= 0; i--) {
      const arg = args[i];
      if (arg?.type === "ArrowFunctionExpression" || arg?.type === "FunctionExpression") {
        return arg;
      }
    }
    return null;
  }

  /** Register the first parameter of a route handler as a `req` alias */
  _registerReqFromHandler(handlerNode) {
    const firstParam = handlerNode.params?.[0];
    if (firstParam?.type === "Identifier") {
      // Find or create a scope for this handler
      // The scope builder already created it, we just need to find it
      const funcScope = this._findScopeForNode(handlerNode);
      if (funcScope) {
        const aliases = this._reqAliases.get(funcScope.id) || new Set();
        aliases.add(firstParam.name);
        this._reqAliases.set(funcScope.id, aliases);

        // Also mark the parameter variable as a taint source in the TaintStore
        this.taintStore.markTainted(funcScope.id, firstParam.name, {
          sourceType: "req",
          sourceLine: handlerNode.loc?.start?.line || 0,
          propagationPath: [firstParam.name],
          sanitizers: [],
          category: "http_request",
        });
      }
    }
  }

  /** Find the scope object created for a given AST node */
  _findScopeForNode(node) {
    for (const [, scope] of this.scopeTree.scopes) {
      if (scope.node === node) return scope;
    }
    return null;
  }

  /** Walk AST and mark all taint sources */
  _walkForSources(ast) {
    const self = this;

    function walk(node, parentScopeId) {
      if (!node || typeof node !== "object" || !node.type) return;

      // Track current scope
      let scopeId = parentScopeId;

      // ── MemberExpression: check for taint source access ──
      if (node.type === "MemberExpression") {
        const flatExpr = self._flattenMemberExpression(node);
        const sourceKey = self._findMatchingSourceKey(flatExpr);
        if (sourceKey) {
          const sourceInfo = TAINT_SOURCES[sourceKey] || {};
          self.taintStore.addExpressionTaint(node, {
            sourceType: sourceKey,
            sourceLine: node.loc?.start?.line || 0,
            propagationPath: [flatExpr],
            sanitizers: [],
            category: sourceInfo.category || sourceInfo.alias_for ? "http_request" : "unknown",
          }, scopeId);
        }
      }

      // ── VariableDeclarator: propagate taint from init to variable ──
      if (node.type === "VariableDeclarator" && node.id?.type === "Identifier" && node.init) {
        const taint = self._extractTaintFromExpression(node.init, scopeId);
        if (taint) {
          self.taintStore.markTainted(scopeId, node.id.name, {
            ...taint,
            propagationPath: [...(taint.propagationPath || []), node.id.name],
          });
        }
      }

      // ── AssignmentExpression: propagate taint ──
      if (node.type === "AssignmentExpression" && node.left?.type === "Identifier" && node.right) {
        const taint = self._extractTaintFromExpression(node.right, scopeId);
        if (taint) {
          self.taintStore.markTainted(scopeId, node.left.name, {
            ...taint,
            propagationPath: [...(taint.propagationPath || []), node.left.name],
          });
        }
      }

      // Recurse into children
      for (const key of Object.keys(node)) {
        if (key === "type" || key === "start" || key === "end" || key === "loc" || key === "raw") continue;
        const child = node[key];
        if (Array.isArray(child)) {
          for (const item of child) walk(item, scopeId);
        } else if (child && typeof child === "object" && child.type) {
          walk(child, scopeId);
        }
      }
    }

    walk(ast, this.scopeTree.root.id);
  }

  /** Extract taint information from an expression node */
  _extractTaintFromExpression(node, scopeId) {
    if (!node) return null;

    // Direct taint source: req.query.x
    if (node.type === "MemberExpression") {
      const exprTaint = this.taintStore.getExpressionTaint(node, scopeId);
      if (exprTaint) return exprTaint;

      const flatExpr = this._flattenMemberExpression(node);
      const sourceKey = this._findMatchingSourceKey(flatExpr);
      if (sourceKey) {
        return {
          sourceType: sourceKey,
          sourceLine: node.loc?.start?.line || 0,
          propagationPath: [flatExpr],
          sanitizers: [],
          category: (TAINT_SOURCES[sourceKey] || {}).category || "http_request",
        };
      }

      // Check if the object is a tainted variable (e.g., req.query → req is tainted)
      const objName = this._getIdentifierName(node.object);
      if (objName) {
        const objTaint = this.taintStore.getVariableTaint(scopeId, objName);
        if (objTaint) return { ...objTaint };
      }

      return null;
    }

    // Template literal with tainted expressions
    if (node.type === "TemplateLiteral") {
      for (const expr of node.expressions || []) {
        const t = this._extractTaintFromExpression(expr, scopeId);
        if (t) return t;
      }
      return null;
    }

    // Binary expression (string concat)
    if (node.type === "BinaryExpression" && node.operator === "+") {
      return this._extractTaintFromExpression(node.left, scopeId) ||
             this._extractTaintFromExpression(node.right, scopeId);
    }

    // Identifier — look up taint in store
    if (node.type === "Identifier") {
      return this.taintStore.getVariableTaint(scopeId, node.name);
    }

    // Call expression — check sanitizers and return taint
    if (node.type === "CallExpression") {
      return this._analyzeCallTaint(node, scopeId);
    }

    return null;
  }

  /** Analyze whether a function call returns tainted data */
  _analyzeCallTaint(node, scopeId) {
    const { SANITIZERS } = require("./sanitizers");
    const calleeName = this._getCalleeName(node);

    // Check if it's a known sanitizer
    if (calleeName && SANITIZERS[calleeName]) {
      const san = SANITIZERS[calleeName];
      if (san.strength === "strong") return null; // Taint removed
      // Weak sanitizer — preserve taint with metadata
      const argTaint = node.arguments?.length > 0
        ? this._extractTaintFromExpression(node.arguments[0], scopeId)
        : null;
      if (argTaint) {
        return {
          ...argTaint,
          sanitizers: [...(argTaint.sanitizers || []), { name: calleeName, strength: san.strength }],
        };
      }
      return null;
    }

    // Check if any argument is tainted (conservative: assume function might return input)
    for (const arg of node.arguments || []) {
      const t = this._extractTaintFromExpression(arg, scopeId);
      if (t) return t;
    }

    return null;
  }

  // ─── Utility methods ────────────────────────────────────────────────

  _flattenMemberExpression(node) {
    if (!node) return "";
    if (node.type === "Identifier") return node.name;
    if (node.type === "MemberExpression") {
      const obj = this._flattenMemberExpression(node.object);
      const prop = node.computed
        ? `[${node.property?.raw || node.property?.name || "?"}]`
        : (node.property?.name || "?");
      return `${obj}.${prop}`;
    }
    if (node.type === "CallExpression") {
      return `${this._getCalleeName(node)}(...)`;
    }
    return "?";
  }

  _findMatchingSourceKey(exprStr) {
    if (!exprStr) return null;
    for (const key of Object.keys(TAINT_SOURCES)) {
      if (exprStr === key || exprStr.startsWith(key + ".")) {
        return key;
      }
    }
    // Check req aliases
    const parts = exprStr.split(".");
    if (parts.length >= 2) {
      const firstPart = parts[0];
      // Check if this variable name is a req alias in any scope
      for (const [, aliases] of this._reqAliases) {
        if (aliases.has(firstPart)) {
          const rest = parts.slice(1).join(".");
          const sourceKey = `req.${rest}`;
          if (TAINT_SOURCES[sourceKey]) return sourceKey;
        }
      }
    }
    return null;
  }

  _getIdentifierName(node) {
    if (!node) return null;
    if (node.type === "Identifier") return node.name;
    if (node.type === "MemberExpression") return this._getIdentifierName(node.object);
    return null;
  }

  _getCalleeName(node) {
    if (!node) return null;
    if (node.type === "Identifier") return node.name;
    if (node.type === "MemberExpression") {
      const obj = this._getIdentifierName(node.object);
      const prop = node.property?.name;
      if (obj && prop) return `${obj}.${prop}`;
      if (prop) return prop;
    }
    return null;
  }
}

module.exports = { TAINT_SOURCES, EXPRESS_ROUTE_PATTERNS, SourceDetector };