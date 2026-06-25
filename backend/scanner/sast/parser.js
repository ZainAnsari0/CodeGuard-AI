/**
 * CodeGuard AI - SAST Parser
 * Parses JavaScript/TypeScript source into ESTree AST using Acorn.
 * Three-tier fallback: strict module → script → loose mode.
 */

const acorn = require("acorn");
let acornLoose;
try {
  acornLoose = require("acorn-loose");
} catch (e) {
  acornLoose = null;
}

/**
 * Parse source code into an ESTree-compatible AST.
 *
 * @param {string} source - Source code text
 * @param {string} filePath - File path (for error messages)
 * @returns {{ ast: object|null, parseMode: string, error: string|null }}
 */
function parseSource(source, filePath) {
  const baseOpts = {
    ecmaVersion: 2022,
    locations: true,
    allowHashBang: true,
    allowReturnOutsideFunction: true,
  };

  // Attempt 1: Strict module parse
  try {
    const ast = acorn.parse(source, { ...baseOpts, sourceType: "module" });
    return { ast, parseMode: "module", error: null };
  } catch (_) {
    // continue
  }

  // Attempt 2: Script mode
  try {
    const ast = acorn.parse(source, { ...baseOpts, sourceType: "script" });
    return { ast, parseMode: "script", error: null };
  } catch (e2) {
    // continue
  }

  // Attempt 3: Loose / error-tolerant parse
  if (acornLoose) {
    try {
      const ast = acornLoose.parse(source, {
        ecmaVersion: 2022,
        sourceType: "script",
        locations: true,
      });
      return { ast, parseMode: "loose", error: null };
    } catch (e3) {
      return { ast: null, parseMode: "failed", error: e3.message };
    }
  }

  return { ast: null, parseMode: "failed", error: "acorn-loose not available" };
}

module.exports = { parseSource };