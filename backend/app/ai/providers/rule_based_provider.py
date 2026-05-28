"""
CodeGuard AI - Rule-Based Provider
Deterministic fallback that uses the CWE knowledge base.
Never fails — always returns a result.
"""

import json
import logging
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
            }
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
            }
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
            }
        },
        "references": [
            "https://owasp.org/www-community/attacks/xss/",
            "https://cwe.mitre.org/data/definitions/79.html",
        ],
    },
}


class RuleBasedProvider(AIProvider):
    """Rule-based AI provider using the CWE knowledge base. Always available."""

    @property
    def name(self) -> str:
        return "rule-based"

    async def generate(
        self, prompt: str, system: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        finding = kwargs.get("finding", {})
        if not finding:
            logger.warning("RuleBasedProvider.generate called without a 'finding' kwarg")

        cwe_id = finding.get("cwe_id", "")
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

    async def chat(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> Dict[str, Any]:
        last_message = messages[-1]["content"] if messages else ""
        return await self.generate(prompt=last_message, **kwargs)

    async def check_health(self) -> Dict[str, Any]:
        return {"available": True, "error": None}