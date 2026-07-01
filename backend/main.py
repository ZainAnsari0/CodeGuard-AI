"""
CodeGuard AI - Backend Main Application
FastAPI server with comprehensive middleware and configuration.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import time
import structlog

# Import settings first (needed for logging configuration)
from app.core.config import settings

# Configure structured logging
from app.core.logging import setup_logging
setup_logging(debug=False, log_level_name=settings.LOG_LEVEL)
logger = structlog.get_logger()

# Import database manager and models
from app.infrastructure.database import db_manager
from sqlmodel import SQLModel
from app.api.routes import api_router
from app.core.exceptions import (
    DomainError,
    # Backward-compatible aliases
    AppException,
    NotFoundException,
    ValidationError,
    UnauthorizedException,
    ForbiddenException,
    RateLimitException,
)

# Import all models so SQLModel.metadata picks them up
from app.models.user import User  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.code_file import CodeFile  # noqa: F401
from app.models.analysis import Analysis, Finding, FixSuggestion  # noqa: F401
from app.models.share_token import ShareToken  # noqa: F401
from app.models.kb_article import KBArticle  # noqa: F401

# Create database tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown events."""
    logger.info("Starting up application...")

    # Run production readiness checks first (fail fast before touching DB)
    from app.core.startup_checks import run_startup_checks
    await run_startup_checks()

    # Initialize Redis prompt cache asynchronously
    from app.services.cache import prompt_cache
    await prompt_cache.initialize()

    # Validate JWT keys for RS256 mode
    from app.services.auth import validate_jwt_keys_on_startup
    if not validate_jwt_keys_on_startup():
        logger.warning("JWT key validation failed — RS256 may not work correctly")

    # Initialize database and ensure schema is up to date
    await db_manager.init()
    from app.infrastructure.database import engine
    from app.db.migrations import ensure_schema
    await ensure_schema(engine)

    # Auto-seed initial admin account from environment variables
    if settings.ADMIN_EMAIL and settings.ADMIN_PASSWORD:
        from app.infrastructure.database import get_session as _get_session
        from sqlalchemy import select
        from app.services.auth import get_password_hash

        async for db in _get_session():
            try:
                result = await db.execute(
                    select(User).where(User.email == settings.ADMIN_EMAIL)
                )
                existing = result.scalar_one_or_none()
                if not existing:
                    admin = User(
                        email=settings.ADMIN_EMAIL,
                        hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                        full_name="Admin",
                        role="admin",
                        is_active=True,
                        is_superuser=True,
                    )
                    db.add(admin)
                    await db.commit()
                    logger.info(f"Initial admin account created: {settings.ADMIN_EMAIL}")
                else:
                    logger.info(f"Admin account already exists: {settings.ADMIN_EMAIL}")
            except Exception as e:
                logger.error(f"Failed to seed admin account: {e}")
            break

    # Auto-seed Knowledge Base articles if table is empty
    from app.infrastructure.database import get_session as _get_session_kb
    from app.models.kb_article import KBArticle
    import uuid as _uuid

    _KB_ARTICLES = [
        {"slug": "sql-injection", "title": "SQL Injection (SQLi)", "category": "injection", "cwe_ids": "89", "owasp_category": "A03:2021 Injection", "content_markdown": """## What is SQL Injection?\n\nSQL Injection exploits vulnerabilities in an application's database layer when user input is included unsanitized in SQL statements.\n\n### Impact\n- **Data Breach**: Read sensitive data\n- **Data Manipulation**: Modify or delete data\n- **Authentication Bypass**: Log in as any user\n- **Remote Code Execution**: Execute OS commands\n\n### Prevention\n1. Use **Parameterized Queries** (primary defense)\n2. Use **Stored Procedures** (properly parameterized)\n3. **Input Validation** — whitelist acceptable input\n4. **Least Privilege** — minimal DB account permissions\n\n### References\n- [OWASP SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection)\n- [CWE-89](https://cwe.mitre.org/data/definitions/89.html)""", "vulnerable_example": "# VULNERABLE: String concatenation\ndef get_user(username):\n    query = f\"SELECT * FROM users WHERE username = '{username}'\"\n    cursor.execute(query)\n    return cursor.fetchone()", "safe_example": "# SAFE: Parameterized query\ndef get_user(username):\n    query = \"SELECT * FROM users WHERE username = %s\"\n    cursor.execute(query, (username,))\n    return cursor.fetchone()"},
        {"slug": "cross-site-scripting-xss", "title": "Cross-Site Scripting (XSS)", "category": "xss", "cwe_ids": "79", "owasp_category": "A03:2021 Injection", "content_markdown": """## What is Cross-Site Scripting (XSS)?\n\nXSS attacks occur when an attacker injects malicious scripts into content served to other users.\n\n### Types\n1. **Stored XSS** — script stored in DB, served to users\n2. **Reflected XSS** — script reflected off the server\n3. **DOM-based XSS** — vulnerability in client-side code\n\n### Impact\n- Session hijacking, account takeover\n- Page defacement, credential theft\n\n### Prevention\n1. **Output Encoding** before rendering HTML\n2. **Content Security Policy (CSP)**\n3. **Input Validation** — sanitize all user input\n4. Use frameworks that auto-escape (React, Angular)\n\n### References\n- [OWASP XSS](https://owasp.org/www-community/attacks/xss/)\n- [CWE-79](https://cwe.mitre.org/data/definitions/79.html)""", "vulnerable_example": "// VULNERABLE: innerHTML with unsanitized input\ndocument.getElementById('output').innerHTML = userInput;", "safe_example": "// SAFE: textContent instead of innerHTML\ndocument.getElementById('output').textContent = userInput;"},
        {"slug": "command-injection", "title": "OS Command Injection", "category": "injection", "cwe_ids": "78", "owasp_category": "A03:2021 Injection", "content_markdown": """## What is Command Injection?\n\nCommand injection passes unsafe user input to a system shell, allowing execution of arbitrary OS commands.\n\n### Impact\n- Full server compromise\n- Data exfiltration, lateral movement\n\n### Prevention\n1. **Avoid calling OS commands** — use language libraries\n2. **Use subprocess with list args** — never `shell=True`\n3. **Input validation** — whitelist allowed characters\n\n### References\n- [OWASP Command Injection](https://owasp.org/www-community/attacks/Command_Injection)\n- [CWE-78](https://cwe.mitre.org/data/definitions/78.html)""", "vulnerable_example": "# VULNERABLE: os.system with user input\nimport os\nos.system(f\"ping -c 4 {host}\")  # attacker: 127.0.0.1; cat /etc/passwd", "safe_example": "# SAFE: subprocess list args (no shell)\nimport subprocess\nsubprocess.run([\"ping\", \"-c\", \"4\", host], check=True)"},
        {"slug": "broken-authentication", "title": "Broken Authentication", "category": "auth", "cwe_ids": "287,306", "owasp_category": "A07:2021 Auth Failures", "content_markdown": """## What is Broken Authentication?\n\nBroken authentication occurs when authentication and session management are implemented incorrectly.\n\n### Common Vulnerabilities\n- Weak passwords, no account lockout\n- Insecure session management\n- Credentials stored in plain text\n- Missing multi-factor authentication\n\n### Prevention\n1. **Implement MFA**\n2. **Account lockout** after 5 failed attempts\n3. **Secure session cookies** — HTTPOnly, Secure, SameSite\n4. **Use bcrypt/argon2** for password hashing\n\n### References\n- [OWASP Auth Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)\n- [CWE-287](https://cwe.mitre.org/data/definitions/287.html)""", "vulnerable_example": "# VULNERABLE: Plain text passwords\ndef register(username, password):\n    db.execute('INSERT INTO users VALUES (?, ?)', (username, password))", "safe_example": "# SAFE: bcrypt hashing\nfrom passlib.context import CryptContext\npwd_context = CryptContext(schemes=['bcrypt'])\nhashed = pwd_context.hash(password)"},
        {"slug": "hardcoded-credentials", "title": "Hardcoded Credentials & Secrets", "category": "auth", "cwe_ids": "798,259", "owasp_category": "A07:2021 Auth Failures", "content_markdown": """## What are Hardcoded Credentials?\n\nHardcoded credentials are passwords, API keys, or secrets embedded directly in source code.\n\n### Impact\n- Unauthorized access to services\n- Cannot rotate credentials without code changes\n\n### Prevention\n1. **Use environment variables** — store secrets in `.env` (gitignored)\n2. **Use secret managers** — AWS Secrets Manager, HashiCorp Vault\n3. **Git hooks** — detect secrets before commit\n\n### References\n- [CWE-798](https://cwe.mitre.org/data/definitions/798.html)""", "vulnerable_example": "# VULNERABLE: Hardcoded secrets\nAPI_KEY = \"sk-abc123secretkey456\"\nDATABASE_URL = \"postgresql://admin:password123@db.example.com/mydb\"", "safe_example": "# SAFE: Environment variables\nimport os\nAPI_KEY = os.environ.get('API_KEY')\nDATABASE_URL = os.environ.get('DATABASE_URL')"},
        {"slug": "insecure-deserialization", "title": "Insecure Deserialization", "category": "injection", "cwe_ids": "502", "owasp_category": "A08:2021 Integrity", "content_markdown": """## What is Insecure Deserialization?\n\nInsecure deserialization occurs when untrusted data abuses application logic. Python's `pickle` is especially dangerous.\n\n### Impact\n- Remote Code Execution (RCE)\n- Privilege escalation, data tampering\n\n### Prevention\n1. **Never deserialize untrusted data** with `pickle`\n2. **Use safe formats** — JSON, `yaml.safe_load()`\n3. **Implement integrity checks** — HMAC signatures\n\n### References\n- [CWE-502](https://cwe.mitre.org/data/definitions/502.html)""", "vulnerable_example": "# VULNERABLE: pickle with untrusted data\nimport pickle\ndata = pickle.loads(user_input)  # RCE possible!", "safe_example": "# SAFE: Use JSON\nimport json\ndata = json.loads(user_input)\n\n# SAFE: yaml.safe_load\nimport yaml\nconfig = yaml.safe_load(user_input)"},
        {"slug": "path-traversal", "title": "Path Traversal / Directory Traversal", "category": "injection", "cwe_ids": "22", "owasp_category": "A01:2021 Broken Access Control", "content_markdown": """## What is Path Traversal?\n\nPath traversal lets attackers read arbitrary server files by manipulating paths with `../` sequences.\n\n### Impact\n- Read `/etc/passwd`, config files, credentials\n- In write scenarios, overwrite critical files\n\n### Prevention\n1. **Use `os.path.realpath()`** and verify path is within allowed directory\n2. **Whitelist** allowed file names\n3. **Chroot jails** — restrict file access\n\n### References\n- [OWASP Path Traversal](https://owasp.org/www-community/attacks/Path_Traversal)\n- [CWE-22](https://cwe.mitre.org/data/definitions/22.html)""", "vulnerable_example": "# VULNERABLE: Direct file path from user input\n@app.get('/files')\ndef get_file(filename: str):\n    with open(f'/uploads/{filename}') as f:\n        return f.read()  # ../../../etc/passwd works!", "safe_example": "# SAFE: Validate path stays within allowed dir\nimport os\nUPLOAD_DIR = '/uploads'\ndef get_file_safe(filename):\n    full_path = os.path.realpath(os.path.join(UPLOAD_DIR, filename))\n    if not full_path.startswith(os.path.realpath(UPLOAD_DIR)):\n        raise ValueError('Path traversal detected')\n    with open(full_path) as f:\n        return f.read()"},
        {"slug": "insecure-cryptography", "title": "Use of Weak Cryptographic Algorithms", "category": "crypto", "cwe_ids": "327,328", "owasp_category": "A02:2021 Crypto Failures", "content_markdown": """## Weak Cryptographic Algorithms\n\nUsing MD5, SHA1, or DES makes data vulnerable to known attacks.\n\n### Algorithms to Avoid\n- **MD5** — collision attacks since 2004\n- **SHA-1** — deprecated by NIST since 2011\n- **DES / 3DES** — insufficient key length\n\n### Recommended Alternatives\n- **Hashing**: SHA-256, bcrypt, argon2 (passwords)\n- **Encryption**: AES-256-GCM, ChaCha20-Poly1305\n\n### References\n- [OWASP Crypto Failures](https://owasp.org/Top10/A02_2021-Cryptographic_Failures/)\n- [CWE-327](https://cwe.mitre.org/data/definitions/327.html)""", "vulnerable_example": "# VULNERABLE: MD5 password hashing\nimport hashlib\nhashed = hashlib.md5(password.encode()).hexdigest()", "safe_example": "# SAFE: bcrypt for passwords\nfrom passlib.context import CryptContext\npwd_context = CryptContext(schemes=['bcrypt'])\nhashed = pwd_context.hash(password)"},
        {"slug": "security-misconfiguration", "title": "Security Misconfiguration", "category": "config", "cwe_ids": "16,209", "owasp_category": "A05:2021 Misconfiguration", "content_markdown": """## What is Security Misconfiguration?\n\nThe most common vulnerability — security settings implemented or maintained incorrectly.\n\n### Common Misconfigurations\n- Default credentials unchanged\n- Debug mode enabled in production\n- Missing security headers\n- Overly permissive CORS (`*`)\n- Verbose error messages exposing stack traces\n\n### Prevention\n1. **Disable debug mode** in production\n2. **Implement security headers** — CSP, X-Frame-Options, HSTS\n3. **Restrict CORS** to known origins\n4. **Remove default accounts**\n\n### References\n- [OWASP Misconfiguration](https://owasp.org/Top10/A05_2021-Security_Misconfiguration/)\n- [CWE-16](https://cwe.mitre.org/data/definitions/16.html)""", "vulnerable_example": "# VULNERABLE: Debug in production + wildcard CORS\napp.debug = True\nCORS_ORIGINS = ['*']", "safe_example": "# SAFE: Environment-based config\napp.debug = os.getenv('ENVIRONMENT') != 'production'\nCORS_ORIGINS = ['https://myapp.example.com']"},
        {"slug": "sensitive-data-exposure", "title": "Sensitive Data Exposure", "category": "crypto", "cwe_ids": "200,312,319", "owasp_category": "A02:2021 Crypto Failures", "content_markdown": """## What is Sensitive Data Exposure?\n\nOccurs when applications don't adequately protect sensitive information (PII, financial data, credentials).\n\n### Common Issues\n- Transmitting data over HTTP (not HTTPS)\n- Storing passwords without hashing\n- Exposing sensitive data in logs or error messages\n\n### Prevention\n1. **Encrypt data in transit** — TLS/HTTPS everywhere\n2. **Hash passwords** with bcrypt or argon2\n3. **Mask sensitive data in logs** — redact tokens, passwords\n4. **Minimize data collection**\n\n### References\n- [CWE-200](https://cwe.mitre.org/data/definitions/200.html)""", "vulnerable_example": "# VULNERABLE: Logging sensitive data\nlogger.info(f'User login: {email}, password: {password}')", "safe_example": "# SAFE: Redact sensitive fields\nlogger.info(f'User login: {email}, password: [REDACTED]')"},
        {"slug": "broken-access-control", "title": "Broken Access Control", "category": "auth", "cwe_ids": "284,639", "owasp_category": "A01:2021 Broken Access Control", "content_markdown": """## What is Broken Access Control?\n\nThe #1 OWASP risk (2021) — users acting outside their intended permissions.\n\n### Common Vulnerabilities\n- **IDOR** — accessing other users' data by changing IDs\n- Missing function-level access control\n- Force browsing to admin pages\n\n### Prevention\n1. **Deny by default** — explicit access grants only\n2. **Server-side access checks** — never rely on client-side\n3. **Validate object ownership** — user owns the resource\n4. **Role-based access control (RBAC)**\n\n### References\n- [OWASP Access Control](https://owasp.org/Top10/A01_2021-Broken_Access_Control/)\n- [CWE-284](https://cwe.mitre.org/data/definitions/284.html)""", "vulnerable_example": "# VULNERABLE: No ownership check (IDOR)\n@app.get('/api/projects/{project_id}')\ndef get_project(project_id):\n    return db.query(Project).get(project_id)  # any user!", "safe_example": "# SAFE: Server-side ownership check\n@app.get('/api/projects/{project_id}')\ndef get_project(project_id, user=Depends(get_current_user)):\n    project = db.query(Project).get(project_id)\n    if project.user_id != user.id:\n        raise HTTPException(403, 'Access denied')\n    return project"},
    ]

    async for db in _get_session_kb():
        try:
            from sqlalchemy import select as _select
            count_result = await db.execute(_select(KBArticle))
            existing_slugs = {a.slug for a in count_result.scalars().all()}
            inserted_kb = 0
            for art in _KB_ARTICLES:
                if art["slug"] not in existing_slugs:
                    db.add(KBArticle(
                        id=str(_uuid.uuid4()),
                        slug=art["slug"],
                        title=art["title"],
                        category=art["category"],
                        cwe_ids=art.get("cwe_ids"),
                        owasp_category=art.get("owasp_category"),
                        content_markdown=art["content_markdown"],
                        vulnerable_example=art.get("vulnerable_example"),
                        safe_example=art.get("safe_example"),
                        is_published=True,
                    ))
                    inserted_kb += 1
            if inserted_kb:
                await db.commit()
                logger.info(f"Seeded {inserted_kb} KB article(s)")
            else:
                logger.info("KB articles already seeded — skipping")
        except Exception as e:
            logger.error(f"Failed to seed KB articles: {e}")
        break

    # Ensure upload directory exists with proper permissions
    import os
    upload_dir = getattr(settings, "UPLOAD_DIR", "/tmp/codeguard_uploads")
    try:
        os.makedirs(upload_dir, exist_ok=True)
        os.chmod(upload_dir, 0o755)
        logger.info(f"Upload directory ready: {upload_dir}")
    except Exception as e:
        logger.warning(f"Could not set up upload directory: {e}")

    logger.info("Application startup complete")
    yield
    logger.info("Shutting down application...")

    # Close database connections (draining happens automatically)
    await db_manager.close()

    # Close AI provider clients if they have open connections
    try:
        from app.ai.fallback_chain import ai_chain
        for provider in ai_chain.providers:
            if hasattr(provider, 'client') and hasattr(provider.client, 'close'):
                await provider.client.close()
    except Exception as e:
        logger.warning(f"Error closing AI provider clients: {e}")

    # Close Redis token revocation store
    try:
        from app.services.auth import close_revocation_store
        await close_revocation_store()
    except Exception as e:
        logger.warning(f"Error closing revocation store: {e}")

    # Clean up stale temporary scan workspaces
    try:
        from app.services.temp_workspace import workspace_service
        cleaned = workspace_service.cleanup_stale_workspaces()
        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} stale workspace(s) on shutdown")
    except Exception as e:
        logger.warning(f"Error cleaning up workspaces: {e}")

    logger.info("Shutdown complete")


