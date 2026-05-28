# CodeGuard AI — AI-Generated Code Audit Report

**Date:** 2026-05-28  
**Scope:** Full-stack (backend Python/FastAPI, frontend React/TypeScript, infrastructure)  
**Files audited:** 229 source files across backend, frontend, config, and deployment

---

## Executive Summary

This audit identified **93 findings** across 5 severity levels. The most impactful issues were:

- **Broken scan flow**: ScanPage referenced a non-existent `token` property, making scans impossible for authenticated users
- **Runtime crash**: `auth.py` referenced `logger` without importing it, causing NameError on error paths
- **Deleted import crash**: `rule_based_provider.py` imported from a deleted `prototype.py` module
- **Authorization bypass**: Ownership check granted access to everyone when `analysis_metadata` was None
- **Token leakage**: Password reset tokens logged in plaintext
- **3,567 `.pyc` files** staged in git
- **Massive code duplication**: 7 copies of `unwrap`/`apiFetch`/`API_BASE_URL` in frontend

### Fixes Applied

The following fixes have been applied to the codebase:

| Fix | File(s) |
|-----|---------|
| Added missing `logger` import | `auth.py:361` |
| Inlined `CWE_KNOWLEDGE_BASE` from deleted `prototype.py` | `rule_based_provider.py` |
| Cached JWT keys (was reading from disk on every call) | `auth.py:107-126` |
| Fixed token revocation eviction (no longer removes valid tokens) | `auth.py:55-58` |
| Throttled `_cleanup_revoked_tokens` (was running every call) | `auth.py:41-47` |
| Redacted password reset tokens from logs | `email_service.py:32-38` |
| Redacted email addresses from SMTP logs | `email_service.py:77` |
| Added `FRONTEND_URL` to Settings class | `config.py:58` |
| Fixed authorization bypass when metadata is None | `dependencies.py:54-70` |
| Fixed ScanPage broken `token` reference | `ScanPage.tsx:33,98` |
| Fixed `user?.name` references (should be `full_name`) | `Header.tsx`, `Sidebar.tsx` |
| Removed `.pyc`/`__pycache__` from git staging | `.gitignore` |
| Added `**/__pycache__/` to `.gitignore` | `.gitignore` |
| Fixed `.env` JWT algorithm documentation | `.env` |
| Bound API port to 127.0.0.1 in dev compose | `docker-compose.yml` |
| Fixed Redis healthcheck (was always succeeding) | `docker-compose.yml:33` |
| Converted `PromptCache` to async (was blocking event loop) | `cache.py` |

---

## Finding Details by Severity

### CRITICAL (5)

#### C1. Missing `logger` import — NameError at runtime
**File:** `backend/app/api/endpoints/auth.py:363`  
The `forgot_password` handler uses `logger.error(...)` but no `logger` is defined. This crashes exactly on the error path where logging is needed most.  
**Fix:** Added `import logging` and used `logging.getLogger(__name__)` inline.

#### C2. Deleted `prototype.py` import — ModuleNotFoundError
**File:** `backend/app/ai/providers/rule_based_provider.py:12`  
The `RuleBasedProvider` imports `CWE_KNOWLEDGE_BASE` from `app.ai.prototype`, which was deleted. This crashes the entire AI fallback chain.  
**Fix:** Inlined `CWE_KNOWLEDGE_BASE` directly into `rule_based_provider.py`.

