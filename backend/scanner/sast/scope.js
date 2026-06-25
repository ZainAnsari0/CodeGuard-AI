/**
 * CodeGuard AI - Scope Analysis
 * Builds a scope tree mapping variable declarations to their containing scopes.
 * Required for correct taint tracking — variable taint is scope-local.
 */

class ScopeTree {
  constructor() {
    this.scopes = new Map();
    this.root = this.createScope("global", null, null);
    this._currentScope = this.root;
  }

  createScope(type, parentId, node) {
    const id = `scope_${this.scopes.size}`;
    const scope = {
      id,
      type,               // "global" | "function" | "block" | "module" | "arrow"
      parentId,
      children: [],
      variables: new Map(), // name → { kind, node, taintLabels }
      node,
    };
    this.scopes.set(id, scope);
    if (parentId !== null) {
      const parent = this.scopes.get(parentId);
      if (parent) parent.children.push(id);
    }
    return scope;
  }

  /** Look up a variable, searching up the scope chain */
  lookupVariable(scopeId, name) {
    let current = this.scopes.get(scopeId);
    while (current) {
      if (current.variables.has(name)) {
        return { scope: current, info: current.variables.get(name) };
      }
      current = current.parentId ? this.scopes.get(current.parentId) : null;
    }
    return null;
  }

  /** Add a variable to a scope */
  declareVariable(scopeId, name, kind, node) {
    const scope = this.scopes.get(scopeId);
    if (!scope) return;
    if (!scope.variables.has(name)) {
      scope.variables.set(name, { kind, node, taintLabels: [] });
    }
  }

  /** Get current scope for external consumers */
  get currentScope() {
    return this._currentScope;
  }

  set currentScope(scope) {
    this._currentScope = scope;
  }
}

/**
 * Build a scope tree from an AST.
 * Returns a ScopeTree with all variable declarations mapped.
 */
function buildScopes(ast) {
  const scopeTree = new ScopeTree();
  const { ASTTraversal } = require("./traversal");
  const traversal = new ASTTraversal(ast);

  // Stack to track scope nesting during the walk
  const scopeStack = [scopeTree.root];

  function currentScope() {
    return scopeStack[scopeStack.length - 1];
  }

  function enterScope(type, node) {
    const parent = currentScope();
    const scope = scopeTree.createScope(type, parent.id, node);
    scopeStack.push(scope);
    return scope;
  }

  function exitScope() {
    scopeStack.pop();
  }

  // ── FunctionDeclaration ──
  traversal.on("FunctionDeclaration", (node, parent) => {
    // Register function name in the enclosing (parent) scope
    if (node.id && node.id.type === "Identifier") {
      scopeTree.declareVariable(currentScope().id, node.id.name, "function", node);
    }
    // Enter function scope
    const funcScope = enterScope("function", node);
    // Register parameters
    for (const param of node.params || []) {
      if (param.type === "Identifier") {
        scopeTree.declareVariable(funcScope.id, param.name, "parameter", param);
      } else if (param.type === "AssignmentPattern" && param.left?.type === "Identifier") {
        scopeTree.declareVariable(funcScope.id, param.left.name, "parameter", param);
      }
    }
    // Walk the body inside the function scope
    // (We don't walk manually — the traversal does that; we just manage the stack)
  });

  traversal.on("FunctionExpression", (node) => {
    const funcScope = enterScope("function", node);
    if (node.id && node.id.type === "Identifier") {
      scopeTree.declareVariable(funcScope.id, node.id.name, "function", node);
    }
    for (const param of node.params || []) {
      if (param.type === "Identifier") {
        scopeTree.declareVariable(funcScope.id, param.name, "parameter", param);
      } else if (param.type === "AssignmentPattern" && param.left?.type === "Identifier") {
        scopeTree.declareVariable(funcScope.id, param.left.name, "parameter", param);
      }
    }
  });

  traversal.on("ArrowFunctionExpression", (node) => {
    const funcScope = enterScope("arrow", node);
    for (const param of node.params || []) {
      if (param.type === "Identifier") {
        scopeTree.declareVariable(funcScope.id, param.name, "parameter", param);
      } else if (param.type === "AssignmentPattern" && param.left?.type === "Identifier") {
        scopeTree.declareVariable(funcScope.id, param.left.name, "parameter", param);
      }
    }
  });

  // ── Variable declarations ──
  traversal.on("VariableDeclarator", (node, parent) => {
    if (node.id?.type === "Identifier") {
      const kind = parent?.kind || "let";
      scopeTree.declareVariable(currentScope().id, node.id.name, kind, node);
    } else if (node.id?.type === "ObjectPattern") {
      // Destructuring: const { a, b } = ...
      for (const prop of node.id.properties || []) {
        const name = prop.key?.name || prop.value?.name;
        if (name) {
          scopeTree.declareVariable(currentScope().id, name, parent?.kind || "let", node);
        }
      }
    }
  });

  // ── Class declarations ──
  traversal.on("ClassDeclaration", (node) => {
    if (node.id?.type === "Identifier") {
      scopeTree.declareVariable(currentScope().id, node.id.name, "class", node);
    }
  });

  // ── Block statements (for let/const scoping) ──
  traversal.on("BlockStatement", (node, parent) => {
    // Skip if this is the body of a function — we already entered its scope
    if (parent?.type === "FunctionDeclaration" ||
        parent?.type === "FunctionExpression" ||
        parent?.type === "ArrowFunctionExpression") {
      return;
    }
    // For standalone blocks, only create a new scope if there are let/const inside
    // (simplified: we just track them for completeness)
    enterScope("block", node);
  });

  // We need to exit scopes as we leave them.
  // Since our walker is depth-first, we need to track scope entry/exit pairs.
  // The simplest approach: override walk to manage exit.

  // ── Post-visit cleanup ──
  // We'll manage scope exits by tracking which node types created scopes.
  // After the traversal walks into a function/block body, we need to pop the scope.
  // This is tricky with a simple visitor pattern. Let's use a wrapper.

  // Actually, let's restructure: use a custom walk that pushes/pops scopes.
  // The traversal's walk method is recursive, so we need to integrate scope management.

  // Simpler approach: track scope depth and pop after visiting function bodies.
  // We'll do this by listening for the *end* of function/block nodes.

  // Alternative: build scopes in a single pass with manual recursion.
  // Let's do that instead for reliability.

  return _buildScopesManual(ast, scopeTree);
}