# Initialize FastAPI application
# Disable API docs in production
_is_production = getattr(settings, "ENVIRONMENT", "development") == "production"
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    openapi_url="/api/v1/openapi.json" if not _is_production else None,
    docs_url="/api/v1/docs" if not _is_production else None,
    redoc_url="/api/v1/redoc" if not _is_production else None,
    lifespan=lifespan
)

# Configure trusted hosts
ALLOWED_HOSTS = getattr(settings, "ALLOWED_HOSTS", ["*"])

if _is_production:
    # In production, TrustedHostMiddleware is ALWAYS active
    if "*" in ALLOWED_HOSTS:
        logger.warning(
            "ALLOWED_HOSTS contains '*' in production — "
            "this effectively disables host validation. "
            "Set ALLOWED_HOSTS to your actual domains."
        )
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=ALLOWED_HOSTS,
    )
elif ALLOWED_HOSTS != ["*"]:
    # In development, only add middleware if hosts are explicitly configured
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=ALLOWED_HOSTS,
    )

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
    expose_headers=["X-Process-Time"]
)

# Rate limiting middleware
from app.core.rate_limit import limiter
from slowapi.errors import RateLimitExceeded
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom exception handler for SlowAPI RateLimitExceeded."""
    retry_after = 60
    view_limit = getattr(request.state, "view_rate_limit", None)
    if view_limit:
        try:
            window_stats = request.app.state.limiter.limiter.get_window_stats(
                view_limit[0], *view_limit[1]
            )
            reset_in = 1 + window_stats[0]
            retry_after = max(1, int(reset_in - time.time()))
        except Exception:
            pass

    response = JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        headers={"Retry-After": str(retry_after)},
        content={
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": f"Rate limit exceeded: {exc.detail}",
                "details": {"retry_after": retry_after},
            }
        },
    )
    if hasattr(request.app.state, "limiter") and view_limit:
        response = request.app.state.limiter._inject_headers(response, view_limit)
    return response

# Prometheus metrics — restrict to internal networks in production
from prometheus_fastapi_instrumentator import Instrumentator
_metrics_endpoint = "/metrics" if not _is_production else None
_instrumentator = Instrumentator()
_instrumentator.instrument(app)
if _metrics_endpoint:
    _instrumentator.expose(app, endpoint=_metrics_endpoint)
elif _is_production:
    # In production, only expose via internal network (handled by nginx ACL)
    _instrumentator.expose(app, endpoint="/metrics", should_gzip=False)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses (dev only)."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    if not _is_production:
        response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    logger.debug(f"{request.method} {request.url.path} - {process_time:.4f}s")
    return response


# ─── New Enterprise Middleware ──────────────────────────────────────────
from app.api.middleware import (
    DomainExceptionMiddleware,
    RequestIdMiddleware,
    SecurityHeadersMiddleware,
    HTTPSEnforcementMiddleware,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(HTTPSEnforcementMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(DomainExceptionMiddleware)


# Exception handlers — standardized error response format
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions with standardized format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException):
    """Handle not found exceptions."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": {"path": request.url.path},
            }
        },
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle validation exceptions."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": {"errors": exc.errors},
            }
        },
    )


