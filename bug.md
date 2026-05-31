# CodeGuard AI — Bug & Production Risk Report

**Auditor:** Senior QA Engineer  
**Date:** 2026-05-28  
**Scope:** Backend (Python/FastAPI), Frontend (React/TypeScript), Infrastructure

---

## CRITICAL SEVERITY

### BUG-01: Race Condition in Token Revocation (TOCTOU on Refresh)

**File:** `backend/app/api/endpoints/auth.py` lines 191–241  
**How it occurs:** The `/auth/refresh` endpoint reads the refresh token from the cookie, checks if it's revoked, then issues new tokens and revokes the old one. If two refresh requests arrive simultaneously (e.g., two tabs), both pass the revocation check before either revokes, resulting in two valid access tokens and the first token being revoked while the second refresh succeeds — but the old token is now invalid for future use while the client still holds it.  
**User impact:** Users get logged out unexpectedly, or worse, one of the two concurrent sessions gets an invalid refresh token.  
**Severity:** Critical  
**Reproduction:** Open two tabs, both with expired access tokens. Trigger refresh in both within milliseconds. One will fail with "token has been revoked."  
**Fix:** Use a Redis-based token family scheme or add a nonce/identifier to tokens and rotate atomically with a Redis WATCH/MULTI transaction. Alternatively, add a short grace period window in `is_refresh_token_revoked()` that allows the old token for ~5 seconds after revocation.

---

### BUG-02: Account Lockout Bypass via Timing Side-Channel

**File:** `backend/app/services/auth.py` lines 276–282, `backend/app/api/endpoints/auth.py` lines 144–161  
**How it occurs:** When an account IS locked, the API responds with a specific message: "Account is temporarily locked. Try again in X minutes." When an account is NOT locked but the password is wrong, it responds with "Invalid email or password." An attacker probing for valid emails can distinguish between a locked account (email exists) and invalid credentials (email may not exist).  
**User impact:** Email enumeration allows targeted phishing attacks.  
**Severity:** Critical  
**Reproduction:** Send a login request with a correct email and wrong password 5+ times to trigger lockout. Then send a request with a non-existent email — different error response.  
**Fix:** Always return the same generic error message regardless of whether the account is locked, email doesn't exist, or password is wrong. Don't reveal the remaining lockout time. Example:

```python
# Instead of specific lockout error:
if user and is_account_locked(user):
    raise UnauthorizedException(message="Invalid email or password")
    # Same message as wrong password — no info leakage
```

Also add a uniform delay (e.g., 500ms) on all auth endpoints to prevent timing attacks.

---

### BUG-03: Arbitrary Column Update in Admin User Patch (Privilege Escalation Vector)

**File:** `backend/app/api/endpoints/admin.py` lines 84–132  
**How it occurs:** The `update_user` endpoint uses `AdminUserUpdate` schema which includes `is_active`, `role`, and `full_name`. While the schema validates role values, there's no protection against an admin setting their own `is_superuser` field through the `model_dump()` on line 119 which logs ALL changes. More critically, the `data.model_dump()` call at line 119 in the `SystemEvent` metadata includes the raw input — but the real issue is that `AdminUserUpdate` schema includes `email` as `Optional[EmailStr]`, and there's no separate email verification flow. An admin could change any user's email without verification.  
**User impact:** Admin can change user emails without verification, potentially hijacking accounts.  
**Severity:** Critical  
**Reproduction:** PATCH `/api/v1/admin/users/{id}` with `{"email": "attacker@evil.com"}` — the email changes without confirmation.  
**Fix:** Remove `email` from `AdminUserUpdate` or require a separate email verification flow. At minimum, add a check: `if data.email and data.email != user.email: raise HTTPException(400, "Email changes require verification")`.

---

### BUG-04: SSRF-Adjacent Vulnerability in Ollama URL Validation

