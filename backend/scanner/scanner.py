"""CodeGuard AI - Scanner Entry Point
Orchestrates Python and JavaScript AST scanning.
Runs in-process within the Celery worker — no container isolation needed
since code is only parsed, never executed.
"""

import json
import sys
import os
import subprocess
from typing import List, Dict, Any


def run_python_scanner(target_dir: str) -> List[Dict[str, Any]]:
    """Run the Python AST scanner on a directory."""
    try:
        from python_scanner import PythonScanner
        scanner = PythonScanner()
        return scanner.scan_directory(target_dir)
    except Exception as e:
        print(f"Python scanner error: {e}", file=sys.stderr)
        return []


def run_js_scanner(target_dir: str) -> List[Dict[str, Any]]:
    """Run the JavaScript AST scanner via Node.js subprocess."""
    js_scanner_path = os.path.join(os.path.dirname(__file__), "js_scanner.js")
    if not os.path.exists(js_scanner_path):
        print("JS scanner not found, skipping", file=sys.stderr)
        return []

    try:
        result = subprocess.run(
            ["node", js_scanner_path, target_dir],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            print(f"JS scanner error: {result.stderr}", file=sys.stderr)
            return []

        output = json.loads(result.stdout)
        return output.get("findings", [])
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
        print(f"JS scanner failed: {e}", file=sys.stderr)
        return []


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "/code"

    if not os.path.isdir(target):
        print(json.dumps({"error": f"Target directory not found: {target}", "findings": []}))
        sys.exit(1)

    findings = []

    python_findings = run_python_scanner(target)
    findings.extend(python_findings)

    js_findings = run_js_scanner(target)
    findings.extend(js_findings)

    output = {
        "findings": findings,
        "total_findings": len(findings),
        "scanner_version": "1.0.0",
        "target_directory": target,
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()