@app.exception_handler(UnauthorizedException)
async def unauthorized_exception_handler(request: Request, exc: UnauthorizedException):
    """Handle unauthorized exceptions."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": {},
            }
        },
    )


@app.exception_handler(ForbiddenException)
async def forbidden_exception_handler(request: Request, exc: ForbiddenException):
    """Handle forbidden exceptions."""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": {},
            }
        },
    )


@app.exception_handler(RateLimitException)
async def rate_limit_exception_handler(request: Request, exc: RateLimitException):
    """Handle rate limit exceptions."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        headers={"Retry-After": str(exc.retry_after)},
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": {"retry_after": exc.retry_after},
            }
        },
    )


# Include API router
app.include_router(api_router, prefix="/api/v1")


# Generic exception handler — sanitize in production to avoid leaking stack traces
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unhandled exceptions. Sanitize details in production."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    if _is_production:
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred", "details": {}}},
        )
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": str(exc), "details": {}}},
    )


@app.get("/health", include_in_schema=False)
async def health_check():
    """Health check endpoint for load balancers."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION
    }


@app.get("/ready", include_in_schema=False)
async def readiness_check():
    """Readiness probe for Kubernetes/load balancers."""
    return {
        "status": "ready",
        "service": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION
    }


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.PROJECT_VERSION,
        "docs": "/api/v1/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )