/**
 * CodeGuard AI - Taint Tracking Engine
 * Forward data-flow analysis that propagates taint labels from sources
 * through variable assignments, string operations, and function calls.
 */

// ─── Taint Store ─────────────────────────────────────────────────────

class TaintStore {
  constructor(scopeTree) {
    this.scopeTree = scopeTree;
    // scopeId → variableName → TaintLabel[]
    this.variableTaints = new Map();
    // Store expression-level taints by source location (start offset)
    this.expressionTaints = new Map();
  }

  /** Mark a variable as tainted in a given scope */
  markTainted(scopeId, variableName, taintLabel) {
    if (!this.variableTaints.has(scopeId)) {
      this.variableTaints.set(scopeId, new Map());
    }
    const scopeMap = this.variableTaints.get(scopeId);
    if (!scopeMap.has(variableName)) {
      scopeMap.set(variableName, []);
    }
    scopeMap.get(variableName).push(taintLabel);
  }

  /** Check if a variable is tainted in a given scope (searches up scope chain) */
  getVariableTaint(scopeId, variableName) {
    let current = scopeId;
    while (current !== null && current !== undefined) {
      const scopeMap = this.variableTaints.get(current);
      if (scopeMap?.has(variableName)) {
        const labels = scopeMap.get(variableName);
        if (labels.length > 0) return labels[0]; // Return first taint label
      }
      // Walk up scope chain
      const scope = this.scopeTree.scopes.get(current);
      current = scope?.parentId || null;
    }
    return null;
  }

  /** Mark an AST expression as tainted (keyed by source start offset) */
  addExpressionTaint(node, taintLabel, scopeId) {
    if (node?.start !== undefined) {
      this.expressionTaints.set(`${scopeId}:${node.start}`, taintLabel);
    }
  }

  /** Check if an AST expression is tainted */
  getExpressionTaint(node, scopeId) {
    if (node?.start !== undefined) {
      return this.expressionTaints.get(`${scopeId}:${node.start}`) || null;
    }
    return null;
  }

  /** Remove taint from a variable (after strong sanitization) */
  removeTaint(scopeId, variableName) {
    const scopeMap = this.variableTaints.get(scopeId);
    if (scopeMap) {
      scopeMap.delete(variableName);
    }
  }
}

// ─── Taint Propagation ───────────────────────────────────────────────

/**
 * Run multi-pass forward taint propagation until convergence.
 * Starts from variables already marked as tainted (by SourceDetector)
 * and propagates taint through assignments and expressions.
 */