/**
 * Manual scope-building walk that correctly enters/exits scopes.
 */
function _buildScopesManual(ast, scopeTree) {
  const scopeStack = [scopeTree.root];

  function currentScope() {
    return scopeStack[scopeStack.length - 1];
  }

  function pushScope(type, node) {
    const scope = scopeTree.createScope(type, currentScope().id, node);
    scopeStack.push(scope);
    return scope;
  }

  function popScope() {
    if (scopeStack.length > 1) {
      scopeStack.pop();
    }
  }

  function walk(node, parent) {
    if (!node || typeof node !== "object" || !node.type) return;

    // ── Scope-entering nodes ──
    if (node.type === "FunctionDeclaration") {
      if (node.id?.type === "Identifier") {
        scopeTree.declareVariable(currentScope().id, node.id.name, "function", node);
      }
      const funcScope = pushScope("function", node);
      for (const param of node.params || []) {
        _declareParam(funcScope.id, param, scopeTree);
      }
      if (node.body?.type === "BlockStatement") {
        walk(node.body, node);
      }
      popScope();
      return; // body already walked
    }

    if (node.type === "FunctionExpression") {
      const funcScope = pushScope("function", node);
      if (node.id?.type === "Identifier") {
        scopeTree.declareVariable(funcScope.id, node.id.name, "function", node);
      }
      for (const param of node.params || []) {
        _declareParam(funcScope.id, param, scopeTree);
      }
      if (node.body?.type === "BlockStatement") {
        walk(node.body, node);
      } else if (node.body) {
        // Arrow function with expression body
        walk(node.body, node);
      }
      popScope();
      return;
    }

    if (node.type === "ArrowFunctionExpression") {
      const funcScope = pushScope("arrow", node);
      for (const param of node.params || []) {
        _declareParam(funcScope.id, param, scopeTree);
      }
      if (node.body) {
        walk(node.body, node);
      }
      popScope();
      return;
    }

    // ── Variable declarations ──
    if (node.type === "VariableDeclarator") {
      if (node.id?.type === "Identifier") {
        const kind = parent?.kind || "let";
        scopeTree.declareVariable(currentScope().id, node.id.name, kind, node);
      } else if (node.id?.type === "ObjectPattern") {
        for (const prop of node.id.properties || []) {
          const name = prop.key?.name || prop.value?.name;
          if (name) {
            scopeTree.declareVariable(currentScope().id, name, parent?.kind || "let", node);
          }
        }
      }
      if (node.init) walk(node.init, node);
      return;
    }

    if (node.type === "VariableDeclaration") {
      for (const decl of node.declarations || []) {
        walk(decl, node);
      }
      return;
    }

    if (node.type === "ClassDeclaration") {
      if (node.id?.type === "Identifier") {
        scopeTree.declareVariable(currentScope().id, node.id.name, "class", node);
      }
      // Walk class body
      if (node.body) walk(node.body, node);
      return;
    }

    // ── Recurse into all child properties ──
    for (const key of Object.keys(node)) {
      if (key === "type" || key === "start" || key === "end" || key === "loc" || key === "raw") continue;
      const child = node[key];
      if (Array.isArray(child)) {
        for (const item of child) {
          if (item && typeof item === "object" && item.type) {
            walk(item, node);
          }
        }
      } else if (child && typeof child === "object" && child.type) {
        walk(child, node);
      }
    }
  }

  walk(ast, null);
  return scopeTree;
}

function _declareParam(scopeId, param, scopeTree) {
  if (param.type === "Identifier") {
    scopeTree.declareVariable(scopeId, param.name, "parameter", param);
  } else if (param.type === "AssignmentPattern" && param.left?.type === "Identifier") {
    scopeTree.declareVariable(scopeId, param.left.name, "parameter", param);
  } else if (param.type === "ObjectPattern") {
    for (const prop of param.properties || []) {
      const name = prop.key?.name || prop.value?.name;
      if (name) {
        scopeTree.declareVariable(scopeId, name, "parameter", param);
      }
    }
  } else if (param.type === "RestElement" && param.argument?.type === "Identifier") {
    scopeTree.declareVariable(scopeId, param.argument.name, "parameter", param);
  }
}

module.exports = { ScopeTree, buildScopes };