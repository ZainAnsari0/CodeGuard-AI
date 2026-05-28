"""
CodeGuard AI - Demo Scan Results
Pre-computed static scan results for the guest demo.
"""

DEMO_SCAN_RESULTS = {
    "scan_id": "demo-vulnerable-app",
    "status": "completed",
    "total_files": 2,
    "findings": [
        {
            "id": "demo-finding-1",
            "vulnerability_type": "SQL Injection",
            "severity": "critical",
            "title": "SQL Injection in user login query",
            "description": "The login function constructs SQL queries using string formatting with user-supplied input, allowing attackers to inject arbitrary SQL.",
            "analyzer_type": "sast",
            "cwe_id": "CWE-89",
            "cvss_score": "9.8",
            "file_path": "app.py",
            "line_start": 25,
            "line_end": 28,
            "code_snippet": 'query = f"SELECT * FROM users WHERE username = \'{username}\' AND password = \'{password}\'"\ncursor.execute(query)',
            "status": "new",
            "confidence": 95,
            "fix_suggestions": [
                {
                    "id": "demo-fix-1",
                    "title": "Use parameterized query",
                    "description": "Replace string formatting with parameterized queries to prevent SQL injection.",
                    "priority": 1,
                    "code_before": 'query = f"SELECT * FROM users WHERE username = \'{username}\' AND password = \'{password}\'"\ncursor.execute(query)',
                    "code_after": 'query = "SELECT * FROM users WHERE username = ? AND password = ?"\ncursor.execute(query, (username, password))',
                    "language": "python",
                }
            ],
        },
        {
            "id": "demo-finding-2",
            "vulnerability_type": "Cross-Site Scripting (XSS)",
            "severity": "high",
            "title": "Reflected XSS in search endpoint",
            "description": "User input is directly embedded into HTML responses without escaping, enabling cross-site scripting attacks.",
            "analyzer_type": "sast",
            "cwe_id": "CWE-79",
            "cvss_score": "7.5",
            "file_path": "app.py",
            "line_start": 42,
            "line_end": 44,
            "code_snippet": '@app.route("/search")\ndef search():\n    return f"<h2>Results for: {request.args.get(\'q\', \'\')}</h2>"',
            "status": "new",
            "confidence": 92,
            "fix_suggestions": [
                {
                    "id": "demo-fix-2",
                    "title": "Escape user input in HTML output",
                    "description": "Use html.escape() to sanitize user input before embedding in HTML.",
                    "priority": 1,
                    "code_before": '@app.route("/search")\ndef search():\n    return f"<h2>Results for: {request.args.get(\'q\', \'\')}</h2>"',
                    "code_after": "import html\n\n@app.route('/search')\ndef search():\n    query = html.escape(request.args.get('q', ''))\n    return f'<h2>Results for: {query}</h2>'",
                    "language": "python",
                }
            ],
        },
        {
            "id": "demo-finding-3",
            "vulnerability_type": "Hardcoded Credentials",
            "severity": "high",
            "title": "Hardcoded database password in source code",
            "description": "A database password is hardcoded in the source code, making it accessible to anyone with code access.",
            "analyzer_type": "sast",
            "cwe_id": "CWE-798",
            "cvss_score": "7.5",
            "file_path": "app.py",
            "line_start": 5,
            "line_end": 5,
            "code_snippet": 'DB_PASSWORD = "super_secret_password_123"',
            "status": "new",
            "confidence": 99,
            "fix_suggestions": [
                {
                    "id": "demo-fix-3",
                    "title": "Move credentials to environment variables",
                    "description": "Use environment variables to store sensitive credentials instead of hardcoding them.",
                    "priority": 1,
                    "code_before": 'DB_PASSWORD = "super_secret_password_123"',
                    "code_after": "import os\n\nDB_PASSWORD = os.environ.get('DB_PASSWORD')",
                    "language": "python",
                }
            ],
        },
        {
            "id": "demo-finding-4",
            "vulnerability_type": "Insecure Deserialization",
            "severity": "medium",
            "title": "Pickle deserialization of untrusted data",
            "description": "The application uses pickle.loads() on user-supplied data, which can lead to arbitrary code execution.",
            "analyzer_type": "sast",
            "cwe_id": "CWE-502",
            "cvss_score": "6.5",
            "file_path": "utils.py",
            "line_start": 15,
            "line_end": 16,
            "code_snippet": "import pickle\n\ndata = pickle.loads(request.data)",
            "status": "new",
            "confidence": 88,
            "fix_suggestions": [],
        },
        {
            "id": "demo-finding-5",
            "vulnerability_type": "Path Traversal",
            "severity": "medium",
            "title": "Potential path traversal in file download",
            "description": "User input is used to construct file paths without sanitization, potentially allowing access to arbitrary files.",
            "analyzer_type": "sast",
            "cwe_id": "CWE-22",
            "cvss_score": "5.3",
            "file_path": "utils.py",
            "line_start": 30,
            "line_end": 32,
            "code_snippet": '@app.route("/download/<filename>")\ndef download(filename):\n    return send_file(f"/uploads/{filename}")',
            "status": "new",
            "confidence": 85,
            "fix_suggestions": [
                {
                    "id": "demo-fix-5",
                    "title": "Validate and sanitize file paths",
                    "description": "Use secure_filename() to prevent path traversal attacks.",
                    "priority": 1,
                    "code_before": '@app.route("/download/<filename>")\ndef download(filename):\n    return send_file(f"/uploads/{filename}")',
                    "code_after": "from werkzeug.utils import secure_filename\n\n@app.route('/download/<filename>')\ndef download(filename):\n    safe_name = secure_filename(filename)\n    return send_file(f'/uploads/{safe_name}')",
                    "language": "python",
                }
            ],
        },
        {
            "id": "demo-finding-6",
            "vulnerability_type": "Eval Injection",
            "severity": "critical",
            "title": "Use of eval() on user input",
            "description": "The eval() function is used on user-supplied data, allowing arbitrary code execution.",
            "analyzer_type": "sast",
            "cwe_id": "CWE-94",
            "cvss_score": "9.1",
            "file_path": "app.py",
            "line_start": 55,
            "line_end": 55,
            "code_snippet": 'result = eval(request.args.get("expr", "0"))',
            "status": "new",
            "confidence": 97,
            "fix_suggestions": [
                {
                    "id": "demo-fix-6",
                    "title": "Replace eval() with safe alternative",
                    "description": "Use ast.literal_eval() for simple expressions, or a dedicated expression parser.",
                    "priority": 1,
                    "code_before": 'result = eval(request.args.get("expr", "0"))',
                    "code_after": "import ast\n\ntry:\n    result = ast.literal_eval(request.args.get('expr', '0'))\nexcept (ValueError, SyntaxError):\n    result = 'Invalid expression'",
                    "language": "python",
                }
            ],
        },
    ],
    "code_files": {
        "app.py": """from flask import Flask, request, send_file
import pickle
import os

app = Flask(__name__)

DB_PASSWORD = "super_secret_password_123"

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    user = cursor.fetchone()
    return {"success": bool(user)}

@app.route("/search")
def search():
    return f"<h2>Results for: {request.args.get('q', '')}</h2>"

@app.route("/calculate")
def calculate():
    result = eval(request.args.get("expr", "0"))
    return {"result": result}

@app.route("/data", methods=["POST"])
def receive_data():
    data = pickle.loads(request.data)
    return {"received": True}
""",
        "utils.py": """import os
from flask import send_file
from werkzeug.utils import secure_filename

@app.route("/download/<filename>")
def download(filename):
    return send_file(f"/uploads/{filename}")

@app.route("/process", methods=["POST"])
def process():
    data = pickle.loads(request.data)
    return {"status": "processed"}
""",
    },
    "summary": {
        "total_findings": 6,
        "by_severity": {
            "critical": 2,
            "high": 2,
            "medium": 2,
            "low": 0,
            "info": 0,
        },
        "by_type": {
            "SQL Injection": 1,
            "Cross-Site Scripting (XSS)": 1,
            "Hardcoded Credentials": 1,
            "Insecure Deserialization": 1,
            "Path Traversal": 1,
            "Eval Injection": 1,
        },
    },
}