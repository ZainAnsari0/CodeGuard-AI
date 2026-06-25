"""
CodeGuard AI - Rule-Based Provider
Deterministic fallback that uses the CWE knowledge base.
Never fails — always returns a result.
"""

import json
import logging
import re
from typing import Optional, Dict, Any, List

from app.ai.providers.base import AIProvider

logger = logging.getLogger(__name__)

CWE_KNOWLEDGE_BASE = {
    "CWE-89": {
        "name": "SQL Injection",
        "category": "Injection",
        "explanation": (
            "SQL Injection occurs when untrusted user input is concatenated directly into "
            "a SQL query string. An attacker can manipulate the input to modify the intended "
            "SQL command, potentially reading, modifying, or deleting data from the database."
        ),
        "impact": (
            "An attacker can: read sensitive data from the database, modify or delete records, "
            "bypass authentication, and in some cases execute operating system commands on the "
            "database server."
        ),
        "fix_approach": (
            "Use parameterized queries (prepared statements) instead of string concatenation. "
            "For Python with SQLAlchemy, use the ORM or text() with bound parameters. "
            "For raw SQL, always pass parameters separately from the query string."
        ),
        "fix_examples": {
            "python": {
                "vulnerable": 'query = f"SELECT * FROM users WHERE email = \'{email}\'"',
                "secure": 'result = db.execute(text("SELECT * FROM users WHERE email = :email"), {"email": email})',
            },
            "javascript": {
                "vulnerable": 'const query = `SELECT * FROM users WHERE username = \'${username}\'`',
                "secure": 'db.get("SELECT * FROM users WHERE username = ?", [username], callback)',
            },
        },
        "references": [
            "https://owasp.org/www-community/attacks/SQL_Injection",
            "https://cwe.mitre.org/data/definitions/89.html",
        ],
    },
    "CWE-798": {
        "name": "Use of Hard-coded Credentials",
        "category": "Authentication",
        "explanation": (
            "Hardcoded secrets (API keys, passwords, tokens) embedded in source code are "
            "accessible to anyone with access to the code repository. This includes developers, "
            "CI/CD systems, and potentially attackers if the repository is public or compromised."
        ),
        "impact": (
            "An attacker who discovers hardcoded secrets can impersonate the application, "
            "access restricted resources, and bypass authentication mechanisms. Secrets in "
            "version control history remain even after removal."
        ),
        "fix_approach": (
            "Store secrets in environment variables or a secrets manager (e.g., AWS Secrets "
            "Manager, HashiCorp Vault). Use .env files for local development (never committed "
            "to version control). Always use os.environ.get() with sensible defaults only for "
            "non-sensitive configuration."
        ),
        "fix_examples": {
            "python": {
                "vulnerable": 'SECRET_KEY: str = "sk-default-change-me"',
                "secure": 'SECRET_KEY: str = os.environ.get("SECRET_KEY", os.urandom(32).hex())',
            },
            "javascript": {
                "vulnerable": 'const API_KEY = "abc123def456";',
                "secure": 'const API_KEY = process.env.API_KEY;',
            },
        },
        "references": [
            "https://owasp.org/www-community/vulnerabilities/Use_of_hard-coded_cryptographic_key",
            "https://cwe.mitre.org/data/definitions/798.html",
        ],
    },
    "CWE-79": {
        "name": "Cross-Site Scripting (XSS)",
        "category": "Injection",
        "explanation": (
            "Cross-Site Scripting (XSS) occurs when untrusted data is included in a web page "
            "without proper validation or escaping. The attacker can inject malicious scripts "
            "that execute in the victim's browser, potentially stealing session tokens or "
            "redirecting users to malicious sites."
        ),
        "impact": (
            "An attacker can: steal session cookies and hijack user accounts, redirect users "
            "to phishing pages, deface the application, and spread worms across user accounts."
        ),
        "fix_approach": (
            "Always escape user-supplied data before rendering in HTML. Use template engines "
            "that auto-escape by default (Jinja2, React JSX). Apply Content Security Policy "
            "(CSP) headers as a defense-in-depth measure."
        ),
        "fix_examples": {
            "python": {
                "vulnerable": 'return f"<h1>Welcome {username}</h1>"',
                "secure": 'return render_template("welcome.html", username=escape(username))',
            },
            "javascript": {
                "vulnerable": 'element.innerHTML = userInput;',
                "secure": 'element.textContent = userInput;',
            },
        },
        "references": [
            "https://owasp.org/www-community/attacks/xss/",
            "https://cwe.mitre.org/data/definitions/79.html",
        ],
    },
    "CWE-94": {
        "name": "Code Injection",
        "category": "Injection",
        "explanation": (
            "Code Injection occurs when an application uses user-supplied input in a code "
            "evaluation context (eval, exec, etc.). An attacker can execute arbitrary code "
            "within the context of the application."
        ),
        "impact": (
            "An attacker can execute arbitrary code on the server, potentially gaining full "
            "control over the application and its hosting environment."
        ),
        "fix_approach": (
            "Never use eval() or exec() with user-controlled input. Use JSON.parse() for "
            "data parsing, and use allowlisted function dispatch instead of dynamic evaluation."
        ),
        "fix_examples": {
            "python": {
                "vulnerable": 'result = eval(user_input)',
                "secure": 'result = ast.literal_eval(user_input)',
            },
            "javascript": {
                "vulnerable": 'eval(request.body.expression)',
                "secure": 'JSON.parse(request.body.data)',
            },
        },
        "references": [
            "https://owasp.org/www-community/attacks/Code_Injection",
            "https://cwe.mitre.org/data/definitions/94.html",
        ],
    },
    "CWE-78": {
        "name": "OS Command Injection",
        "category": "Injection",
        "explanation": (
            "OS Command Injection occurs when an application passes user-supplied data to a "
            "system shell command. An attacker can execute arbitrary commands on the host "
            "operating system."
        ),
        "impact": (
            "An attacker can execute arbitrary commands on the server, potentially gaining full "
            "control over the system, accessing sensitive files, or pivoting to other systems."
        ),
        "fix_approach": (
            "Never pass user input directly to shell commands. Use parameterized APIs or "
            "allowlisted inputs. If shell execution is necessary, use subprocess with "
            "shell=False and pass arguments as a list."
        ),
        "fix_examples": {
            "python": {
                "vulnerable": 'os.system(f"ping {user_input}")',
                "secure": 'subprocess.run(["ping", "-c", "1", user_input], shell=False)',
            },
            "javascript": {
                "vulnerable": 'exec(`ls ${userInput}`)',
                "secure": 'execFile("ls", ["-la", userInput])',
            },
        },
        "references": [
            "https://owasp.org/www-community/attacks/Command_Injection",
            "https://cwe.mitre.org/data/definitions/78.html",
        ],
    },
}

