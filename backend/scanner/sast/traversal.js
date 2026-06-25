/**
 * CodeGuard AI - AST Traversal Engine
 * Visitor-pattern walker that supports scope stack tracking.
 */

class ASTTraversal {
  constructor(ast) {
    this.ast = ast;
    this.visitors = {};       // nodeType → [callback, ...]
    this.scopeStack = [];     // Stack of scope objects passed to visitors
  }

  /** Register a visitor for a specific AST node type */
  on(nodeType, callback) {
    if (!this.visitors[nodeType]) this.visitors[nodeType] = [];
    this.visitors[nodeType].push(callback);
    return this; // chainable
  }

  /** Push a scope onto the stack (called externally by scope builder) */
  pushScope(scope) {
    this.scopeStack.push(scope);
  }

  /** Pop a scope from the stack */
  popScope() {
    return this.scopeStack.pop();
  }

  /** Walk the AST, calling registered visitors for each matching node type */
  walk(node, parent, parentKey, parentIndex) {
    if (!node || typeof node !== "object") return;
    if (!node.type) return;

    // Call visitors registered for this node type
    const callbacks = this.visitors[node.type];
    if (callbacks) {
      for (const cb of callbacks) {
        cb(node, parent, this.scopeStack, parentKey, parentIndex);
      }
    }

    // Recurse into child nodes
    for (const key of Object.keys(node)) {
      if (key === "type" || key === "start" || key === "end" || key === "loc") continue;
      const child = node[key];

      if (Array.isArray(child)) {
        for (let i = 0; i < child.length; i++) {
          if (child[i] && typeof child[i] === "object" && child[i].type) {
            this.walk(child[i], node, key, i);
          }
        }
      } else if (child && typeof child === "object" && child.type) {
        this.walk(child, node, key, null);
      }
    }
  }

  /** Start the walk from the root */
  run() {
    this.walk(this.ast, null, null, null);
  }
}

module.exports = { ASTTraversal };