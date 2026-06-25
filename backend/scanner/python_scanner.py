"""CodeGuard AI - Python AST Scanner
Scans Python source files for security vulnerabilities using AST analysis.
Runs in-process within the Celery worker — no container isolation needed
since code is only parsed, never executed.
"""

import ast
import json
import logging
import os
import sys
import re
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class PythonScanner:
    """Scans Python source files for security vulnerabilities using AST."""

    def scan_content(self, content: str, filename: str = "code.py") -> List[Dict[str, Any]]:
        """Scan Python content directly without writing to disk."""
        findings = []

        try:
            tree = ast.parse(content, filename=filename)
        except SyntaxError as e:
            logger.warning(f"Syntax error in {filename}: {e}")
            return findings
        except Exception as e:
            logger.warning(f"Failed to parse content for {filename}: {e}")
            return findings

        for node in ast.walk(tree):
            findings.extend(self._check_sql_injection(node, filename, content))
            findings.extend(self._check_command_injection(node, filename, content))
            findings.extend(self._check_hardcoded_secrets(node, filename, content))
            findings.extend(self._check_eval_usage(node, filename, content))
            findings.extend(self._check_insecure_pickle(node, filename, content))
            findings.extend(self._check_insecure_yaml(node, filename, content))
            findings.extend(self._check_insecure_crypto(node, filename, content))
            findings.extend(self._check_path_traversal(node, filename, content))

        return findings

    def scan_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Scan a single Python file for vulnerabilities."""
        try:
            with open(file_path, "r", errors="replace") as f:
                source = f.read()
            return self.scan_content(source, file_path)
        except Exception as e:
            logger.warning(f"Failed to scan {file_path}: {e}")
            return []

    def scan_directory(self, directory: str) -> List[Dict[str, Any]]:
        """Recursively scan a directory for Python files."""
        findings = []

        for root, dirs, files in os.walk(directory):
            for filename in files:
                if filename.endswith(".py"):
                    file_path = os.path.join(root, filename)
                    findings.extend(self.scan_file(file_path))

        return findings

    def _get_line(self, node: ast.AST, source: str) -> int:
        return getattr(node, "lineno", 0)

    def _get_snippet(self, source: str, line: int, context: int = 2) -> str:
        lines = source.split("\n")
        start = max(0, line - context - 1)
        end = min(len(lines), line + context)
        return "\n".join(lines[start:end])

    def _make_finding(self, vuln_type: str, severity: str, cwe_id: str,
                      file_path: str, line: int, code: str, desc: str,
                      confidence: float = 0.8) -> Dict[str, Any]:
        return {
            "vulnerability_type": vuln_type,
            "severity": severity,
            "cwe_id": cwe_id,
            "file_path": file_path,
            "line_number": line,
            "code_snippet": code,
            "description": desc,
            "confidence": confidence,
            "analyzer_type": "python_ast",
        }

    def _check_sql_injection(self, node: ast.AST, file_path: str, source: str) -> List[Dict]:
        """Detect string formatting in SQL execution calls (CWE-89)."""
        findings = []
        sql_functions = {"execute", "executemany", "raw", "raw_query"}
        sql_keywords = {"SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER"}

        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr in sql_functions:
                for arg in node.args:
                    if isinstance(arg, (ast.JoinedStr, ast.BinOp)):
                        line = self._get_line(node, source)
                        snippet = self._get_snippet(source, line)
                        findings.append(self._make_finding(
                            "SQL Injection", "high", "CWE-89",
                            file_path, line, snippet,
                            "String formatting detected in SQL query. Use parameterized queries instead.",
                            confidence=0.85,
                        ))

            if isinstance(func, ast.Name) and func.id in sql_functions:
                for arg in node.args:
                    if isinstance(arg, (ast.JoinedStr, ast.BinOp)):
                        line = self._get_line(node, source)
                        snippet = self._get_snippet(source, line)
                        findings.append(self._make_finding(
                            "SQL Injection", "high", "CWE-89",
                            file_path, line, snippet,
                            "String formatting detected in SQL query execution.",
                            confidence=0.75,
                        ))

        # Check for string concatenation / f-strings creating SQL queries.
        # Walks nested BinOp(+) chains and JoinedStr nodes so multi-part
        # concatenations like "SELECT ..." + str(x) + "..." are caught.
        if isinstance(node, ast.Assign):
            literals, has_dynamic = self._collect_sql_string_parts(node.value)
            if has_dynamic:
                combined = " ".join(literals).upper()
                if any(keyword in combined for keyword in sql_keywords):
                    line = self._get_line(node, source)
                    snippet = self._get_snippet(source, line)
                    findings.append(self._make_finding(
                        "SQL Injection", "high", "CWE-89",
                        file_path, line, snippet,
                        "Dynamic value interpolated/concatenated into SQL query. Use parameterized queries instead.",
                        confidence=0.80,
                    ))

        return findings

    def _collect_sql_string_parts(self, node: ast.AST):
        """Collect literal string fragments from a + BinOp chain or an f-string,
        and report whether any dynamic (non-constant) value is mixed in.

        Returns (list_of_string_literals, has_dynamic_part).
        """
        literals: List[str] = []
        has_dynamic = False

        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left_lits, left_dyn = self._collect_sql_string_parts(node.left)
            right_lits, right_dyn = self._collect_sql_string_parts(node.right)
            return left_lits + right_lits, (left_dyn or right_dyn)

        if isinstance(node, ast.JoinedStr):
            for value in node.values:
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    literals.append(value.value)
                elif isinstance(value, ast.FormattedValue):
                    has_dynamic = True
            return literals, has_dynamic

        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return [node.value], False

        # Name, Call, Attribute, Subscript, etc. = dynamic, untrusted input
        return [], True

    def _check_command_injection(self, node: ast.AST, file_path: str, source: str) -> List[Dict]:
        """Detect os.system/subprocess with string formatting (CWE-78)."""
        findings = []
        dangerous_funcs = {"system", "popen", "call", "run", "check_output", "check_call"}

        if isinstance(node, ast.Call):
            func = node.func
            is_dangerous = False

            if isinstance(func, ast.Attribute) and func.attr in dangerous_funcs:
                is_dangerous = True
            elif isinstance(func, ast.Name) and func.id in dangerous_funcs:
                is_dangerous = True

            if is_dangerous:
                for arg in node.args:
                    if isinstance(arg, (ast.JoinedStr, ast.BinOp)):
                        line = getattr(node, "lineno", 0)
                        snippet = self._get_snippet(source, line)
                        findings.append(self._make_finding(
                            "Command Injection", "critical", "CWE-78",
                            file_path, line, snippet,
                            "String formatting in shell command. Use subprocess with shell=False and list arguments.",
                            confidence=0.9,
                        ))

            if isinstance(func, ast.Attribute) and func.attr == "call":
                for kw in node.keywords:
                    if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        line = getattr(node, "lineno", 0)
                        snippet = self._get_snippet(source, line)
                        findings.append(self._make_finding(
                            "Command Injection", "high", "CWE-78",
                            file_path, line, snippet,
                            "subprocess.call with shell=True is vulnerable to command injection.",
                            confidence=0.9,
                        ))

        return findings

    def _check_hardcoded_secrets(self, node: ast.AST, file_path: str, source: str) -> List[Dict]:
        """Detect hardcoded passwords, API keys, and secrets (CWE-798)."""
        findings = []
        
        # Patterns for variable names (case-insensitive). Substring match,
        # so "private_key_secret", "db_password", "client_secret" all hit.
        secret_var_patterns = {
            "password": ["password", "passwd", "pwd"],
            "api_key": ["api_key", "apikey", "api_secret", "secret_key", "access_key",
                        "private_key", "secret", "credential", "client_secret"],
            "token": ["token", "auth_token", "access_token", "bearer_token"],
        }

        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var_name_lower = target.id.lower()
                    
                    # Check if it's a string constant value
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        val = node.value.value
                        
                        # Skip short values that are unlikely to be real secrets
                        if len(val) < 6:
                            continue

                        placeholders = ["", "none", "null", "todo", "changeme",
                                        "example", "your_key_here", "xxxxxx", "placeholder"]

                        # Report only once per assignment even if several patterns match
                        matched = False
                        # Check if variable name matches any secret pattern
                        for secret_type, patterns in secret_var_patterns.items():
                            if matched:
                                break
                            for pattern in patterns:
                                if pattern in var_name_lower:
                                    # Additional check: value should look like a secret (not placeholder)
                                    if val and val.lower() not in placeholders:
                                        matched = True
                                        line = getattr(node, "lineno", 0)
                                        snippet = self._get_snippet(source, line)
                                        findings.append(self._make_finding(
                                            "Hardcoded Secret", "high", "CWE-798",
                                            file_path, line, snippet,
                                            f"Hardcoded {secret_type} detected. Use environment variables or a secrets manager.",
                                            confidence=0.8,
                                        ))
                                    break

        return findings

    def _check_eval_usage(self, node: ast.AST, file_path: str, source: str) -> List[Dict]:
        """Detect eval() and exec() usage (CWE-94)."""
        findings = []

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
                line = getattr(node, "lineno", 0)
                snippet = self._get_snippet(source, line)
                findings.append(self._make_finding(
                    "Dangerous Function", "critical", "CWE-94",
                    file_path, line, snippet,
                    f"Use of {node.func.id}() is dangerous and can lead to code injection.",
                    confidence=0.95,
                ))

        return findings

    def _check_insecure_pickle(self, node: ast.AST, file_path: str, source: str) -> List[Dict]:
        """Detect pickle.loads on untrusted data (CWE-502)."""
        findings = []

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr == "loads":
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "pickle":
                    line = getattr(node, "lineno", 0)
                    snippet = self._get_snippet(source, line)
                    findings.append(self._make_finding(
                        "Insecure Deserialization", "high", "CWE-502",
                        file_path, line, snippet,
                        "pickle.loads() on untrusted data can lead to arbitrary code execution.",
                        confidence=0.85,
                    ))

        return findings

    def _check_insecure_yaml(self, node: ast.AST, file_path: str, source: str) -> List[Dict]:
        """Detect yaml.load without SafeLoader (CWE-502)."""
        findings = []

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr == "load":
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "yaml":
                    has_safe_loader = False
                    for kw in node.keywords:
                        if kw.arg == "Loader" and isinstance(kw.value, ast.Name):
                            if "safe" in kw.value.id.lower():
                                has_safe_loader = True
                    if not has_safe_loader:
                        line = getattr(node, "lineno", 0)
                        snippet = self._get_snippet(source, line)
                        findings.append(self._make_finding(
                            "Insecure Deserialization", "medium", "CWE-502",
                            file_path, line, snippet,
                            "yaml.load() without SafeLoader can lead to arbitrary code execution. Use yaml.safe_load().",
                            confidence=0.8,
                        ))

        return findings

    def _check_insecure_crypto(self, node: ast.AST, file_path: str, source: str) -> List[Dict]:
        """Detect weak cryptographic algorithms (CWE-327)."""
        findings = []
        weak_hash_funcs = {"md5", "sha1"}

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in weak_hash_funcs:
                    line = getattr(node, "lineno", 0)
                    snippet = self._get_snippet(source, line)
                    findings.append(self._make_finding(
                        "Weak Cryptography", "medium", "CWE-327",
                        file_path, line, snippet,
                        f"Weak hash function {node.func.attr} detected. Use SHA-256 or stronger.",
                        confidence=0.85,
                    ))

        return findings

    def _check_path_traversal(self, node: ast.AST, file_path: str, source: str) -> List[Dict]:
        """Detect path traversal vulnerabilities (CWE-22)."""
        findings = []

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "open":
                for arg in node.args:
                    # Check for any string concatenation in file paths
                    if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
                        # Check if either side involves a variable (not just constants)
                        has_variable = False
                        if isinstance(arg.right, ast.Name):
                            has_variable = True
                        elif isinstance(arg.left, ast.Name):
                            has_variable = True
                        
                        if has_variable:
                            line = getattr(node, "lineno", 0)
                            snippet = self._get_snippet(source, line)
                            findings.append(self._make_finding(
                                "Path Traversal", "high", "CWE-22",
                                file_path, line, snippet,
                                "String concatenation in file path with variable. Validate and sanitize path inputs.",
                                confidence=0.75,
                            ))

        return findings


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "/code"
    scanner = PythonScanner()
    results = scanner.scan_directory(target)
    print(json.dumps({"findings": results, "total_findings": len(results)}, indent=2))