**File:** `backend/app/ai/ollama_client.py` lines 22–43  
**How it occurs:** The `_validate_ollama_url` function whitelists specific hostnames but relies on `urlparse` for hostname extraction. A URL like `http://127.0.0.1:11434@evil.com/api/generate` would have `hostname` set to `evil.com` (which is not in the allowlist), but more critically, `http://0x7f000001:11434` (hex-encoded 127.0.0.1) passes the `ip_address()` check because Python's `ip_address` doesn't parse hex IPs in URLs — but `0x7f000001` could bypass hostname checks. Additionally, DNS rebinding attacks could resolve an allowed hostname to an internal IP after validation.  
**User impact:** Attacker with access to the OLLAMA_URL env var (or config) could redirect AI inference requests to an arbitrary internal server.  
**Severity:** High  
**Reproduction:** Set `OLLAMA_URL=http://0x7f000001:11434` and observe it resolves to 127.0.0.1, potentially bypassing validation.  
**Fix:** After URL parsing, resolve the hostname and verify the resolved IP is in the allowlist. Use `socket.getaddrinfo()` and check all resolved IPs against `ipaddress.ip_network` for private ranges.

---

## HIGH SEVERITY

### BUG-05: Unbounded Upload Directory Accumulation (Disk Exhaustion)