# Regex patterns for detecting vulnerabilities in code when no AI provider is available
_VULN_REGEX_PATTERNS = [
    {
        # SQL Injection: string concatenation, template literals, f-strings, format() in SQL
        "pattern": re.compile(
            r'(?:SELECT|INSERT|UPDATE|DELETE|DROP)\s+.*?'
            r'(?:'
            r'["\']\s*\+\s*[\w.]+\s*\+\s*["\']'           # string concatenation: ' + var + '
            r'|`[^`]*\$\{[^}]+\}[^`]*`'                     # template literal: `${var}`
            r'|f["\'][^"\']*\{[^}]+\}[^"\']*["\']'          # f-string: f"...{var}..."
            r'|\.format\s*\([^)]*\)'                         # .format()
            r'|%\([^)]+\)[sd]'                               # %-formatting: %(var)s
            r')',
            re.IGNORECASE | re.DOTALL,
        ),
        "cwe_id": "CWE-89",
        "severity": "critical",
    },
    {
        # Hardcoded Credentials
        # Matches: password = "sk-abc123", api_key = 'my-secret-key'
        # Does NOT match: password = '${password}' (template literal — dynamic value)
        # Does NOT match: password = :password (SQL named parameter)
        "pattern": re.compile(
            r'(?:password|passwd|secret|api_key|apikey|token|auth_key|db_pass)\s*[:=]\s*["\'][^"\']{4,}["\']',
            re.IGNORECASE,
        ),
        "cwe_id": "CWE-798",
        "severity": "high",
    },
    {
        # XSS: innerHTML or document.write with user-controlled data
        "pattern": re.compile(
            r'\.innerHTML\s*=\s*.*?(?:req|request|query|params|input|user|body)'
            r'|document\.write\s*\(.*?(?:req|request|query|params|input|user|body)',
            re.IGNORECASE,
        ),
        "cwe_id": "CWE-79",
        "severity": "high",
    },
    {
        # Code Injection: eval/exec with user input
        "pattern": re.compile(
            r'\b(?:eval|exec)\s*\(\s*.*?(?:req|request|query|params|input|user|body)',
            re.IGNORECASE,
        ),
        "cwe_id": "CWE-94",
        "severity": "critical",
    },
    {
        # Command Injection
        "pattern": re.compile(
            r'(?:exec|execSync|spawn|execFile)\s*\(\s*.*?(?:req|request|query|params|input|user|body)',
            re.IGNORECASE,
        ),
        "cwe_id": "CWE-78",
        "severity": "critical",
    },
]


