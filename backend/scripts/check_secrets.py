#!/usr/bin/env python3
"""
CodeGuard AI - Secret Detection Script
Scans source files for hardcoded secrets, API keys, passwords, and tokens.
"""

import os
import re
import sys

# Patterns that indicate hardcoded secrets
SECRET_PATTERNS = [
    # API keys (common formats)
    (r'(?:api[_-]?key|apikey)\s*[=:]\s*["\']?[a-zA-Z0-9]{20,}["\']?', "Hardcoded API key"),
    # AWS keys
    (r'AKIA[0-9A-Z]{16}', "AWS Access Key ID"),
    (r'(?:aws[_-]?secret[_-]?access[_-]?key)\s*[=:]\s*["\'][a-zA-Z0-9/+=]{40}["\']', "AWS Secret Access Key"),
    # Private keys
    (r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----', "Private key in source"),
    # Generic secret patterns
    (r'(?:secret|password|passwd|token|auth)\s*[=:]\s*["\'][^"\']{8,}["\']', "Hardcoded secret/password"),
    # Database connection strings
    (r'(?:postgres|mysql|mongodb|redis)://[^\s"\']+:([^\s"\']+)@[^\s"\']+', "Database password in connection string"),
    # Bearer tokens
    (r'Bearer\s+[a-zA-Z0-9\-._~+/]+=*', "Hardcoded Bearer token"),
    # JWT-like tokens
    (r'eyJ[a-zA-Z0-9\-._+/]+=*\.eyJ[a-zA-Z0-9\-._+/]+=*\.[a-zA-Z0-9\-._+/]+=*', "Hardcoded JWT token"),
]

# Files/directories to skip
SKIP_DIRS = {'.git', '.venv', 'venv', '__pycache__', 'node_modules', '.mypy_cache', '.pytest_cache', 'alembic'}
SKIP_EXTENSIONS = {'.pyc', '.pyo', '.exe', '.bin', '.so', '.dylib', '.png', '.jpg', '.gif', '.ico', '.woff', '.woff2', '.ttf', '.eot'}
SKIP_FILES = {'demo_scan_results.py', 'hardcoded_credentials.py', 'sql_injection.py'}


def scan_file(filepath: str) -> list[tuple[int, str, str]]:
    """Scan a single file for secrets. Returns list of (line_num, pattern_name, line_content)."""
    findings = []

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                # Skip lines that are clearly test fixtures or config defaults
                stripped = line.strip()
                if stripped.startswith('#') or stripped.startswith('//'):
                    continue
                if any(kw in stripped.lower() for kw in ['example', 'placeholder', 'changeme', 'your_', 'xxx', 'test_', 'fake']):
                    continue
                if 'settings.' in stripped or 'os.environ' in stripped or 'os.getenv' in stripped:
                    continue
                if 'env(' in stripped or 'getenv(' in stripped or 'environ[' in stripped:
                    continue

                for pattern, description in SECRET_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        findings.append((line_num, description, stripped[:120]))
                        break  # One finding per line is enough
    except (OSError, UnicodeDecodeError):
        pass

    return findings


def main():
    """Scan all source files in the app directory for secrets."""
    print("Scanning for hardcoded secrets...")
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_dir = os.path.join(root_dir, 'app')

    if not os.path.isdir(app_dir):
        print(f"Error: app directory not found at {app_dir}")
        sys.exit(1)

    total_findings = 0
    files_scanned = 0

    for dirpath, dirnames, filenames in os.walk(app_dir):
        # Skip hidden and cache directories
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith('.')]

        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext in SKIP_EXTENSIONS:
                continue

            filepath = os.path.join(dirpath, filename)
            # Skip known false positives (demo/test data)
            if filename in SKIP_FILES:
                continue
            findings = scan_file(filepath)
            files_scanned += 1

            for line_num, description, content in findings:
                rel_path = os.path.relpath(filepath, root_dir)
                print(f"  [{description}] {rel_path}:{line_num}")
                print(f"    {content}")
                total_findings += 1

    print(f"\nScanned {files_scanned} files. Found {total_findings} potential secret(s).")

    if total_findings > 0:
        print("\nREVIEW these findings and either:")
        print("  1. Move secrets to environment variables")
        print("  2. Add false positives to this script's skip list")
        return 1
    else:
        print("No hardcoded secrets detected.")
        return 0


if __name__ == "__main__":
    sys.exit(main())