function propagateTaint(ast, taintStore, scopeTree, maxPasses = 10) {
  let changed = true;
  let pass = 0;

  while (changed && pass < maxPasses) {
    changed = false;
    pass++;

    const scopeStack = [scopeTree.root.id];

    function walk(node, scopeId) {
      if (!node || typeof node !== "object" || !node.type) return;

      let childScopeId = scopeId;

      // Track scope changes for functions
      if (node.type === "FunctionDeclaration" || node.type === "FunctionExpression" || node.type === "ArrowFunctionExpression") {
        const funcScope = _findScopeForNode(node, scopeTree);
        if (funcScope) childScopeId = funcScope.id;
      }

      // ── VariableDeclarator: propagate taint from init to variable ──
      if (node.type === "VariableDeclarator" && node.id?.type === "Identifier" && node.init) {
        const varName = node.id.name;
        // Skip if already tainted
        if (!taintStore.getVariableTaint(scopeId, varName)) {
          const initTaint = resolveTaint(node.init, taintStore, scopeTree, scopeId);
          if (initTaint) {
            taintStore.markTainted(scopeId, varName, {
              ...initTaint,
              propagationPath: [...(initTaint.propagationPath || []), varName],
            });
            changed = true;
          }
        }
      }

      // ── AssignmentExpression: propagate taint from right to left ──
      if (node.type === "AssignmentExpression" && node.left?.type === "Identifier" && node.right) {
        const varName = node.left.name;
        if (!taintStore.getVariableTaint(scopeId, varName)) {
          const rightTaint = resolveTaint(node.right, taintStore, scopeTree, scopeId);
          if (rightTaint) {
            taintStore.markTainted(scopeId, varName, {
              ...rightTaint,
              propagationPath: [...(rightTaint.propagationPath || []), varName],
            });
            changed = true;
          }
        }
      }

      // ── Destructuring: propagate taint from source to destructured vars ──
      if (node.type === "VariableDeclarator" && node.id?.type === "ObjectPattern" && node.init) {
        const initTaint = resolveTaint(node.init, taintStore, scopeTree, scopeId);
        if (initTaint) {
          for (const prop of node.id.properties || []) {
            const name = prop.key?.name || prop.value?.name;
            if (name && !taintStore.getVariableTaint(scopeId, name)) {
              taintStore.markTainted(scopeId, name, {
                ...initTaint,
                propagationPath: [...(initTaint.propagationPath || []), name],
              });
              changed = true;
            }
          }
        }
      }

      // Recurse
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

    walk(ast, scopeTree.root.id);
  }

  return taintStore;
}

/**
 * Resolve the taint status of an arbitrary expression node.
 */
function resolveTaint(node, taintStore, scopeTree, scopeId) {
  if (!node) return null;

  // Identifier — look up in taint store
  if (node.type === "Identifier") {
    return taintStore.getVariableTaint(scopeId, node.name);
  }

  // MemberExpression — check expression taint then object taint
  if (node.type === "MemberExpression") {
    const exprTaint = taintStore.getExpressionTaint(node, scopeId);
    if (exprTaint) return exprTaint;

    // Check if the object is tainted
    const objName = _getIdentifierName(node.object);
    if (objName) {
      const objTaint = taintStore.getVariableTaint(scopeId, objName);
      if (objTaint) return { ...objTaint };
    }

    // Check deeper: object.object chain
    return resolveTaint(node.object, taintStore, scopeTree, scopeId);
  }

  // Template literal — any tainted expression taints the whole thing
  if (node.type === "TemplateLiteral") {
    for (const expr of node.expressions || []) {
      const t = resolveTaint(expr, taintStore, scopeTree, scopeId);
      if (t) return t;
    }
    return null;
  }

  // Binary expression (string concat) — taint propagates
  if (node.type === "BinaryExpression" && node.operator === "+") {
    return resolveTaint(node.left, taintStore, scopeTree, scopeId) ||
           resolveTaint(node.right, taintStore, scopeTree, scopeId);
  }

  // Call expression — check sanitizers and argument taint
  if (node.type === "CallExpression") {
    return resolveCallTaint(node, taintStore, scopeTree, scopeId);
  }

  // Conditional expression — check both branches
  if (node.type === "ConditionalExpression") {
    return resolveTaint(node.consequent, taintStore, scopeTree, scopeId) ||
           resolveTaint(node.alternate, taintStore, scopeTree, scopeId);
  }

  // Logical expression (||, &&, ??)
  if (node.type === "LogicalExpression") {
    return resolveTaint(node.left, taintStore, scopeTree, scopeId) ||
           resolveTaint(node.right, taintStore, scopeTree, scopeId);
  }

  return null;
}

/**
 * Resolve taint for a function call — check sanitizers and arg propagation.
 */
function resolveCallTaint(node, taintStore, scopeTree, scopeId) {
  const { SANITIZERS } = require("./sanitizers");
  const calleeName = _getCalleeName(node);

  // Check if it's a known sanitizer
  if (calleeName && SANITIZERS[calleeName]) {
    const san = SANITIZERS[calleeName];
    if (san.strength === "strong") return null; // Taint removed

    // Weak sanitizer — preserve taint with sanitizer metadata
    const argTaint = node.arguments?.length > 0
      ? resolveTaint(node.arguments[0], taintStore, scopeTree, scopeId)
      : null;
    if (argTaint) {
      return {
        ...argTaint,
        sanitizers: [...(argTaint.sanitizers || []), { name: calleeName, strength: san.strength }],
      };
    }
    return null;
  }

  // Inter-procedural: if calling a function defined in this file,
  // check if it returns tainted data
  if (calleeName && node.callee?.type === "Identifier") {
    const funcScope = _findFunctionScope(calleeName, scopeTree);
    if (funcScope) {
      // Propagate taint from call arguments to function parameters
      const funcNode = funcScope.node;
      if (funcNode?.params && node.arguments) {
        for (let i = 0; i < funcNode.params.length && i < node.arguments.length; i++) {
          const paramName = funcNode.params[i].type === "Identifier"
            ? funcNode.params[i].name
            : funcNode.params[i].left?.name;
          if (paramName) {
            const argTaint = resolveTaint(node.arguments[i], taintStore, scopeTree, scopeId);
            if (argTaint && !taintStore.getVariableTaint(funcScope.id, paramName)) {
              taintStore.markTainted(funcScope.id, paramName, {
                ...argTaint,
                propagationPath: [...(argTaint.propagationPath || []), `${calleeName}(${paramName})`],
              });
            }
          }
        }
      }

      // Check if the function returns tainted data
      const returnTaint = _analyzeFunctionReturnTaint(funcNode, taintStore, scopeTree, funcScope.id);
      if (returnTaint) return returnTaint;
    }
  }

  // Conservative: if any argument is tainted, assume the call might return it
  for (const arg of node.arguments || []) {
    const t = resolveTaint(arg, taintStore, scopeTree, scopeId);
    if (t) return t;
  }

  return null;
}

/**
 * Analyze a function body to determine if it returns tainted data.
 */
function _analyzeFunctionReturnTaint(funcNode, taintStore, scopeTree, funcScopeId) {
  // Run a mini-propagation inside the function body
  const body = funcNode.body;
  if (!body) return null;

  // Find return statements
  const returnValues = [];
  _findReturnStatements(body, returnValues);

  for (const retExpr of returnValues) {
    const taint = resolveTaint(retExpr, taintStore, scopeTree, funcScopeId);
    if (taint) return taint;
  }

  return null;
}

function _findReturnStatements(node, results) {
  if (!node || typeof node !== "object" || !node.type) return;

  if (node.type === "ReturnStatement" && node.argument) {
    results.push(node.argument);
    return; // Don't recurse into return statements
  }

  for (const key of Object.keys(node)) {
    if (key === "type" || key === "start" || key === "end" || key === "loc" || key === "raw") continue;
    const child = node[key];
    if (Array.isArray(child)) {
      for (const item of child) _findReturnStatements(item, results);
    } else if (child && typeof child === "object" && child.type) {
      _findReturnStatements(child, results);
    }
  }
}

function _findScopeForNode(node, scopeTree) {
  for (const [, scope] of scopeTree.scopes) {
    if (scope.node === node) return scope;
  }
  return null;
}

function _findFunctionScope(name, scopeTree) {
  // Search all scopes for a function with this name
  for (const [, scope] of scopeTree.scopes) {
    if (scope.variables.has(name)) {
      const info = scope.variables.get(name);
      if (info.kind === "function" && info.node) {
        // Find the scope that was created for this function
        for (const [, childScope] of scopeTree.scopes) {
          if (childScope.node === info.node) return childScope;
        }
      }
    }
  }
  return null;
}

function _getIdentifierName(node) {
  if (!node) return null;
  if (node.type === "Identifier") return node.name;
  if (node.type === "MemberExpression") return _getIdentifierName(node.object);
  return null;
}

function _getCalleeName(node) {
  if (!node?.callee) return null;
  if (node.callee.type === "Identifier") return node.callee.name;
  if (node.callee.type === "MemberExpression") {
    const obj = _getIdentifierName(node.callee.object);
    const prop = node.callee.property?.name;
    if (obj && prop) return `${obj}.${prop}`;
    if (prop) return prop;
  }
  return null;
}

module.exports = { TaintStore, propagateTaint, resolveTaint };