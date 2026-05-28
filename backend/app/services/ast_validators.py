"""
CodeGuard AI - AST Re-Validation
Validates that AI-generated fixes produce syntactically correct code
by parsing them through Python ast / Node.js acorn.
"""

import ast
import json
import logging
import subprocess
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ASTValidator:
    """Validates fixed code by parsing it through the appropriate AST."""

    def validate_fix(self, original_code: str, fixed_code: str, language: str = "python") -> Dict[str, Any]:
        """Validate that a fix is syntactically correct and meaningfully different.

        Returns:
            Dict with 'valid' (bool), 'warnings' (list), 'checks_performed' (int)
        """
        warnings = []
        checks_performed = 0

        # Check 1: fixed code differs from original
        if fixed_code.strip() == original_code.strip():
            warnings.append("Fixed code is identical to original code")
        checks_performed += 1

        # Check 2: fixed code is not empty
        if not fixed_code.strip():
            warnings.append("Fixed code is empty")
            return {"valid": False, "warnings": warnings, "checks_performed": checks_performed}
        checks_performed += 1

        # Check 3: syntax validation via AST parsing
        if language.lower() in ("python", "py"):
            ast_result = self._validate_python_ast(fixed_code)
            checks_performed += 1
            if not ast_result["valid"]:
                warnings.append(f"Python syntax error: {ast_result['error']}")

        elif language.lower() in ("javascript", "js", "typescript", "ts", "jsx", "tsx"):
            js_result = self._validate_js_ast(fixed_code, language)
            checks_performed += 1
            if not js_result["valid"]:
                warnings.append(f"JavaScript syntax error: {js_result['error']}")

        # Check 4: fixed code doesn't re-introduce the same vulnerability pattern
        pattern_result = self._check_vulnerability_regression(original_code, fixed_code)
        checks_performed += 1
        if pattern_result["regression"]:
            for pattern in pattern_result["patterns"]:
                warnings.append(f"Fix may re-introduce vulnerability: {pattern}")

        return {
            "valid": len(warnings) == 0,
            "warnings": warnings,
            "checks_performed": checks_performed,
        }

    def _validate_python_ast(self, code: str) -> Dict[str, Any]:
        """Parse code through Python's ast module to verify syntax."""
        try:
            ast.parse(code)
            return {"valid": True, "error": None}
        except SyntaxError as e:
            return {"valid": False, "error": f"Line {e.lineno}: {e.msg}"}

    def _validate_js_ast(self, code: str, language: str = "javascript") -> Dict[str, Any]:
        """Parse code through Node.js acorn to verify JavaScript syntax."""
        source_type = "module" if language in ("typescript", "ts", "tsx") else "script"

        # Use inline Node.js script with acorn
        js_script = """
const acorn = require("acorn");
let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => { input += chunk; });
process.stdin.on("end", () => {
    try {
        acorn.parse(input, { ecmaVersion: 2022, sourceType: process.argv[2] || "script" });
        console.log(JSON.stringify({ valid: true, error: null }));
    } catch (e) {
        console.log(JSON.stringify({ valid: false, error: e.message }));
    }
});
"""
        try:
            result = subprocess.run(
                ["node", "-e", js_script, source_type],
                input=code,
                capture_output=True,
                text=True,
                timeout=10,
            )
            output = result.stdout.strip()
            if output:
                parsed = json.loads(output)
                return {"valid": parsed.get("valid", False), "error": parsed.get("error")}
            # Node.js ran but produced no output — likely not installed or script failed
            if result.returncode != 0:
                logger.warning("Node.js not available for JS AST validation")
                return {"valid": False, "error": "Node.js not available for validation"}
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"JS AST validation unavailable: {e}")
            return {"valid": False, "error": f"Validation unavailable: {type(e).__name__}"}

        return {"valid": False, "error": "Unknown validation failure"}

    def _check_vulnerability_regression(self, original_code: str, fixed_code: str) -> Dict[str, Any]:
        """Check if the fixed code re-introduces dangerous patterns from the original."""
        patterns = []

        # Dangerous patterns that should NOT appear in the fix
        dangerous_calls = [
            ("eval(", "eval() usage"),
            ("exec(", "exec() usage"),
            ("__import__(", "__import__() usage"),
            ("pickle.loads(", "pickle.loads() usage"),
            ("yaml.load(", "yaml.load() without SafeLoader"),
            ("subprocess.call(", "subprocess.call() with potential shell=True"),
            ("innerHTML", "innerHTML assignment"),
        ]

        # Check if original had the pattern but fix still has it
        # (i.e., the fix didn't actually remove the vulnerability)
        for pattern, description in dangerous_calls:
            if pattern in original_code and pattern in fixed_code:
                # If the fix added the same pattern, it's a regression
                # But if it was in both, it might be context — only flag if
                # the pattern appears MORE times in the fix
                orig_count = original_code.count(pattern)
                fix_count = fixed_code.count(pattern)
                if fix_count >= orig_count:
                    patterns.append(description)

        return {"regression": len(patterns) > 0, "patterns": patterns}


ast_validator = ASTValidator()