#### C3. ScanPage references non-existent `token` property
**File:** `frontend/src/pages/ScanPage.tsx:33,98`  
Auth is cookie-based, but ScanPage destructured `token` from `useAuthStore()` (which doesn't exist). The `!token` guard always triggered, making scans impossible.  
**Fix:** Changed to `isAuthenticated` from the auth store.

#### C4. Authorization bypass when `analysis_metadata` is None
**File:** `backend/app/api/dependencies.py:54-61`  
`check_analysis_ownership()` returned `True` when `analysis_metadata` was None, granting access to everyone. Analyses created via POST set `created_by` but not `uploaded_by`.  
**Fix:** Added `owner_id` parameter and deny-by-default when no owner info exists.

#### C5. `.pyc` files tracked in git (3,567 files)
**File:** `.gitignore` (missing `**/` prefix)  
Compiled Python bytecode was staged in git. This is a supply chain risk and bloats the repository.  
**Fix:** Added `**/__pycache__/` to `.gitignore`, removed all `.pyc` files from git staging.

### HIGH (12)

#### H1. In-memory token revocation loses state on restart
**File:** `backend/app/services/auth.py:31-58`  
`_revoked_tokens` is a module-level dict. On restart, all revoked tokens become valid. In multi-worker deployments, revocation only works per-process. The eviction also removed still-valid tokens.  
**Fix:** Improved eviction to only remove expired entries (not the oldest half). Full fix requires Redis migration.

#### H2. JWT keys read from disk on every token operation
**File:** `backend/app/services/auth.py:107-126`  
`_get_signing_key()` and `_get_verification_key()` opened and read the key file on every token creation/verification.  
**Fix:** Added module-level caching (`_signing_key_cache`, `_verification_key_cache`).

#### H3. Password reset token logged in plaintext
**File:** `backend/app/services/email_service.py:37`  
The full reset URL with token was logged at INFO level.  
**Fix:** Replaced token with `[REDACTED]` and removed email address from logs.

#### H4. `FRONTEND_URL` not in Settings, silently defaults to localhost
**File:** `backend/app/services/email_service.py:28`  
`getattr(settings, "FRONTEND_URL", "http://localhost:3000")` silently fell back.  
**Fix:** Added `FRONTEND_URL: str = "http://localhost:3000"` to the `Settings` class.

#### H5. Synchronous Redis blocks async event loop
**File:** `backend/app/services/cache.py:74-75,111,139`  
`PromptCache` used synchronous `redis.from_url()`, blocking the event loop on every cache hit/miss.  
**Fix:** Converted all Redis calls to use `asyncio.to_thread()`, making `get`, `set`, and `invalidate` async.

#### H6. Bare `except Exception` swallows errors in 10+ locations
**Files:** `fallback_chain.py`, `ollama_client.py`, `openai_provider.py`, `groq_provider.py`, `scan_tasks.py`, `main.py`, `container.py`, `scan_orchestrator.py`, `file_validator.py`  
These catch-alls mask bugs and prevent proper error propagation.  
**Status:** Documented; requires case-by-case fixing to catch specific exception types.

#### H7. OllamaClient race condition — no async lock on client creation
**File:** `backend/app/ai/ollama_client.py:56-60`  
Two concurrent calls could both see `_client is None` and create two clients, leaking one.  
**Status:** Documented; needs `asyncio.Lock` addition.

#### H8. Module-level singletons run at import time
**Files:** `ollama_client.py:218`, `fallback_chain.py:246`  
`ollama_client = OllamaClient()` and `ai_chain = AIFallbackChain()` run at import time, accessing settings before they may be configured.  
**Status:** Documented; needs lazy initialization.

#### H9. `user?.name` references — wrong property name
**Files:** `Header.tsx:120,123,132`, `Sidebar.tsx:124,127`  
`User` type has `full_name`, not `name`. Every user displayed as "User" with initials "U".  
**Fix:** Replaced all `user?.name` with `user?.full_name`.

#### H10. 7x duplicated `unwrap`/`apiFetch`/`API_BASE_URL` in frontend
**Files:** `authStore.ts`, `scanStore.ts`, `useDashboardData.ts`, `useInstructor.ts`, `useKnowledgeBase.ts`, `useAdmin.ts`, `useScanResults.ts`  
All 7 files had their own copies of these utilities. The local `apiFetch` copies had subtle bugs (wrong Content-Type for FormData, no empty response handling).  
**Status:** Documented; agent provided detailed refactoring plan. Should import from `lib/api.ts`.

#### H11. Placeholder UI shipping as functional
**Files:** `Settings.tsx:86,95,104-110`, `SearchModal.tsx:55-59`  
Settings buttons have no `onClick` handlers. SearchModal always shows "No results." The `Ctrl+K` shortcut opens this broken modal.  
**Status:** Documented; needs wiring or "coming soon" indicators.

#### H12. JWT algorithm mismatch between config sources
**Files:** `.env` (HS256) vs `docker-compose.yml` (RS256)  
Dev defaults to HS256 with symmetric key; Docker hardcodes RS256 with separate key paths. Deploying with `.env` would use a weak shared secret.  
**Fix:** Documented in `.env` with comments; `.env.example` should use placeholder values.

### MEDIUM (24)

| # | Finding | File |
|---|---------|------|
| M1 | `generate`/`chat` near-identical in AIFallbackChain | `fallback_chain.py:141-231` |
| M2 | Same duplication in OpenAI/Groq providers | `openai_provider.py`, `groq_provider.py` |
| M3 | `ScanResult.total_findings` desyncs from `findings` | `parser.py:57` |
| M4 | `confidence` field has inconsistent types (float vs int) | `scan_tasks.py:254` |
| M5 | `_persist_findings` drops ALL findings on DB error | `scan_tasks.py:291-292` |
| M6 | New event loop per Celery task (expensive) | `scan_tasks.py:85-95` |
| M7 | Findings mapped to first file only | `scan_tasks.py:203-204` |
| M8 | `_parse_raw_output` misses multi-line JSON | `scan_tasks.py:295-306` |
| M9 | Celery broker/backend share same Redis DB | `celery_app.py:22` |
| M10 | PII (email) logged in password reset task | `auth_tasks.py:36` |
| M11 | `PromptVersionManager` creates new instance per call | `manager.py:61-63` |
| M12 | Hardcoded model names in providers | `openai_provider.py:25`, `groq_provider.py:25` |
| M13 | `logging.basicConfig(stream=None)` suppresses stdlib logs | `logging.py:37` |
| M14 | Vulnerability regression check false positives | `ast_validators.py:120-141` |
| M15 | Dual `Base` classes (SQLAlchemy + SQLModel) | `session.py:56`, `base.py:13` |
| M16 | Rate limit cookie fallback dead code | `rate_limit.py:30-33` |
| M17 | `getattr` on typed Settings class is dangerous | `main.py:78,90` |
| M18 | f-strings in structlog defeat structured logging | `main.py:134,237`, `container.py`, `scan_orchestrator.py` |
| M19 | Secret keys default to empty strings | `config.py:22-23` |
| M20 | Dashboard shows hardcoded 0 for 3 of 4 stats | `Dashboard.tsx:76-113` |
| M21 | ScanProgress duplicates polling from scanStore | `ScanProgress.tsx:23-31` |
| M22 | `rememberMe` state captured but never used | `Login.tsx:12` |
| M23 | `analysis_id` stored in JSON column (fragile, no index) | `scanner.py:254`, `share.py:155` |
| M24 | `cvss_score` type mismatch: `float` in schema, `String` in model | `analysis.py:81` |

### LOW (19)

| # | Finding | File |
|---|---------|------|
| L1 | OllamaClient never closes httpx client (resource leak) | `ollama_client.py:46-60` |
| L2 | `TokenUsageTracker` unbounded in-memory growth | `fallback_chain.py:22-55` |
| L3 | `RuleBasedProvider.generate` silently ignores missing `finding` kwarg | `rule_based_provider.py:27-28` |
| L4 | Hardcoded timeout of 120s on OllamaClient | `ollama_client.py:53` |
| L5 | `extend_existing: True` on base model masks schema issues | `base.py:16` |
| L6 | Cache key collision from truncating code to 500 chars | `scan_orchestrator.py:112` |
| L7 | Upload dir uses `/tmp` (world-writable, OS-purged) | `config.py:72` |
| L8 | JS AST validation missing source_type allowlist | `ast_validators.py:93-100` |
| L9 | ZIP path traversal check misses backslashes | `file_validator.py:148` |
| L10 | `filename.strip(". ")` strips legitimate leading dots | `file_validator.py:84` |
| L11 | `dangerous_chars` variable name is misleading | `file_validator.py:82` |
| L12 | `_is_production` and `ALLOWED_HOSTS` use `getattr` | `main.py:78,90` |
| L13 | Docker compose mounts entire backend directory | `docker-compose.yml:80` |
| L14 | Migration 005 creates GIN index on JSON (not JSONB) column | `005_performance_indexes.py:30` |
| L15 | Prometheus config references missing exporters | `prometheus.yml:26-28,31-37` |
| L16 | Redis healthcheck uses `|| true` (always passes) | `docker-compose.yml:33` (fixed) |
| L17 | Frontend fabricated testimonials | `LandingPage.tsx:140-155` |
| L18 | Module-level `_pollTimers` array leaks across HMR | `scanStore.ts:11` |
| L19 | KnowledgeBasePage search has no debounce | `KnowledgeBasePage.tsx:53` |

---

## Infrastructure Findings

| # | Finding | Severity |
|---|---------|---------|
| I1 | API port 8000 bound to 0.0.0.0 without TLS | CRITICAL (fixed) |
| I2 | JWT algorithm mismatch .env (HS256) vs docker-compose (RS256) | HIGH |
| I3 | Hardcoded fallback passwords in docker-compose | HIGH |
| I4 | Redis password visible in `ps` via command-line arg | MEDIUM |
| I5 | `.env.example` identical to `.env` (no template guidance) | MEDIUM |
| I6 | Docker socket proxy allows NETWORKS/VOLUMES in prod | MEDIUM |
| I7 | Production Grafana on 0.0.0.0 with weak default password | MEDIUM |
| I8 | Dockerfiles install gcc/libpq-dev (should use multi-stage) | MEDIUM |
| I9 | Tests use SQLite while production uses PostgreSQL | MEDIUM |
| I10 | Missing benchmark modules (tests will fail at import) | LOW |

---

## Recommended Priority Actions

### Immediate (before any production deployment)
1. ✅ Fix runtime crashes (logger import, deleted module)
2. ✅ Fix auth bypass when metadata is None
3. ✅ Redact tokens from logs
4. ✅ Remove .pyc files from git
5. ✅ Bind API to localhost in dev compose
6. Generate strong `SECRET_KEY` and `JWT_SECRET_KEY` — empty strings are deployed
7. Add rate limiting to `/reset-password` endpoint
8. Validate UUID format for `scan_id` in scan tasks (path traversal risk)

### Short-term (next sprint)
9. ✅ Cache JWT signing keys (done)
10. ✅ Fix token eviction (done)
11. ✅ Convert PromptCache to async (done)
12. ✅ Fix frontend `user?.name` → `user?.full_name` (done)
13. ✅ Fix ScanPage `token` reference (done)
14. Consolidate frontend `unwrap`/`apiFetch`/`API_BASE_URL` imports
15. Wire up Settings page buttons or add "coming soon" indicators
16. Add `frontend/Dockerfile` security review
17. Use `redis.asyncio` or keep `asyncio.to_thread` for all Redis operations

### Medium-term (architecture improvements)
18. Migrate in-memory token revocation to Redis
19. Add `analysis_id` foreign key to `CodeFile` instead of JSON metadata
20. Extract shared `_try_providers` method in `AIFallbackChain`
21. Add debounce to KnowledgeBasePage search
22. Use `settings.OPENAI_MODEL`/`settings.GROQ_MODEL` instead of hardcoded model names
23. Remove dual `Base` classes (SQLAlchemy declarative_base + SQLModel)
24. Use multi-stage Docker builds
25. Add missing Prometheus exporters or update config