**File:** `backend/app/api/endpoints/scanner.py` lines 59–186  
**How it occurs:** When the upload succeeds but the Celery task fails to start (e.g., Redis is down so the task isn't queued), the upload directory is created on disk but never cleaned up. The cleanup in `scan_tasks.py` only runs inside the Celery task. If `run_scan_task.delay()` raises an exception or the task never executes, files accumulate indefinitely.  
**User impact:** Disk fills up on the API server, causing Denial of Service.  
**Severity:** High  
**Reproduction:** Upload files while Redis/Celery is down. The files remain in `/tmp/codeguard_uploads/{scan_id}/` forever.  
**Fix:** Add a try/except around `run_scan_task.delay()` in the upload endpoint that removes the upload directory if task dispatch fails. Also add a periodic cleanup cron job for orphaned directories older than 24 hours.

---

### BUG-06: Container Not Removed on Spawn Failure

**File:** `backend/app/services/container.py` lines 80–153  
**How it occurs:** If `container.wait()` times out (the `_wait_container` method), the container is left running. The `finally` block tries `container.remove(force=True)`, but if the Docker daemon connection was lost during the wait, `remove()` will also fail silently. Meanwhile, the container continues consuming resources. Additionally, `ContainerService.close()` is called in `scan_tasks.py` finally block, but this kills the Docker client — if a subsequent scan is queued on the same worker, `_get_client()` will reinitialize, but any containers from the previous failed scan that weren't removed will leak.  
**User impact:** Docker host runs out of resources (memory, CPU, container count limit).  
**Severity:** High  
**Reproduction:** Kill the Docker socket mid-scan. Observe leaked containers with `docker ps -a`.  
**Fix:** Move `ContainerService.close()` out of the finally block and instead ensure container removal is more robust. Add a container label (`codeguard-scan-id`) and implement a watchdog that periodically removes orphaned containers.

---

### BUG-07: Prompt Manager Singleton Not Thread-Safe in Multi-Worker Deployments

**File:** `backend/app/api/endpoints/ai.py` lines 23–25  
**How it occurs:** `_prompt_manager = PromptManager()` and `_output_parser = LLMOutputParser()` are module-level singletons. In a multi-worker uvicorn deployment, each worker process has its own copy. If `PromptManager.__init__` loads templates from disk and caches them, concurrent access from multiple coroutines within the same process should be fine (asyncio is single-threaded). But if `PromptManager` or `LLMOutputParser` have mutable state that gets modified during `render_template()` or `parse_*()` calls, concurrent requests could corrupt that state.  
**User impact:** Garbled prompt rendering or parsed responses in rare concurrent conditions.  
**Severity:** High (if state mutation exists) / Low (if truly read-only after init)  
**Reproduction:** Unclear — depends on whether `PromptManager`/`LLMOutputParser` mutate state during rendering/parsing.  
**Fix:** Verify `PromptManager` and `LLMOutputParser` are truly stateless after initialization. If they use any mutable state (caches, counters), protect with `asyncio.Lock` or use `functools.lru_cache` for deterministic results.

---

### BUG-08: Race Condition in `scanStore` Polling — Stale Timers Not Cancelled

**File:** `frontend/src/store/scanStore.ts` lines 101–131  
**How it occurs:** The polling implementation stores timer references on the Zustand state object via `(get() as Record<string, unknown>)._pollTimers`. When `pollScanStatus` is called, it first calls `cancelPolling()` to clear old timers, then creates new ones. However, `cancelPolling()` only clears the timers from the *previous* poll cycle — if `fetchScanStatus` throws before setting a new timer, no new timer array is created, and the reference is lost. More critically, when `clearScan()` is called from a component unmount, it cancels timers, but the `poll()` async function may still be awaiting — and after the await resolves, it will try to `set()` state on an unmounted component.  
**User impact:** Memory leak, state updates on unmounted components, stale data in UI.  
**Severity:** High  
**Reproduction:** Start a scan, navigate away before it completes, navigate back. Observe stale poll timers or React state update warnings.  
**Fix:** Replace the ad-hoc timer management with a proper `AbortController` pattern or React's `useRef` + cleanup pattern. Use a flag to track whether polling is active:

```typescript
pollScanStatus: async (scanId: string) => {
  get().cancelPolling()
  const controller = new AbortController()
  // Store controller for cancellation
  // In fetch calls, pass signal: controller.signal
}
```

Also add a `useEffect` cleanup in components that calls `cancelPolling()` on unmount.

---

### BUG-09: Redis Client Connection Leak in Token Revocation

**File:** `backend/app/services/auth.py` lines 39–49  
**How it occurs:** The `_get_redis()` function creates a new `aioredis.from_url()` client but never closes it. If Redis becomes unavailable and `_redis_client` is set to `None`, the next call will try to connect again. But if it connects and then Redis goes down mid-connection, the stale client reference remains in `_redis_client` and all subsequent calls will fail with connection errors until the process restarts. There's no reconnection logic or health check.  
**User impact:** Once Redis has a transient failure, token revocation stops working for the lifetime of the process. Logout no longer invalidates tokens.  
**Severity:** High  
**Reproduction:** Start with Redis available, perform logout (token is revoked in Redis). Kill Redis. Perform logout again — it will fail silently and fall back to in-memory revocation, which is per-process. In multi-worker deployments, revocation is lost on other workers. Restart Redis — the old `_redis_client` is still broken and won't reconnect.  
**Fix:** Add a `close()` method and connection health check. Replace the stale connection on error:

```python
async def _get_redis():
    global _redis_client
    if _redis_client is not None:
        try:
            await _redis_client.ping()
            return _redis_client
        except Exception:
            await _redis_client.close()
            _redis_client = None
    # Create new connection...
```

---

### BUG-10: Sync Redis Client in PromptCache Blocks Event Loop

**File:** `backend/app/services/cache.py` lines 77–93  
**How it occurs:** `_get_client()` creates a synchronous Redis client (`redis.from_url`), not an async one. While `get()` and `set()` calls are wrapped in `asyncio.to_thread()`, the `_get_client()` method itself blocks to call `ping()` synchronously. If Redis is slow, this blocks the entire async event loop on the first cache access.  
**User impact:** First request to any AI endpoint blocks all other requests until Redis `ping()` completes or times out.  
**Severity:** High  
**Reproduction:** Set a very short Redis timeout or point to a non-responsive Redis. First AI request hangs the entire server.  
**Fix:** Convert `PromptCache` to use `redis.asyncio` (aioredis) for all operations, including the initial `ping()`. Use `await self._client.ping()` instead of `self._client.ping()`.

---

## MEDIUM SEVERITY

### BUG-11: In-Memory Token Revocation Not Shared Across Workers

**File:** `backend/app/services/auth.py` lines 30, 64, 77–83  
**How it occurs:** `_revoked_tokens` is a Python dict at module level. In a multi-worker deployment (uvicorn --workers 4), each worker has its own `_revoked_tokens`. If a user logs out on worker 1, the revocation is only in that worker's memory. The access token will still work on workers 2-4.  
**User impact:** Logout doesn't fully work in production.  
**Severity:** Medium  
**Reproduction:** Deploy with `uvicorn --workers 4`, log in, log out, immediately hit a different worker — the old access token still works for up to 30 minutes.  
**Fix:** Always use Redis for token revocation. Remove the in-memory fallback or make it only used for development. When Redis is unavailable, treat all tokens as valid (fail-open) and log loudly, rather than silently accepting all tokens.

---

### BUG-12: Scanner Endpoint Missing Rate Limiting

**File:** `backend/app/api/endpoints/scanner.py`  
**How it occurs:** The `/upload` endpoint has no rate limiting. An attacker could upload massive files repeatedly, consuming storage and queuing many scans, depleting Docker resources. The `MAX_FILE_SIZE` check exists but doesn't prevent repeated uploads.  
**User impact:** Denial of Service via resource exhaustion.  
**Severity:** Medium  
**Reproduction:** Write a script that POSTs to `/api/v1/scanner/upload` with valid files 100 times in rapid succession.  
**Fix:** Add `@limiter.limit("5/minute")` to the upload endpoint.

---

### BUG-13: `uploadFiles` Doesn't Set Content-Type for Error Responses

**File:** `frontend/src/store/scanStore.ts` lines 42–80  
**How it occurs:** In `uploadFiles`, the `FormData` upload works because the browser automatically sets the multipart boundary. But in the error handling, `response.json()` is called without checking `Content-Type` first. If the server returns a 502 with an HTML error page (nginx default), `response.json()` will throw a `SyntaxError` which gets caught by the generic `catch` block and reported as "Upload failed" instead of showing the actual error.  
**User impact:** Misleading error messages when the server is behind a reverse proxy.  
**Severity:** Medium  
**Reproduction:** Put nginx in front, take the backend down, and try to upload. You'll get "Upload failed" instead of a useful message.  
**Fix:** Check `response.headers.get('content-type')` before parsing JSON. Fall back to `response.text()` for non-JSON responses.

---

### BUG-14: Celery Task `_update_analysis_status` SQL Injection Vector (Parameterized, But Fragile)

**File:** `backend/app/tasks/scan_tasks.py` lines 175–208  
**How it occurs:** The function uses parameterized queries with `:scan_id` which is safe. However, the `_ALLOWED_UPDATE_COLUMNS` check only validates column names in `update_fields`. The `set_clauses` string is built from dictionary keys that pass the allowlist. While currently safe (the allowlist is a frozenset), if someone adds dynamic columns in the future without careful review, it could introduce injection. More importantly, `metadata` is serialized with `json.dumps(metadata)` — if `metadata` contains user-controlled keys from scanner output, and those keys contain special characters, the JSON is still safe for SQL, but the potential for future misuse exists.  
**User impact:** Currently safe, but fragile architecture.  
**Severity:** Medium (defense in depth)  
**Reproduction:** N/A — no current exploit, but architectural risk.  
**Fix:** Use SQLAlchemy Core or ORM for updates instead of raw text-based SQL. This eliminates the allowlist pattern entirely and provides type safety.

---

### BUG-15: No CORS Restriction in Development Mode Creates Security Habit

**File:** `backend/app/core/config.py` line 37  
**How it occurs:** `CORS_ORIGINS` defaults to `["http://localhost:5173", "http://localhost:3000"]`. While not wildcard `*`, this is only secure if the backend is truly only accessible from localhost. In Docker deployments where the backend port is exposed, any website can make requests to `localhost:8000` if the victim is running the app locally.  
**User impact:** CSRF-style attacks from malicious websites when developers have the app running locally.  
**Severity:** Medium  
**Reproduction:** Create a malicious HTML page that posts to `http://localhost:8000/api/v1/auth/logout` — if the developer is logged in, their session is terminated.  
**Fix:** Add `CORS_ALLOW_ORIGINS` validation that rejects localhost origins in production. In development, restrict to specific ports only. Also ensure CSRF protection via `SameSite=Strict` cookies (currently `lax`, which allows top-level navigations).

---

### BUG-16: `ContainerService._get_client()` Race Condition

**File:** `backend/app/services/container.py` lines 44–57  
**How it occurs:** `_get_client()` is not thread-safe. If two Celery task threads call it simultaneously on first access, both check `self._client is None`, both enter the creation block, and one overwrites the other. `close()` then closes only one client while the other leaks.  
**User impact:** Docker client connection leak and potential double-initialization.  
**Severity:** Medium  
**Reproduction:** Trigger two scans simultaneously when the service hasn't been initialized.  
**Fix:** Add a `threading.Lock` around client initialization in `_get_client()`:

```python
import threading
class ContainerService:
    def __init__(self):
        self._client = None
        self._lock = threading.Lock()
    def _get_client(self):
        if self._client is None:
            with self._lock:
                if self._client is None:  # double-check
                    import docker
                    self._client = docker.from_env()
        return self._client
```

---

### BUG-17: Password Reset Token Stored in Plain Text in Database

**File:** `backend/app/models/user.py` line 60-63  
**How it occurs:** The `password_reset_token` field stores the token directly in the database. If the database is compromised, all pending password reset tokens are exposed, allowing an attacker to reset any user's password.  
**User impact:** Full account takeover if DB is compromised.  
**Severity:** Medium  
**Reproduction:** Read the `users` table — `password_reset_token` column contains the raw token.  
**Fix:** Store only the SHA-256 hash of the reset token, similar to how passwords are hashed. When a reset request comes in, hash it and compare against the stored hash.

---

## LOW SEVERITY

### BUG-18: `unwrap()` Unwraps Nested Data Incorrectly for Paginated Responses

**File:** `frontend/src/lib/api.ts` lines 14–28  
**How it occurs:** If an API returns `{ data: { items: [...], total: 5 } }`, `unwrap()` returns just the `items` array, discarding `total`. But some hooks like `useDashboardData` expect the full paginated response object. This causes `totalProjects` and other pagination data to be lost.  
**User impact:** Dashboard metrics like total counts are often `undefined` or `0`.  
**Severity:** Low  
**Reproduction:** Load the dashboard — total project count may be incorrect.  
**Fix:** Add an option to `unwrap` to control whether to extract items or return the full data envelope:

```typescript
export function unwrap<T>(response: unknown, extractItems: boolean = true): T {
  // If extractItems and data has items, return items
  // Otherwise return data as-is
}
```

---

### BUG-19: `scanStore` Polling Timer Maximum Raised Too High Then Lowered

**File:** `frontend/src/store/scanStore.ts` line 9  
**How it occurs:** The `MAX_POLL_ATTEMPTS` was changed from 300 to 90, but 90 attempts at 2-second intervals = 3 minutes. For a scanner timeout of 600 seconds (10 minutes), this is far too short. The scan will appear to "time out" while the Celery task is still processing.  
**User impact:** Long-running scans show "taking too long" error while they're still processing.  
**Severity:** Low  
**Reproduction:** Upload a large codebase that takes >3 minutes to scan.  
**Fix:** Either increase `MAX_POLL_ATTEMPTS` to 300+ (matching the 10-minute scanner timeout) or implement exponential backoff instead of fixed 2-second intervals.

---

### BUG-20: `_persist_findings` Only Maps to First File

**File:** `backend/app/tasks/scan_tasks.py` lines 228–229  
**How it occurs:** `file_id = file_ids[0] if file_ids else None` maps ALL findings to the first uploaded file, regardless of which file they actually belong to. This means finding-to-file association is always wrong for multi-file uploads.  
**User impact:** Findings show the wrong file associations in the UI.  
**Severity:** Low  
**Reproduction:** Upload multiple files with vulnerabilities. All findings will be associated with only the first file.  
**Fix:** The scanner output should include `file_path` per finding. Use that to match back to `CodeFile` IDs:

```python
file_id_map = {}
for fid in file_ids:
    # Query code_file to get file_path -> id mapping
    ...
# Then per finding:
finding_file_id = file_id_map.get(finding_data.get("file_path"), file_id)
```

---

### BUG-21: Frontend `apiFetch` Doesn't Handle Empty Response Bodies

**File:** `frontend/src/lib/api.ts` lines 55–68  
**How it occurs:** When a response has status 200 but an empty body (e.g., DELETE endpoints returning 204, or a 200 with no content), `response.text()` returns `""`, and `JSON.parse("")` throws a `SyntaxError`. The function then throws `new Error("API error: ...")` for what should be a success response.  
**User impact:** DELETE operations and other empty-body responses fail silently.  
**Severity:** Low  
**Reproduction:** Call the deactivate user endpoint — it may return 200 with no body and crash.  
**Fix:** Handle empty response body:

```typescript
const text = await response.text()
if (!text) return undefined as T
return JSON.parse(text)
```

This is already present in the current code, but the `undefined as T` cast will cause runtime errors if the caller expects a specific type. Consider returning `null as unknown as T` or adding explicit handling.

---

### BUG-22: SlowAPI Rate Limiting Bypassed by Cookie Fallback

**File:** `backend/app/core/rate_limit.py` lines 45–51  
**How it occurs:** When no `X-Forwarded-For` header or `request.client.host` is available, the rate limiter falls back to a persistent `x-rate-id` cookie. But there's no code that *sets* this cookie — only code that *reads* it. Since the cookie is never set, the fallback always goes to `uuid.uuid4()`, generating a unique ID per request and effectively bypassing rate limiting entirely for anonymous clients.  
**User impact:** Rate limiting is completely ineffective for any request that doesn't have X-Forwarded-For (i.e., direct connections without a proxy).  
**Severity:** Low  
**Reproduction:** Send requests directly to the FastAPI server without a reverse proxy. Each request gets a unique rate limit key, so the limit is never reached.  
**Fix:** Set the `x-rate-id` cookie on the response when it doesn't exist:

```python
if not rate_id:
    rate_id = str(uuid.uuid4())
    response = request.scope.get("fastapi_response")
    if response:
        response.set_cookie(_RATE_LIMIT_COOKIE, rate_id, max_age=86400*30, httponly=True, samesite="lax")
    return rate_id
```

Also consider making the rate limiter use `request.client.host` as a more reliable fallback.

---

### BUG-23: `PromptManager` Instantiated Per-Request in Two Places

**File:** `backend/app/api/endpoints/scanner.py` lines 408–409  
**How it occurs:** While we fixed `ai.py` to use singletons, `scanner.py` at line 408-409 still creates `PromptManager()` and `LLMOutputParser()` per request in the `preview_fix` endpoint. This re-introduces the same issue that was fixed in `ai.py`.  
**User impact:** Unnecessary object creation and template re-loading per request.  
**Severity:** Low  
**Reproduction:** Call `/api/v1/scanner/{scan_id}/findings/{finding_id}/preview-fix` repeatedly.  
**Fix:** Import the module-level singletons from `ai.py`:

```python
from app.api.endpoints.ai import _prompt_manager, _output_parser
```

---

### BUG-24: Health Check Endpoint Writes to Cache

**File:** `backend/app/api/endpoints/admin.py` lines 188–195  
**How it occurs:** The `_check_redis()` function calls `prompt_cache.set()` and then `prompt_cache.get()` to verify cache works. This pollutes the cache with dummy `{"ok": True}` entries under key `prompt_cache:health:check:default` that never expire if the TTL is long. Over time, repeated health checks fill the Redis cache with junk data.  
**User impact:** Cache pollution; minor memory waste.  
**Severity:** Low  
**Reproduction:** Repeatedly call `GET /api/v1/admin/system/health`. Observe growing keys in Redis.  
**Fix:** Delete the test key after verification:

```python
await prompt_cache.set("health", "check", "default", {"ok": True}, ttl=10)
result = await prompt_cache.get("health", "check", "default")
# Delete immediately
# (add an invalidate method or use a separate health-check key namespace)
```

Or use `PING` command directly instead of write-then-read.

---

### BUG-25: `OllamaClient._get_client()` Creates New Client After Close

**File:** `backend/app/ai/ollama_client.py` lines 56–59  
**How it occurs:** If `self._client.is_closed` returns True (e.g., after a connection error), `_get_client()` creates a new `httpx.AsyncClient`. But the old closed client is never explicitly `await`-closed. httpx `AsyncClient` requires `await client.aclose()` for proper cleanup. Creating new clients without closing old ones leaks connection pools.  
**User impact:** Memory and connection pool leak over time.  
**Severity:** Low  
**Reproduction:** Trigger repeated Ollama connection errors. Each error creates a new client without closing the old one.  
**Fix:** Add an `aclose()` method or close the old client before creating a new one:

```python
async def _get_client(self) -> httpx.AsyncClient:
    if self._client is not None:
        if not self._client.is_closed:
            return self._client
        await self._client.aclose()
    self._client = httpx.AsyncClient(timeout=self.timeout)
    return self._client
```

---

### BUG-26: `scanStore.uploadFiles` Doesn't Use `apiFetch` — Inconsistent Error Handling

**File:** `frontend/src/store/scanStore.ts` lines 42–80  
**How it occurs:** `uploadFiles` uses raw `fetch()` instead of `apiFetch()` because it needs to send `FormData`. But this means it doesn't benefit from `apiFetch`'s error handling, auth cookie handling, or consistent error messages. The `unwrap()` call also expects `{ data: ... }` wrapping but the scanner endpoint returns `{ success, message, data: { ... } }` — if the `data` field contains `scan_id` directly (not wrapped in another `data`), the types won't match.  
**User impact:** Inconsistent error messages and potential type mismatches.  
**Severity:** Low  
**Reproduction:** Upload fails with a server error — different error format than other API calls.  
**Fix:** Add a `raw: true` option to `apiFetch` that skips JSON Content-Type header, or extract the FormData upload logic into a shared utility.

---

### BUG-27: JS AST Validation Uses `require()` in Node.js Script Without Safety Check

**File:** `backend/app/services/ast_validators.py` lines 78–100  
**How it occurs:** The `_validate_js_ast` method runs an inline Node.js script that `require("acorn")`. If `acorn` is not installed globally (which it won't be in the Docker container), the subprocess fails but returns a non-zero exit code. More importantly, the `code` parameter is piped to `stdin` without any escaping — if the code contains shell-like characters, it could potentially break the `node -e` command since it's passed via `input=code`. While `subprocess.run` with `input=` is safe from shell injection, the `node -e` script itself uses `process.stdin` which is fine, but the overall approach is fragile.  
**User impact:** JS validation silently fails in Docker where acorn isn't installed.  
**Severity:** Low (already has graceful fallback)  
**Reproduction:** Submit a JavaScript finding for fix generation in Docker.  
**Fix:** Bundle a standalone JS validation script in the project instead of requiring global `acorn`. Or use a pure-Python JS parser like `pyjsparser`.

---

### BUG-28: `ScanResultResponse.code_files` Type Mismatch

**File:** `backend/app/schemas/scanner.py` line 65  
**How it occurs:** The schema declares `code_files: Dict[str, str] = Field(default_factory=dict, description="file_path -> file_content")`, implying it maps file paths to full file contents. But in the endpoint (`scanner.py` lines 261-277), only metadata is returned (id, language, lines), not actual file content. The frontend's `scanStore.ts` stores this as `codeFiles: Record<string, string>`, expecting content strings but receiving metadata objects.  
**User impact:** TypeError when trying to display code file content in the frontend.  
**Severity:** Low  
**Reproduction:** View a completed scan's results — file content tabs are empty or show `[object Object]`.  
**Fix:** Change the schema to `Dict[str, Dict[str, Any]]` or create a separate route for on-demand file content (which already exists at `/{scan_id}/files/{file_id}/content`). Update the frontend type accordingly.

---

## SUMMARY TABLE

| ID | Severity | Category | Component | Brief Description |
|----|----------|----------|-----------|-------------------|
| BUG-01 | Critical | Race Condition | auth.py | TOCTOU in refresh token rotation |
| BUG-02 | Critical | Security | auth.py | Email enumeration via lockout error messages |
| BUG-03 | Critical | Security | admin.py | Unverified email change by admin |
| BUG-04 | High | SSRF | ollama_client.py | Ollama URL validation bypass via hex IPs |
| BUG-05 | High | Resource Exhaustion | scanner.py | Upload dirs never cleaned on task dispatch failure |
| BUG-06 | High | Resource Leak | container.py | Containers leak on spawn failure |
| BUG-07 | High | Concurrency | ai.py | Singleton thread-safety needs verification |
| BUG-08 | High | Memory Leak | scanStore.ts | Polling timers not properly cancelled on unmount |
| BUG-09 | High | Connection Leak | auth.py | Redis client never reconnects after failure |
| BUG-10 | High | Blocking | cache.py | Sync Redis client blocks async event loop |
| BUG-11 | Medium | Auth | auth.py | In-memory revocation not shared across workers |
| BUG-12 | Medium | Security | scanner.py | No rate limiting on upload endpoint |
| BUG-13 | Medium | Error Handling | scanStore.ts | JSON parse failure on non-JSON error responses |
| BUG-14 | Medium | Security | scan_tasks.py | Raw SQL architecture is fragile |
| BUG-15 | Medium | Security | config.py | CORS allows localhost in all environments |
| BUG-16 | Medium | Concurrency | container.py | Docker client init race condition |
| BUG-17 | Medium | Security | user.py | Password reset token stored in plaintext |
| BUG-18 | Low | Data Loss | api.ts | unwrap() discards pagination metadata |
| BUG-19 | Low | Logic | scanStore.ts | Poll max attempts too low for scanner timeout |
| BUG-20 | Low | Data Integrity | scan_tasks.py | All findings mapped to first file |
| BUG-21 | Low | Error Handling | api.ts | Empty response body crash |
| BUG-22 | Low | Security | rate_limit.py | Rate limiting bypassed by cookie fallback |
| BUG-23 | Low | Performance | scanner.py | Duplicate PromptManager per request |
| BUG-24 | Low | Cache | admin.py | Health check pollutes cache |
| BUG-25 | Low | Resource Leak | ollama_client.py | httpx client leak after connection error |
| BUG-26 | Low | Consistency | scanStore.ts | Inconsistent error handling vs apiFetch |
| BUG-27 | Low | Validation | ast_validators.py | JS AST validation broken in Docker |
| BUG-28 | Low | Type Safety | scanner.py | code_files type mismatch between schema and endpoint |

**Total: 28 issues (3 Critical, 7 High, 7 Medium, 11 Low)**