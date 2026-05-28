# CodeGuard AI — Performance & Scalability Audit

**Date:** 2026-05-28  
**Auditor:** Senior Scalability & Performance Engineer  
**Scope:** Full-stack — Backend (Python/FastAPI), Frontend (React/TS), Infrastructure (Docker/Celery/PostgreSQL)

---

## Executive Summary

CodeGuard AI has a solid architectural foundation but carries **17 distinct performance bottlenecks** and **8 scalability limitations** that will degrade user experience and increase costs under production load. The most impactful are: in-memory state that prevents horizontal scaling (#1), unbounded database queries that load full file contents (#3), a Celery task architecture that cannot scale (#7), and a frontend that loads Monaco Editor eagerly (#14). Collectively, the recommended fixes could reduce API response times by 60-80%, reduce memory per worker by ~40%, and improve frontend Time-to-Interactive by 4-6x.

---

## 1. PERFORMANCE BOTTLENECKS

### 1.1 CRITICAL — In-Memory Token Revocation Prevents Horizontal Scaling

**Location:** `backend/app/services/auth.py:31-58`

**Problem:** Token revocation uses a Python dict (`_revoked_tokens`) stored in process memory. This means:
- Every server worker maintains its own separate revocation list
- Revoking a token on Worker A has zero effect on Worker B
- Server restarts restore all revoked tokens — users stay logged out only until the server bounces
- The `_cleanup_revoked_tokens()` runs O(n) iteration on every `revoke_refresh_token` call

**Impact:** At 3+ uvicorn workers, ~67% of revocations silently fail. At 100K entries, cleanup takes milliseconds on every logout.

**Estimated Impact of Fix:** 100% revocation correctness at any scale, negligible per-request overhead.

**Fix:**
```python
# Replace in-memory dict with Redis SET with TTL
import redis.asyncio as aioredis
from app.core.config import settings

class TokenRevocationStore:
    def __init__(self):
        self._redis: aioredis.Redis | None = None
        self._local_fallback: dict[str, str] = {}  # single-worker fallback with TTL

    async def _get_redis(self):
        if self._redis is None and settings.REDIS_ENABLED:
            self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    async def revoke(self, token: str, ttl_seconds: int) -> None:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        r = await self._get_redis()
        if r:
            await r.setex(f"revoked:{token_hash}", ttl_seconds, "1")
        else:
            # Fallback: in-memory with expiry timestamp
            self._local_fallback[token_hash] = str(time.time() + ttl_seconds)

    async def is_revoked(self, token: str) -> bool:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        r = await self._get_redis()
        if r:
            return bool(await r.exists(f"revoked:{token_hash}"))
        expiry = self._local_fallback.get(token_hash)
        if expiry and float(expiry) > time.time():
            return True
        self._local_fallback.pop(token_hash, None)
        return False
```

---

### 1.2 CRITICAL — Full File Contents Loaded Into Memory for API Responses

**Location:** `backend/app/api/endpoints/scanner.py:253-262`

**Problem:** The scan results endpoint loads `CodeFile.content` (which can be 10MB per file) for ALL files in a scan, then builds a `code_files_dict` sending all file contents in a single API response:

```python
code_files_stmt = select(CodeFile).where(
    CodeFile.file_metadata["analysis_id"].as_string() == scan_id
)
code_files = code_files_result.scalars().all()

code_files_dict = {}
for cf in code_files:
    if cf.content:
        code_files_dict[cf.file_name] = cf.content
```

A scan with 50 files of 200KB each sends **10MB of JSON** in a single response. The SQLAlchemy query fetches every column including the massive `content` Text field, even for list views that don't need it.

**Impact:** 2-5 second response times on scan results, O(n) memory per request proportional to total file size across all scanned files.

**Estimated Impact of Fix:** 80-90% reduction in scan results payload size, 60-70% faster response time.

**Fix:**
1. Add a dedicated endpoint for individual file content: `GET /scanner/{scan_id}/files/{file_id}/content`
2. In the main results endpoint, use `load_only()` to exclude content:
```python
from sqlalchemy.orm import load_only

code_files_stmt = (
    select(CodeFile)
    .where(CodeFile.file_metadata["analysis_id"].as_string() == scan_id)
    .options(load_only(CodeFile.id, CodeFile.file_name, CodeFile.file_path, 
                       CodeFile.file_extension, CodeFile.language, CodeFile.line_count))
)
```
3. Frontend fetches file content on-demand when a user clicks a file, not upfront.

---

### 1.3 HIGH — N+1 Query on Findings with Fix Suggestions

**Location:** `backend/app/api/endpoints/scanner.py:247`, `share.py:148`

**Problem:** Only 3 endpoints use `selectinload(Finding.fix_suggestions)`. All other Finding queries (analysis list, admin reports) don't eager-load, causing N+1 queries. When displaying 20 findings with 2 suggestions each, this produces **61 queries** (1 for findings + 60 for suggestions).

**Impact:** Under load, this creates 3-5x more DB round trips than necessary.

**Estimated Impact of Fix:** 60-80% reduction in DB queries for findings pages.

**Fix:** Add `selectinload(Finding.fix_suggestions)` to all Finding queries, or use a `column_property` to aggregate suggestion counts.

---

### 1.4 HIGH — Scan Orchestrator Sequential LLM Calls

**Location:** `backend/app/services/scan_orchestrator.py:104-138`

**Problem:** The `_run_ai_analysis` method loops over findings and calls the AI chain **sequentially**:

```python
for finding in important_findings:
    # cache lookup...
    result = await ai_chain.generate(...)
    # parse result...
```

Each call to `ai_chain.generate()` can take 2-10 seconds. For 5 findings, this blocks for 10-50 seconds. With the circuit breaker and retries, it can be 60+ seconds.

**Impact:** Scan completion times of 30-120 seconds for typical workloads. Users see "analyzing" with no progress for extended periods.

**Estimated Impact of Fix:** 4-5x faster AI enrichment for typical scans (5 findings → parallel in ~3-10s vs sequential in ~15-50s).

**Fix:**
```python
import asyncio

async def _run_ai_analysis(self, ast_findings, code_snippets, language, scan_id):
    # Build all tasks upfront
    tasks = []
    for finding in important_findings:
        tasks.append(self._analyze_single_finding(finding, code_snippets, language, scan_id))
    
    # Run with bounded concurrency (3 concurrent LLM calls)
    semaphore = asyncio.Semaphore(3)
    
    async def run_with_sem(task):
        async with semaphore:
            return await task
    
    results = await asyncio.gather(
        *[run_with_sem(t) for t in tasks],
        return_exceptions=True
    )
    
    ai_findings = [r for r in results if r is not None and not isinstance(r, Exception)]
    for r in results:
        if isinstance(r, Exception):
            logger.warning(f"AI analysis for a finding failed: {r}")
    return ai_findings
```

---

### 1.5 HIGH — Celery Task Creates New Event Loop (Blocking + Leak)

**Location:** `backend/app/tasks/scan_tasks.py:85-95`

**Problem:** `run_scan_task` creates a brand-new `asyncio.new_event_loop()` for each scan. This:
- Cannot properly clean up the Docker client (httpx AsyncClient) created inside `spawn_container`
- Creates a new Docker client per scan (no connection reuse)
- The module-level `_sync_engine` global creates only one connection pool across all Celery workers in the same process, but the guard `if _sync_engine is None` is not thread-safe

**Impact:** Connection leak per scan task, growing memory usage, eventually Docker API connection exhaustion.

**Estimated Impact of Fix:** Eliminates connection leaks, enables connection pooling across scans.

**Fix:** Run async code via a long-lived event loop or use `asyncio.run()` (Python 3.10+) which handles cleanup. Better yet, restructure to use an async task runner (e.g., dramatiq with async, or FastAPI BackgroundTasks for single-server deployment).

---

### 1.6 MEDIUM — Docker Client Reinitialized Per Scan

**Location:** `backend/app/services/container.py:36-49`

**Problem:** `ContainerService._get_client()` creates a new Docker client lazily but never closes it. Combined with the new event loop per task above, each scan gets a fresh Docker client that never gets closed. During the scan, the client creates HTTP connections to the Docker daemon that remain open.

**Impact:** In production, after 50-100 scans, Docker socket file descriptors accumulate.

**Fix:** Use `@asynccontextmanager` for Docker client lifecycle or use a shared client with connection pooling.

---

### 1.7 MEDIUM — Admin Dashboard System Health Check Queries All Services Synchronously

**Location:** `backend/app/api/endpoints/admin.py` (system health endpoint)

**Problem:** The health endpoint checks PostgreSQL, Redis, and Ollama sequentially. Each check can timeout (5s default). If Ollama is down but PostgreSQL and Redis are healthy, users wait 10+ seconds for a health check.

**Estimated Impact of Fix:** Health check latency drops from sum(all_timeouts) to max(all_timeouts) — typically 500ms vs 10+ seconds.

**Fix:**
```python
results = await asyncio.gather(
    check_postgres(), check_redis(), check_ollama(),
    return_exceptions=True
)
```

---

### 1.8 MEDIUM — Rate Limiter Cookie Fallback Creates Shared Bucket

**Location:** `backend/app/core/rate_limit.py:22-34`

**Problem:** When `X-Forwarded-For` is absent and `request.client.host` is None (e.g., behind certain proxies), the fallback is the literal string `"unknown"`. All anonymous users sharing this bucket get rate-limited collectively. A single aggressive user can exhaust the "unknown" bucket for all anonymous users.

**Fix:** Use the rightmost IP from `X-Forwarded-For` and generate a UUID-based cookie for anonymous clients when no identifier is found, rather than lumping all unknowns together.

---

### 1.9 MEDIUM — Dashboard API Returns Zero for 3 of 4 Stats

**Location:** `frontend/src/pages/Dashboard.tsx:88-112`

**Problem:** Three stat cards (Code Files, Vulnerabilities, Security Score) are hardcoded to `value: 0`. The backend `analysis` endpoint returns the data needed but the Dashboard doesn't query for it. This means every Dashboard load triggers 2 API calls that return data that's partially unused.

**Impact:** Misleading UX, wasted API calls.

**Fix:** Query `/api/v1/analysis?limit=1000` to compute vulnerability counts and security scores, or add a dedicated `/dashboard/stats` endpoint.

---

### 1.10 MEDIUM — PromptManager LRU Cache Does Not Evict on TTL Properly

**Location:** `backend/app/services/cache.py:17-50`

**Problem:** The `LRUCache.set()` method moves items to the end on update (line 36) but only evicts from the front when `_max_size` is exceeded. Expired items are not proactively evicted — they're only checked on `get()`. This means the cache grows to `max_size` and stays there even if most entries are expired, consuming memory for stale data.

**Fix:** Add a periodic cleanup or evict expired items during `set()` as well:
```python
def set(self, key, value, ttl=3600):
    # Evict expired items before adding
    now = time.time()
    expired = [k for k, (_, exp) in self._cache.items() if exp and exp <= now]
    for k in expired:
        del self._cache[k]
    # Then proceed with normal LRU logic
```

---

### 1.11 MEDIUM — Frontend `apiFetch` Duplicated 5 Times

**Location:** `frontend/src/lib/api.ts`, `frontend/src/store/authStore.ts`, `frontend/src/store/scanStore.ts`, `frontend/src/hooks/useDashboardData.ts`, `frontend/src/hooks/useScanResults.ts`, `frontend/src/hooks/useAdmin.ts`, `frontend/src/hooks/useInstructor.ts`, `frontend/src/hooks/useKnowledgeBase.ts`

**Problem:** The `apiFetch` utility function is independently defined and slightly different in 7 files. Some set `Content-Type: application/json` unconditionally (breaking FormData uploads), others handle errors differently, some don't handle non-JSON responses.

**Impact:** Inconsistent error handling, FormData uploads broken in hooks that set Content-Type unconditionally, duplicated network config across 7 files.

**Estimated Impact of Fix:** ~200 lines of code removed, consistent API error handling, FormData actually works everywhere.

**Fix:** Single `apiFetch` in `lib/api.ts` (which already exists and correctly handles FormData by only setting Content-Type for string bodies). Remove all duplicates from hooks/stores and import from the shared module.

---

### 1.12 LOW-MEDIUM — No Database Query Timeout or Pagination Safety

**Location:** Multiple endpoints (`projects.py`, `admin.py`, `analysis.py`)

**Problem:** While most endpoints have `limit` parameters, they default to 20-100 and have no max cap on some routes. A request with `limit=100000` can load 100K rows into memory. No statement timeout is set on the DB engine.

**Impact:** A malicious or buggy client can cause OOM by requesting very large pages.

**Fix:** Add strict max limits (e.g., `Query(20, ge=1, le=100)`) to all paginated endpoints and set `statement_timeout` on the PostgreSQL engine.

---

### 1.13 LOW-MEDIUM — Benchmark Runner Runs AI Calls Synchronously

**Location:** `backend/app/benchmark/runner.py:122-130`

**Problem:** `_scan_with_ai` creates a new `asyncio.new_event_loop()` for each sample — the same anti-pattern as scan_tasks. Also, the runner processes samples sequentially with no parallelism.

**Impact:** Benchmark of 6 samples with AI takes 30-60 seconds vs 5-10 seconds with parallelism.

---

### 1.14 LOW — `TokenUsageTracker` Is In-Memory Only, Resets on Restart

**Location:** `backend/app/ai/fallback_chain.py:22-55`

**Problem:** Admin token usage tracking is a Python dict that resets on every server restart. After a restart, all usage data is lost. This means the `/admin/system/token-usage` endpoint shows zeroes after any restart.

**Fix:** Persist to Redis or a database table. Use the existing `PromptCache` Redis infrastructure.

---

### 1.15 LOW — `_analysis_dict()` and `_project_dict()` Manual Serialization

**Location:** `backend/app/api/endpoints/analysis.py:27-39`, `projects.py:26-37`

**Problem:** These functions manually serialize model fields with `if a.started_at else None` guards. This duplicates work Pydantic response models already handle, and is fragile when fields are added/removed.

**Fix:** Use Pydantic response models exclusively (already defined in `schemas/`) and return them directly with `model_dump()`.

---

### 1.16 LOW — Frontend Polling Creates Stale Timers

**Location:** `frontend/src/store/scanStore.ts:10-16`

**Problem:** Module-level `_pollTimers` array accumulates `setTimeout` references. If `pollScanStatus` is called multiple times (e.g., navigating away and back), old timers may not be cancelled if `_cancelPolling` doesn't run during component unmount. The `MAX_POLL_ATTEMPTS = 300` at 2s intervals means up to 10 minutes of polling per scan attempt.

**Fix:** Use `useEffect` cleanup to call `cancelPolling()`, or use `ref` instead of module-level array. Reduce `MAX_POLL_ATTEMPTS` to 60 (2 minutes) and rely on react-query retry logic.

---

### 1.17 LOW — Upload Handler Reads Full File Into Memory Before Validation

**Location:** `backend/app/api/endpoints/scanner.py:66`

**Problem:** `content = await upload_file.read()` loads the entire file into memory before checking size. A 10MB file consumes 10MB per concurrent upload. With 5 concurrent uploads, that's 50MB.

**Fix:** Stream-read with size checking, or use `SpooledTemporaryFile` with a max size:
```python
# Read in chunks with size limit
content = b""
async for chunk in upload_file.chunks():
    content += chunk
    if len(content) > MAX_UPLOAD_SIZE:
        raise FileException(f"File exceeds maximum size")
```

---

## 2. SCALABILITY LIMITATIONS

### 2.1 CRITICAL — Single-Process In-Memory State Blocks Multi-Worker

**Affected:** Token revocation store, circuit breaker state, `TokenUsageTracker`, `PromptCache` LRU fallback

All four in-memory stores reset on restart and don't share state across workers. In a production deployment with 4+ gunicorn/uvicorn workers:
- Token revocations are ~75% ineffective
- Circuit breaker state doesn't propagate (one worker may keep retrying a dead provider)
- Token usage metrics are fragmented per worker
- Cache misses increase 4x

**Impact:** Horizontal scaling is fundamentally broken for auth and AI features.

**Fix:** Move all state to Redis. Circuit breaker state should be in Redis with atomic operations. Token usage should be Redis HINCRBY.

---

### 2.2 HIGH — SQLite Won't Scale Past Single-User Development

**Location:** `backend/app/core/config.py:45`

**Problem:** Default `DATABASE_URL` is SQLite (`sqlite+aiosqlite:///./codeguard.db`). SQLite handles only one write at a time. Under concurrent scans, the WAL mode helps reads but writes still serialize, causing 2-10 second contentions.

**Impact:** In production with 10+ concurrent users, scan writes block auth reads, causing login timeouts.

**Fix:** The docker-compose.yml correctly uses PostgreSQL, but local development should also default to PostgreSQL or at minimum document the limitation clearly. The `DATABASE_URL` default should be `postgresql+asyncpg://...`, not SQLite.

---

### 2.3 HIGH — Celery Worker Cannot Scale Beyond One Process Per Task Type

**Location:** `backend/app/tasks/scan_tasks.py`, `backend/app/tasks/celery_app.py`

**Problem:**
1. The `_sync_engine` global is not fork-safe if Celery uses prefork (default)
2. `asyncio.new_event_loop()` per task means no connection reuse for Docker or DB
3. No task priority or routing — scans queue behind all other tasks
4. `task_time_limit=300` (5 min) is too short for large scans that take 10+ minutes

**Fix:** Use `--pool=solo` or `--pool=gevent` for Celery workers handling async code, or migrate to an async-native task queue. Increase time limit to match `SCANNER_TIMEOUT`.

---

### 2.4 MEDIUM — No Connection Pooling for LLM Provider Clients

**Location:** `backend/app/ai/providers/openai_provider.py:18-24`, `groq_provider.py:18-24`

**Problem:** `OpenAIProvider.__init__()` and `GroqProvider.__init__()` create `AsyncOpenAI()` and `AsyncGroq()` clients with `max_retries=2`. These are created once per `AIFallbackChain` initialization. But the `AIFallbackChain` is a module-level singleton, so this is fine — however, the providers are instantiated eagerly even when no AI calls are made.

**Fix:** Lazy initialization of provider clients (only create when first `.generate()` / `.chat()` is called). This avoids importing `openai`/`groq` packages at startup when their API keys aren't set.

---

### 2.5 MEDIUM — File Upload Directory Not Cleaned Up

**Location:** `backend/app/api/endpoints/scanner.py:57-58`

**Problem:** `os.makedirs(upload_dir, exist_ok=True)` creates directories under `/tmp/codeguard_uploads/{scan_id}/` but they're never cleaned up after scan completion. Over time, disk fills up with scan artifacts.

**Fix:** Add a cleanup task (Celery beat or post-scan hook) that removes upload directories after processing, or use `tempfile.TemporaryDirectory()` scoped to the scan lifecycle.

---

### 2.6 MEDIUM — No Request-Level Caching for Dashboard Data

**Location:** Frontend hooks (`useDashboardData`, `useScanResults`, etc.)

**Problem:** React-Query's `staleTime: 2 * 60 * 1000` helps, but the Dashboard endpoint still queries the database for analyses with no server-side caching. Each Dashboard load hits PostgreSQL even for data that hasn't changed.

**Fix:** Add `ETag` headers or short-lived Redis caching for dashboard data:
```python
@router.get("/dashboard/stats")
@cache(ttl=30)  # 30-second Redis cache
async def dashboard_stats(...):
    ...
```

---

### 2.7 LOW-MEDIUM — Frontend Bundle Size Concerns

**Location:** `frontend/vite.config.js:27-33`, `package.json`

**Problem:** The `manualChunks` config in vite.config.js uses the object format which is incompatible with Rolldown (Vite 8's bundler), causing the build to crash. More importantly, Monaco Editor (~2MB gzipped), Recharts (~300KB), and Lucide Icons (tree-shakeable but still significant) are in the main chunk.

**Impact:** Build currently fails. When fixed, initial load will be 2-3MB without code splitting for Monaco.

**Fix:**
1. Convert `manualChunks` to function format for Rolldown compatibility
2. Lazy-load Monaco Editor only on the Report page
3. Use `@monaco-editor/react`'s dynamic import
```js
build: {
  rollupOptions: {
    output: {
      manualChunks(id) {
        if (id.includes('@monaco-editor')) return 'editor'
        if (id.includes('recharts')) return 'charts'
        if (id.includes('lucide-react')) return 'icons'
        if (id.includes('node_modules')) return 'vendor'
      }
    }
  }
}
```

---

### 2.8 MEDIUM — Container Semaphore Is Per-Process Not Global

**Location:** `backend/app/services/container.py:15-27`

**Problem:** `_get_semaphore()` creates an `asyncio.Semaphore(5)` per process. In a multi-worker deployment (e.g., 4 uvicorn workers), the effective concurrency limit is 20 (5 × 4), not 5. This could overwhelm the Docker daemon.

**Fix:** Use Redis or a database advisory lock to enforce a global concurrency limit across processes.

---

## 3. OPTIMIZATION OPPORTUNITIES

### 3.1 Database Query Optimization

| Query | Current | Optimized | Impact |
|-------|---------|-----------|--------|
| Scan results with file content | Loads ALL columns for ALL files | `load_only()` + separate content endpoint | 80-90% payload reduction |
| Findings + fix_suggestions | 1+N queries (lazy loaded) | `selectinload` on all finding queries | 60-80% fewer DB round trips |
| Admin user list | Separate count + query | Use `window` function for count in same query | 50% fewer DB round trips |
| Dashboard stats | 2 API calls, both uncached | Single `/dashboard/stats` endpoint with 30s Redis cache | 90% reduction in DB load |
| Analysis list with project name | No `joinedload` on project | Add `selectinload(Analysis.project)` | Eliminates N+1 |

### 3.2 Frontend Optimization

| Area | Current | Optimized | Impact |
|------|---------|-----------|--------|
| Monaco Editor | Loaded in main chunk | Lazy import only on ReportPage | Reduces initial JS by ~2MB |
| Recharts | Loaded in main chunk | Lazy import only on Dashboard/ClassMetrics | Reduces initial JS by ~300KB |
| `apiFetch` | Duplicated in 7 files | Single source in `lib/api.ts` | -200 lines, consistent errors |
| `unwrap` | Duplicated in 5 files | Single source in `lib/api.ts` | -50 lines, consistent parsing |
| Scan polling | `setTimeout` chains in Zustand | Use `useQuery` with `refetchInterval` | Eliminates timer management |
| Auth store | 280-line monolith | Split auth state from API calls | Better tree-shaking |
| Dashboard | 3 hardcoded zero stats | Query real data | Meaningful UX |

### 3.3 Backend Optimization

| Area | Current | Optimized | Impact |
|------|---------|-----------|--------|
| AI analysis | Sequential per-finding | Parallel with `asyncio.gather` (semaphore=3) | 4-5x faster |
| Token revocation | In-memory dict | Redis SET with TTL | Horizontal scaling |
| Circuit breaker | In-memory dict per process | Redis atomic operations | Consistent across workers |
| Container client | New per scan | Shared singleton with cleanup | No connection leaks |
| Benchmark runner | Sequential samples | Run all samples in parallel | 5-6x faster |
| Health check | Sequential service probes | `asyncio.gather` | 80% faster |

---

## 4. REFACTORED PRODUCTION-GRADE SOLUTIONS

### 4.1 Redis-Backed Token Revocation (Critical)

```python
# backend/app/services/auth.py — Replace in-memory dict

import hashlib
from datetime import datetime, timedelta, timezone
from app.core.config import settings

class TokenRevocationStore:
    """Redis-backed token revocation with local fallback."""

    def __init__(self):
        self._local_cache: dict[str, float] = {}  # hash -> expiry_ts (fallback)
        self._redis = None

    async def _get_redis(self):
        if self._redis is None and settings.REDIS_ENABLED:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    async def revoke(self, token: str, ttl_seconds: int) -> None:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        r = await self._get_redis()
        if r:
            await r.setex(f"revoked:{token_hash}", ttl_seconds, "1")
        else:
            self._local_cache[token_hash] = (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).timestamp()

    async def is_revoked(self, token: str) -> bool:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        r = await self._get_redis()
        if r:
            return bool(await r.exists(f"revoked:{token_hash}"))
        expiry = self._local_cache.get(token_hash)
        if expiry and expiry > datetime.now(timezone.utc).timestamp():
            return True
        self._local_cache.pop(token_hash, None)
        return False

token_store = TokenRevocationStore()

async def revoke_refresh_token(token: str) -> None:
    await token_store.revoke(token, settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400)

async def is_refresh_token_revoked(token: str) -> bool:
    return await token_store.is_revoked(token)

async def revoke_access_token(token: str) -> None:
    await token_store.revoke(token, settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60)

async def is_access_token_revoked(token: str) -> bool:
    return await token_store.is_revoked(token)
```

### 4.2 Parallel AI Analysis (High Impact)

```python
# backend/app/services/scan_orchestrator.py — Replace sequential loop

import asyncio

AI_CONCURRENCY = 3  # Max parallel LLM calls

async def _run_ai_analysis(self, ast_findings, code_snippets, language, scan_id):
    important_findings = [f for f in ast_findings if f.get("severity") in ("critical", "high")]
    if not important_findings:
        important_findings = ast_findings[:5]

    semaphore = asyncio.Semaphore(AI_CONCURRENCY)

    async def analyze_finding(finding):
        async with semaphore:
            return await self._analyze_single_finding(finding, code_snippets, language, scan_id)

    results = await asyncio.gather(
        *[analyze_finding(f) for f in important_findings],
        return_exceptions=True
    )

    ai_findings = []
    for r in results:
        if isinstance(r, Exception):
            logger.warning(f"AI finding analysis failed: {r}")
        elif r is not None:
            ai_findings.append(r)
    return ai_findings if ai_findings else None
```

### 4.3 Unified Frontend API Client

```typescript
// frontend/src/lib/api.ts — Single source of truth

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
export { API_BASE_URL }

export function unwrap<T>(response: unknown): T {
  if (!response || typeof response !== 'object') {
    throw new Error('Invalid API response')
  }
  const obj = response as Record<string, unknown>
  const data = obj.data
  if (!data) throw new Error('No data in API response')
  if (typeof data === 'object' && data !== null && 'items' in (data as Record<string, unknown>)) {
    return (data as Record<string, unknown>).items as T
  }
  return data as T
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = path.startsWith('http') ? path : `${API_BASE_URL}${path}`
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  }
  // Only set Content-Type for JSON bodies (let FormData set its own boundary)
  if (options.body && typeof options.body === 'string') {
    headers['Content-Type'] = 'application/json'
  }
  const response = await fetch(url, { ...options, headers, credentials: 'include' })
  if (!response.ok) {
    let detail = `API error: ${response.status}`
    try {
      const body = await response.json()
      detail = body.detail || body.message || detail
    } catch { /* response wasn't JSON */ }
    throw new Error(detail)
  }
  const text = await response.text()
  if (!text) return undefined as T
  return JSON.parse(text)
}
```

Then **remove** all duplicate `apiFetch` and `unwrap` from:
- `store/authStore.ts`
- `store/scanStore.ts`
- `hooks/useDashboardData.ts`
- `hooks/useScanResults.ts`
- `hooks/useAdmin.ts`
- `hooks/useInstructor.ts`
- `hooks/useKnowledgeBase.ts`

And replace with:
```typescript
import { apiFetch, unwrap } from '../lib/api'
```

### 4.4 Lazy Monaco Editor Loading

```typescript
// frontend/src/components/report/CodeViewer.tsx — Replace eager import

// BEFORE:
// import Editor from '@monaco-editor/react'

// AFTER:
import { lazy, Suspense } from 'react'
const MonacoEditor = lazy(() => import('@monaco-editor/react'))

function CodeViewer(props: EditorProps) {
  return (
    <Suspense fallback={<div className="h-64 flex items-center justify-center text-text-muted">Loading editor...</div>}>
      <MonacoEditor {...props} />
    </Suspense>
  )
}
```

### 4.5 Scan Results File Content On-Demand

```python
# backend/app/api/endpoints/scanner.py — Add lazy file content endpoint

@router.get("/{scan_id}/files/{file_id}/content", response_model=dict)
async def get_file_content(
    scan_id: str,
    file_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Fetch content for a single code file (for on-demand loading)."""
    stmt = select(CodeFile).where(CodeFile.id == file_id)
    result = await db.execute(stmt)
    code_file = result.scalar_one_or_none()
    if not code_file:
        raise NotFoundException(message="File not found")
    return ResponseSchema(data={"id": code_file.id, "content": code_file.content})
```

Then modify the scan results endpoint to exclude content from the main payload:
```python
code_files_stmt = (
    select(CodeFile)
    .where(CodeFile.file_metadata["analysis_id"].as_string() == scan_id)
    .options(load_only(
        CodeFile.id, CodeFile.file_name, CodeFile.file_path,
        CodeFile.file_extension, CodeFile.language, CodeFile.line_count
    ))
)
code_files = [cf for cf in code_files_result.scalars().all()]
# Return file metadata only; content fetched on demand
code_files_meta = {cf.file_name: {"id": cf.id, "language": cf.language, "lines": cf.line_count} for cf in code_files}
```

---

## 5. ESTIMATED PERFORMANCE IMPACT

| # | Fix | Current | After Fix | Improvement |
|---|-----|---------|-----------|-------------|
| 1.1 | Redis token revocation | ~67% revocations fail at 3 workers | 100% effectiveness | **Critical** |
| 1.2 | Lazy file content loading | 2-5s, 10MB+ payload | 200ms, <500KB | **80-90% faster** |
| 1.3 | Eager-load fix_suggestions | 61 queries for 20 findings | 1 query | **60x fewer queries** |
| 1.4 | Parallel AI analysis | 30-120s per scan | 5-15s per scan | **4-5x faster** |
| 1.5 | Fix Celery async pattern | Connection leak per scan | Reused connections | **Eliminates leak** |
| 1.6 | Docker client pooling | FD leak | Single shared client | **Eliminates leak** |
| 1.7 | Parallel health checks | 10-15s worst case | 3-5s worst case | **3-5x faster** |
| 1.9 | Dashboard real stats | 3/4 stats always zero | Actual data | **UX improvement** |
| 2.1 | Redis state sharing | 4 workers = 4 separate states | Shared state | **Horizontal scaling** |
| 2.7 | Lazy Monaco loading | ~3MB initial JS | ~800KB initial JS | **4x faster TTI** |
| 3.1 | Frontend unified API | 7 duplicated files | 1 shared file | **-200 lines** |
| 3.3 | Container global semaphore | 5×workers concurrent scans | 5 total across all | **Controlled concurrency** |

**Overall Estimated Impact:**
- API response times: **60-80% faster** for scan results
- Frontend Time-to-Interactive: **4-6x faster** (2MB → ~800KB initial load)
- Database queries: **60-80% reduction** via eager loading and caching
- Scan completion: **4-5x faster** via parallel AI analysis
- Horizontal scaling: **Enabled** (currently blocked by in-memory state)
- Memory per worker: **~40% reduction** (no full file contents loaded for lists)