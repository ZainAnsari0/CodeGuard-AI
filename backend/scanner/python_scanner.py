"""CodeGuard AI - Python AST Scanner
Scans Python source files for security vulnerabilities using AST analysis.
Runs inside the ephemeral scanner Docker container.
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

    def scan_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Scan a single Python file for vulnerabilities."""
        findings = []

        try:
            with open(file_path, "r", errors="replace") as f:
                source = f.read()

            tree = ast.parse(source, filename=file_path)
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
            return findings
        except Exception as e:
            logger.warning(f"Failed to scan {file_path}: {e}")
            return findings

        for node in ast.walk(tree):
            findings.extend(self._check_sql_injection(node, file_path, source))
            findings.extend(self._check_command_injection(node, file_path, source))
            findings.extend(self._check_hardcoded_secrets(node, file_path, source))
            findings.extend(self._check_eval_usage(node, file_path, source))
            findings.extend(self._check_insecure_pickle(node, file_path, source))
            findings.extend(self._check_insecure_yaml(node, file_path, source))
            findings.extend(self._check_insecure_crypto(node, file_path, source))
            findings.extend(self._check_path_traversal(node, file_path, source))

        return findings

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

        return findings

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
        secret_patterns = {
            "password": re.compile(r"(password|passwd|pwd)\s*=\s*['\"][^'\"]{3,}['\"]", re.IGNORECASE),
            "api_key": re.compile(r"(api_key|apikey|api_secret|secret_key)\s*=\s*['\"][^'\"]{8,}['\"]", re.IGNORECASE),
            "token": re.compile(r"(token|auth_token|access_token)\s*=\s*['\"][^'\"]{8,}['\"]", re.IGNORECASE),
        }

        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name_lower = target.id.lower()
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        val = node.value.value
                        for pattern_name, pattern in secret_patterns.items():
                            if pattern.search(f"{target.id} = '{val}'"):
                                line = getattr(node, "lineno", 0)
                                snippet = self._get_snippet(source, line)
                                findings.append(self._make_finding(
                                    "Hardcoded Secret", "high", "CWE-798",
                                    file_path, line, snippet,
                                    f"Hardcoded {pattern_name} detected. Use environment variables or a secrets manager.",
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
                    if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
                        if isinstance(arg.left, ast.Call):
                            if isinstance(arg.left.func, ast.Attribute) and arg.left.func.attr == "get":
                                line = getattr(node, "lineno", 0)
                                snippet = self._get_snippet(source, line)
                                findings.append(self._make_finding(
                                    "Path Traversal", "medium", "CWE-22",
                                    file_path, line, snippet,
                                    "User input concatenated in file path. Validate and sanitize path inputs.",
                                    confidence=0.6,
                                ))

        return findings


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "/code"
    scanner = PythonScanner()
    results = scanner.scan_directory(target)
    print(json.dumps({"findings": results, "total_findings": len(results)}, indent=2))