class RuleBasedProvider(AIProvider):
    """Rule-based AI provider using the CWE knowledge base. Always available.

    When called with a 'finding' kwarg (from the fix-generation pipeline), it
    returns knowledge-base details for that specific CWE.

    When called with just a 'prompt' (from the vulnerability-analysis pipeline),
    it parses the prompt for code patterns and returns a structured JSON
    response matching the vulnerability_analysis.j2 output format.
    """

    @property
    def name(self) -> str:
        return "rule-based"

    async def generate(
        self, prompt: str, system: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        finding = kwargs.get("finding", {})

        # If called with an explicit finding (fix-generation pipeline), use the
        # knowledge-base lookup path.
        if finding and finding.get("cwe_id"):
            cwe_id = finding["cwe_id"]
            knowledge = CWE_KNOWLEDGE_BASE.get(cwe_id, None)
            if knowledge:
                response_text = json.dumps({
                    "vulnerability_name": knowledge["name"],
                    "explanation": knowledge["explanation"],
                    "impact": knowledge["impact"],
                    "fix_approach": knowledge["fix_approach"],
                    "fix_examples": knowledge.get("fix_examples", {}),
                    "references": knowledge.get("references", []),
                })
            else:
                severity = finding.get("severity", "unknown")
                title = finding.get("title", "Unknown Vulnerability")
                response_text = json.dumps({
                    "vulnerability_name": title,
                    "explanation": f"A {severity} severity vulnerability was detected: {title}",
                    "impact": "Impact analysis not available for this vulnerability type.",
                    "fix_approach": "Review the identified code and apply security best practices.",
                    "fix_examples": {},
                    "references": [],
                })
            return {
                "response": response_text,
                "model": "rule-based-v1",
                "provider": self.name,
            }

        # When called from the vulnerability-analysis pipeline (no finding kwarg),
        # extract the code snippet from the prompt and detect patterns.
        code_snippet = self._extract_code_from_prompt(prompt)
        language = self._detect_language_from_prompt(prompt) or "unknown"

        if not code_snippet:
            # No code found in prompt — return empty findings
            return {
                "response": json.dumps({
                    "findings": [],
                    "summary": "No code provided for analysis.",
                    "language": language,
                    "total_findings": 0,
                }),
                "model": "rule-based-v1",
                "provider": self.name,
            }

        # Run regex-based detection on the code snippet
        findings = []
        seen = set()

        for vpat in _VULN_REGEX_PATTERNS:
            match = vpat["pattern"].search(code_snippet)
            if match and vpat["cwe_id"] not in seen:
                # Filter false positives for hardcoded credential detections
                if vpat["cwe_id"] == "CWE-798":
                    matched_text = match.group(0)
                    # Skip if the quoted value contains template expressions — it's dynamic, not hardcoded
                    if "${" in matched_text or "#{" in matched_text:
                        continue
                    # Skip if inside a SQL context (preceding code has SQL keywords)
                    context_window = 300
                    preceding = code_snippet[max(0, match.start() - context_window):match.start()]
                    if re.search(r'\b(?:SELECT|INSERT|INTO|UPDATE|DELETE|FROM|WHERE|SET|VALUES|AND|OR)\b', preceding, re.IGNORECASE):
                        continue

                seen.add(vpat["cwe_id"])
                knowledge = CWE_KNOWLEDGE_BASE.get(vpat["cwe_id"], {})

                # Find line number of the match
                line_no = code_snippet[:match.start()].count("\n") + 1

                # Extract matching line and context
                lines = code_snippet.split("\n")
                snippet_start = max(0, line_no - 2)
                snippet_end = min(len(lines), line_no + 2)
                code_snippet_matched = "\n".join(lines[snippet_start:snippet_end])

                findings.append({
                    "vulnerability_type": knowledge.get("name", vpat["cwe_id"]),
                    "severity": vpat["severity"],
                    "cwe_id": vpat["cwe_id"],
                    "file_path": None,
                    "line_number": line_no,
                    "code_snippet": code_snippet_matched,
                    "explanation": knowledge.get("explanation", f"Potential {vpat['cwe_id']} vulnerability detected."),
                    "remediation": knowledge.get("fix_approach", "Review and apply security best practices."),
                    "confidence": 0.85,
                })

        response = {
            "findings": findings,
            "summary": f"Rule-based analysis detected {len(findings)} potential vulnerabilities in {language} code.",
            "language": language,
            "total_findings": len(findings),
        }

        return {
            "response": json.dumps(response),
            "model": "rule-based-v1",
            "provider": self.name,
        }

    def _extract_code_from_prompt(self, prompt: str) -> str:
        """Extract the code snippet from the AI prompt.

        The vulnerability_analysis.j2 template wraps the code between
        ---USER_CODE_START--- and ---USER_CODE_END--- markers.
        """
        start_marker = "---USER_CODE_START---"
        end_marker = "---USER_CODE_END---"
        start_idx = prompt.find(start_marker)
        end_idx = prompt.find(end_marker)

        if start_idx != -1 and end_idx != -1:
            return prompt[start_idx + len(start_marker):end_idx].strip()

        # Fallback: return the full prompt (the regex patterns will still try to match)
        return prompt

    def _detect_language_from_prompt(self, prompt: str) -> Optional[str]:
        """Try to detect the programming language from the prompt."""
        for line in prompt.split("\n")[:5]:
            lower = line.lower().strip()
            if lower.startswith("analyze the following"):
                # e.g. "Analyze the following javascript code..."
                for lang in ["python", "javascript", "typescript", "java", "go", "rust", "c", "c++", "ruby", "php"]:
                    if lang in lower:
                        return lang
        return None

    async def chat(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> Dict[str, Any]:
        last_message = messages[-1]["content"] if messages else ""
        return await self.generate(prompt=last_message, **kwargs)

    async def check_health(self) -> Dict[str, Any]:
        return {"available": True, "error": None}