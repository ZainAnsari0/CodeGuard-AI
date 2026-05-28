# CodeGuard AI — Application Flow Document (AFD)

**Document Version:** 1.0  
**Date:** 2026-05-12  
**Status:** Final — Implementation Reference  
**Audience:** UI/UX Designers, Frontend Engineers, Backend Engineers, Product Managers, QA Engineers  

---

## 1. Product Flow Overview

### 1.1 Product Summary
CodeGuard AI is a privacy-first, AI-augmented static code vulnerability scanner that transforms opaque security warnings into plain-English explanations and one-click validated fixes. The application serves four distinct personas — Guests, Developers (Students), Instructors, and Admins — each with role-tailored navigation, permissions, and workflows.

### 1.2 Main User Goals
| User | Primary Goal |
|---|---|
| Guest | Evaluate the product via a zero-commitment demo scan without creating an account. |
| Developer / Student | Upload or paste code, receive an explainable vulnerability report, apply a validated fix, and share the report. |
| Instructor | Monitor class-wide security trends, review aggregated metrics, and provide targeted guidance to struggling students. |
| Admin | Maintain platform health, manage user accounts, monitor API usage, and ensure container runtime availability. |

### 1.3 Core Navigation Philosophy
- **Progressive Disclosure:** The interface reveals complexity only when needed. First-time users see a clean upload screen; advanced users can access history, filters, and exports.
- **Role-Aware Routing:** The URL space and sidebar dynamically reshape based on the authenticated role. A Developer sees "Scan History" and "Reports"; an Instructor sees "My Classes" and "Class Metrics"; an Admin sees "System Health" and "User Management."
- **Zero-Persistence Privacy Assurance:** Every flow involving code upload explicitly signals that source code is never stored. Visual indicators (shield icons, ephemeral badges) accompany every upload interaction.
- **Contextual Education:** Explanations are not buried in modals. The report screen is designed as a split-pane learning interface: vulnerable code on the left, AI explanation and fix on the right, with a deep-link to the Knowledge Base for deeper reading.

### 1.4 Application Structure
```
Landing Page
    ├── Guest Demo (ephemeral, no auth)
    ├── Login
    └── Register

Authenticated Shell (Role-Aware Sidebar + Header)
    ├── Dashboard (Home / Role-Specific Overview)
    ├── Scan
    │   ├── New Scan (Upload / Paste / Sample)
    │   └── Scan Progress (Real-time WebSocket / Polling)
    ├── Reports
    │   ├── Report Viewer (Interactive findings + diff viewer)
    │   ├── Scan History (List + trend charts)
    │   └── Shared Report (Public token-based view)
    ├── Instructor Panel (Instructor / Admin only)
    │   ├── Class List
    │   ├── Class Detail (Students + Metrics)
    │   └── Shared Student Reports
    ├── Admin Panel (Admin only)
    │   ├── User Management
    │   ├── System Health (Containers + API usage)
    │   └── System Event Logs
    ├── Knowledge Base (All authenticated + Guest)
    │   ├── Article List
    │   └── Article Detail (CWE-linked)
    └── Settings
        ├── Profile
        ├── Password
        └── Preferences
```

### 1.5 User Interaction Principles
- **Immediate Feedback:** Every user action triggers a visible system response within 200ms (button loading states, toast notifications, skeleton screens).
- **Undo / Reversible Actions:** Fix application is reversible via "Revert Fix" within the same session. Report sharing tokens can be revoked.
- **Fail Forward:** If the LLM is unavailable, the user sees a non-blocking warning banner and receives rule-based severity scores rather than a dead-end error screen.
- **Keyboard-First Accessibility:** All primary flows (upload, scan, navigate findings) are fully keyboard-navigable. The Monaco editor supports screen-reader-compatible code navigation.

---

## 2. User Roles

### 2.1 Guest User
- **Permissions:**
  - Browse the landing page and product value proposition.
  - Run a single demo scan using pre-loaded vulnerable sample code.
  - View the demo report in a read-only, session-scoped state.
  - Browse the Knowledge Base (read-only).
- **Restrictions:**
  - Cannot upload custom files or paste custom code.
  - Cannot apply fixes, save reports, or access scan history.
  - Cannot access Instructor or Admin panels.
  - Demo data is not persisted; refreshing the page clears the session.
- **Accessible Modules:** Landing Page, Guest Demo, Knowledge Base (read-only).
- **Navigation:** Top-level navbar only (no sidebar). Post-demo CTA prompts registration.

### 2.2 Developer / Student (Registered User)
- **Permissions:**
  - Upload `.py`, `.js`, or `.zip` files up to 10MB.
  - Paste code directly into the Monaco editor.
  - Run scans, view interactive reports, and apply validated fixes.
  - Access personal scan history with trend charts.
  - Export reports to PDF and JSON.
  - Generate shareable read-only report links.
  - Join instructor classes via join code.
- **Restrictions:**
  - Cannot view other users' scans unless shared.
  - Cannot access Instructor or Admin panels.
  - Cannot manage system settings or other user accounts.
- **Accessible Modules:** Dashboard, Scan, Reports, Scan History, Knowledge Base, Settings, Class Enrollment (as student).
- **Navigation:** Full sidebar with Developer-tier links.

### 2.3 Instructor
- **Permissions:**
  - All Developer permissions.
  - Create and manage classes.
  - Generate class join codes.
  - View class-wide aggregated vulnerability metrics (heatmaps, type distribution, average severity).
  - Filter metrics by vulnerability type, severity, and date range.
  - View read-only shared reports submitted by students.
- **Restrictions:**
  - Cannot apply fixes on behalf of students.
  - Cannot access Admin system health or user management.
- **Accessible Modules:** All Developer modules + Instructor Panel.
- **Navigation:** Sidebar includes "My Classes" and "Class Metrics" sections.

### 2.4 Admin (System Administrator)
- **Permissions:**
  - All Instructor permissions.
  - View, deactivate, and delete user accounts.
  - View real-time API usage metrics (LLM token burn, request counts).
  - Monitor Docker container health (active, idle, failed).
  - Browse and filter system event logs by type, date, and severity.
  - Manually revoke share tokens or cancel running scans.
- **Restrictions:**
  - Cannot directly modify scan findings or bypass AST validation.
- **Accessible Modules:** All modules + Admin Panel.
- **Navigation:** Sidebar includes "System Health," "User Management," and "Event Logs."

### 2.5 AI Agent / System
- **Role:** Non-human actor orchestrating scans, generating explanations, and validating fixes.
- **Permissions:**
  - Read code snippets inside ephemeral containers.
  - Call external LLM APIs using backend-provisioned keys.
  - Write anonymized report metadata and findings to PostgreSQL.
- **Restrictions:**
  - Never writes source code to persistent storage.
  - Cannot access user credentials or authentication tokens.
  - All outputs validated against Pydantic schemas before DB insertion.

---

## 3. Global Navigation Flow

### 3.1 Main Navigation Structure
- **Pre-Auth (Guest):** Horizontal top navbar with links: "Home," "Demo," "Knowledge Base," "Login," "Register."
- **Post-Auth:** Persistent left sidebar (240px desktop, collapsible to 72px icon-only) + fixed top header (64px) + content area.

### 3.2 Sidebar Behavior
- **Desktop:** Expanded by default. Collapsible via hamburger toggle or `Ctrl+B` shortcut. State persisted in `localStorage`.
- **Tablet:** Collapsed icon-only by default; expands to full on hover/focus.
- **Mobile:** Hidden by default; slides in from left as an overlay drawer with a scrim backdrop. Closes on outside click or route change.
- **Active State:** Current route highlighted with a left-border accent (4px) and subtle background tint. Nested items (e.g., under "Reports") show a chevron rotation animation.

### 3.3 Header Navigation
- **Left:** Sidebar toggle (mobile/tablet only), breadcrumb trail.
- **Center:** Global search bar (cmd/ctrl + K shortcut) with scoped search (users, scans, KB articles).
- **Right:**
  - Notification bell (dropdown with recent events).
  - Role badge chip (e.g., "Developer," "Instructor").
  - Avatar dropdown: Profile, Settings, Logout.
- **Admin Header Additions:** Real-time container health dot (green/yellow/red) linking to System Health.

### 3.4 Mobile Navigation
- **Bottom Tab Bar (optional for pure mobile experience):** Home, New Scan, History, Knowledge Base, Profile.
- **Gesture:** Swipe right from edge opens sidebar drawer.

### 3.5 Breadcrumb Flow
- Breadcrumbs appear below the header on all non-dashboard screens.
- Pattern: `Dashboard / Reports / Report Name` or `Dashboard / Instructor / Class Name / Metrics`
- Each breadcrumb segment is clickable (navigates to parent list view).
- Final segment (current page) is non-interactive and truncated if > 40 characters.

### 3.6 Deep Linking
- All screens support direct URL access.
- Auth-guarded deep links redirect unauthenticated users to `/login?redirect=/original/path`.
- Role-restricted deep links redirect unauthorized users to `/dashboard` with a "Insufficient permissions" toast.
- Shared report links (`/reports/share/:token`) are public and bypass auth entirely.

### 3.7 Navigation Hierarchy
```
📂 Dashboard (role-aware landing)
📂 Scan
   ├─ New Scan
   └─ Scan Progress (transient, auto-redirects on completion)
📂 Reports
   ├─ Scan History
   ├─ Report Viewer
   └─ Shared Report (public)
📂 Instructor (Instructor/Admin only)
   ├─ My Classes
   ├─ Class Detail
   └─ Class Metrics
📂 Admin (Admin only)
   ├─ User Management
   ├─ System Health
   └─ Event Logs
📂 Knowledge Base
   ├─ Articles
   └─ Article Detail
⚙️ Settings
   ├─ Profile
   ├─ Password
   └─ Preferences
```

---

## 4. Authentication Flow

### 4.1 Registration Flow
**Entry Point:** CTA buttons on landing page, post-demo prompt, or `/register` direct link.

**Step-by-Step:**
1. **Screen: Register Page**
   - User enters: Full Name, Email, Password, Confirm Password, Role (Developer / Instructor).
   - Frontend validation (Zod): email format, password strength (min 8, 1 uppercase, 1 number, 1 special char), matching passwords.
   - `POST /api/v1/auth/register`
2. **API: Backend Validation**
   - Check email uniqueness against PostgreSQL.
   - Hash password with bcrypt (cost 12).
   - Insert user record; assign role.
   - Return `201 Created` with user object (no tokens yet — optional email verification step if enabled).
3. **Screen: Registration Success**
   - Access token returned directly in response (auto-login).
   - Display welcome toast: "Account created. Welcome to CodeGuard AI!"
   - Auto-redirect to `/dashboard` (role-specific) immediately.
4. **API Response (Success):** `201 Created` — response includes `access_token` (JWT) and `user` object. Refresh token set as `httpOnly` cookie.
5. **Error States:**
   - `409 Conflict` (email exists): inline field error "An account with this email already exists."
   - `422 Validation Error`: inline field errors for password strength, missing fields.
   - `500 Server Error`: generic toast with retry option.

### 4.2 Login Flow
**Entry Point:** `/login`, post-registration redirect, or auth-guard redirect.

**Step-by-Step:**
1. **Screen: Login Page**
   - User enters Email and Password.
   - Frontend validation: required fields.
   - `POST /api/v1/auth/login`
2. **API: Authentication**
   - Retrieve user by email.
   - Check `locked_until`: if active, return `423 Locked` with message "Account locked for X minutes."
   - Verify bcrypt hash.
   - On failure: increment `failed_login_attempts`. If count reaches 3, set `locked_until = now() + 15 min`, send lockout email (async Celery task).
   - On success: reset `failed_login_attempts` to 0.
   - Generate RS256-signed access token (30 min) and refresh token (7 days).
   - Hash refresh token, store in PostgreSQL.
   - Return `200 OK` with access token in JSON body; refresh token set as `httpOnly`, `Secure`, `SameSite=Strict` cookie.
3. **Client Handling**
   - Store access token in Zustand state (memory only).
   - Decode JWT payload to extract role.
   - Redirect to role-specific dashboard (`/dashboard`).
4. **Error States:**
   - `401 Unauthorized`: "Invalid email or password." (ambiguous to prevent user enumeration).
   - `423 Locked`: Display countdown timer; disable submit button.
   - `429 Too Many Requests`: Display rate-limit message with `Retry-After` countdown.

### 4.3 Session Refresh Flow
**Trigger:** Access token expiry (30 min) or 401 response from any API call.

**Step-by-Step:**
1. Axios interceptor catches 401.
2. Silent `POST /api/v1/auth/refresh` sent with refresh token cookie.
3. Backend validates refresh token hash against PostgreSQL.
4. If valid: issue new access token (30 min); return `200 OK`.
5. If invalid/expired: return `401`; frontend clears state, deletes cookie (via `/auth/logout` call), redirects to `/login`.
6. **Concurrent Request Handling:** Queue all outgoing API calls during refresh; replay with new token once refresh succeeds.

### 4.4 Password Reset Flow
**Entry Point:** "Forgot password?" link on login page.

**Step-by-Step:**
1. **Screen: Forgot Password**
   - User enters email.
   - `POST /api/v1/auth/forgot-password`
2. **API:**
   - If email exists, generate cryptographically random 32-byte hex token; hash and store in Redis with 15-minute TTL.
   - Send email (async Celery) containing reset link: `/reset-password?token=xyz`.
   - Return `200 OK` regardless of whether email exists (prevent enumeration).
3. **Screen: Reset Password**
   - User clicks email link; frontend reads `token` from query param.
   - Backend validates token hash against Redis.
   - User enters new password + confirmation.
   - `POST /api/v1/auth/reset-password` with token and new password.
4. **API:**
   - Validate token; update bcrypt hash; invalidate all refresh tokens for user; delete reset token from Redis.
   - Return `200 OK`; redirect to `/login` with success message.
5. **Error States:**
   - Invalid/expired token: display "This password reset link has expired. Please request a new one."

### 4.5 Logout Flow
**Entry Point:** Avatar dropdown "Logout" action.

**Step-by-Step:**
1. User clicks Logout.
2. `POST /api/v1/auth/logout` with access token in header + refresh token cookie.
3. Backend deletes refresh token hash from PostgreSQL.
4. Frontend:
   - Clears access token from Zustand state.
   - Clears all React Query caches.
   - Redirects to `/login`.
5. **Edge Case:** If logout API fails (network error), frontend still clears local state and redirects. Backend token will naturally expire.

### 4.6 Session Expiration Flow
**Trigger:** User returns after >30 min inactivity; access token expired and refresh token also expired/revoked.

**Step-by-Step:**
1. Any API call returns 401.
2. Refresh attempt fails (401).
3. Frontend displays modal: "Your session has expired. Please log in again to continue."
4. Redirect to `/login?redirect=/current/path`.
5. Post-login, user is redirected back to original screen.

---

## 5. Onboarding Flow

### 5.1 First-Time User Experience
**Trigger:** First login after registration (detected via `is_first_login` flag or absence of scan history).

**Step-by-Step:**
1. **Screen: Welcome Modal**
   - Brief value proposition: "Upload your code. Get AI-powered explanations. Fix vulnerabilities in one click."
   - Dismissible "Don't show again" checkbox.
2. **Screen: Product Tour (Optional)**
   - Step 1: "This is your Dashboard." Highlights sidebar, header, and scan CTA.
   - Step 2: "Upload or paste code here." Highlights Monaco editor and file dropzone.
   - Step 3: "Your report appears here." Highlights severity heatmap and diff viewer.
   - Step 4: "Track your progress." Highlights scan history and trend charts.
   - Tour uses a floating spotlight overlay with Next/Skip buttons.
3. **Screen: Quick-Start CTA**
   - Dashboard shows a prominent "Run Your First Scan" card with a sample `.py` file pre-selected.
   - One-click "Scan Sample" runs a pre-loaded vulnerable snippet immediately to demonstrate the full loop.
4. **Completion:**
   - After first scan completes, a celebratory toast: "Your first scan is complete! You found 3 issues." with a link to the report.
   - `onboarding_completed` flag set in user profile (optional).

### 5.2 Preference Collection
- **Not explicitly required in Phase 1.** Future: theme preference (light/dark/system), default language filter, notification preferences.
- **Current:** Theme toggle available in header; preference persisted in `localStorage`.

### 5.3 Profile Setup
- User can update name and password via Settings > Profile.
- No mandatory profile completion gate.

---

## 6. Main Application Flow

### 6.1 Dashboard Access Flow
**Entry Point:** Post-login redirect or clicking the app logo.

**Step-by-Step:**
1. **API:** `GET /api/v1/dashboard` (or role-agnostic `GET /api/v1/me/scans?limit=5`)
2. **Screen: Dashboard (Role-Aware)**
   - **Developer:** Recent scans list (last 5), quick "New Scan" CTA, vulnerability trend sparkline (last 7 days), Knowledge Base recommendations based on recent findings.
   - **Instructor:** Class cards, quick "Create Class" CTA, class-wide vulnerability heatmap preview, recent shared student reports.
   - **Admin:** System health summary cards (active containers, API usage %, user count), critical system events list, quick links to Admin panels.
3. **Loading State:** Skeleton cards for metrics; shimmer rows for lists.
4. **Empty State (Developer):** "No scans yet. Upload your first file to get started." with a drag-and-drop illustration.

### 6.2 Feature Navigation Flow
- User clicks sidebar item or dashboard card.
- React Router transitions with a 200ms fade animation.
- Sidebar active state updates immediately.
- Breadcrumb trail updates to reflect new location.

### 6.3 CRUD Operations Flow (Scans)
**Create (Upload):**
1. User clicks "New Scan" or dashboard CTA.
2. Navigates to `/scan/new`.
3. Chooses upload method: drag-and-drop file, click to browse, or paste into Monaco editor.
4. Frontend validates file (extension, size <10MB) or detects language from Monaco mode.
5. `POST /api/v1/scans` with `multipart/form-data`.
6. Backend returns `202 Accepted` with `scan_id`, `queue_position`, `estimated_wait`.
7. Frontend transitions to Scan Progress screen.

**Read (View Report):**
1. Scan completes; user auto-redirected to `/scan/:scanId/report`.
2. `GET /api/v1/reports/:scanId`.
3. Report viewer renders severity heatmap, findings list, and Monaco diff viewer.

**Update (Apply Fix):**
1. User clicks a finding row; side panel expands with explanation and "Preview Fix" button.
2. User clicks "Preview Fix"; diff viewer renders original vs. suggested code.
3. User clicks "Apply Fix"; `POST /api/v1/scans/:id/findings/:findingId/apply-fix`.
4. Backend re-parses fix via AST validator.
5. On success: `fix_status` updated to `applied`; UI updates finding badge to green "Remediated".
6. On failure: toast error "Fix could not be validated. An alternative suggestion will be generated." Backend triggers a new LLM call for alternative fix.

**Re-scan After Fix (Post-Remediation):**
1. After applying one or more fixes, user clicks "Re-scan" button on the report page.
2. `POST /api/v1/scans/:id/rescan` triggers a new scan of the remediated code.
3. Backend creates a new scan record linked to the original scan (via `parent_scan_id` field).
4. Progress page shows re-scan status.
5. On completion: new report reflects updated vulnerability counts; trend chart shows improvement.

**Delete (Remove History):**
1. User clicks trash icon on scan history item.
2. Confirmation modal: "Delete this scan report? This action cannot be undone."
3. `DELETE /api/v1/scans/:scanId`.
4. Backend cascades delete to findings and report metadata.
5. UI removes item from list with a fade-out animation.

### 6.4 AI Interaction Flow
See Section 8 for full detail. Brief summary:
- User initiates scan -> AST parser runs -> flagged nodes sent to AI pipeline -> LLM returns explanation + fix -> AST re-validates fix -> results streamed to frontend via WebSocket or polling.

### 6.5 Search / Filter Operations
- **Global Search (Cmd/Ctrl + K):** Modal overlay with fuzzy search across scan filenames, KB article titles, and class names.
- **History Filter:** Scan history page has filter chips: Language (Python/JS), Severity (Low/Medium/High/Critical), Date Range. Filter state synced to URL query params (`?language=python&severity=high,critical`).
- **Instructor Metrics Filter:** Filter by vulnerability type, severity, date range. Backend aggregates via PostgreSQL `jsonb` containment queries.

### 6.6 Notifications Flow
- **In-App Toast System:**
  - Scan started: "Your scan is in progress. Estimated wait: 15s."
  - Scan completed: "Scan complete! 3 findings detected." (clickable, navigates to report).
  - Fix applied: "Fix applied and validated successfully."
  - Error: "Scan failed: Docker runtime unavailable." (with retry action).
- **Notification Center:** Dropdown in header showing last 20 events with timestamps. Mark-all-read and clear buttons.

### 6.7 Analytics Viewing Flow
- **Developer:** Trend chart on dashboard/history page. Clicking a data point filters history to that date range.
- **Instructor:** Class metrics page with Recharts bar chart (vulnerability type distribution) and line chart (severity trends over time).
- **Admin:** System Health page with real-time metric cards and Grafana-embedded iframe (future) or Recharts line charts for API usage and container counts.

### 6.8 Settings Management Flow
- **Profile:** Update full name. `PATCH /api/v1/auth/me`.
- **Password:** Current password required for change; new password must pass strength meter. `PATCH /api/v1/auth/me/password`.
- **Preferences:** Theme toggle (light/dark/system). Saved to `localStorage` + optional backend preference (future).

---

## 7. Screen-by-Screen Flow

### 7.1 Splash Screen / Landing Page
- **Purpose:** Product introduction, value proposition, and primary conversion funnel.
- **Accessible by:** All (public).
- **Entry Points:** Direct URL `/`, post-logout redirect.
- **Exit Points:** Login, Register, Guest Demo, Knowledge Base.
- **Components:**
  - Hero section with product tagline and animated code vulnerability visualization.
  - Feature grid (AI explanations, one-click fixes, privacy-first, educational dashboards).
  - Testimonials / use cases (Zara, Dr. Ahmed personas).
  - CTA cluster: "Get Started" (Register), "Try Demo" (Guest), "Learn More" (scroll to features).
- **User Actions:** Click CTAs, scroll, watch demo video (optional).
- **API Calls:** None.
- **Loading States:** Hero image lazy-loaded with blur placeholder.
- **Empty States:** N/A.
- **Error States:** N/A.

### 7.2 Login Page
- **Purpose:** Authenticate existing users.
- **Accessible by:** Unauthenticated users.
- **Entry Points:** `/login`, auth-guard redirects, registration success redirect.
- **Exit Points:** Dashboard (success), Register, Forgot Password, Landing Page.
- **Components:**
  - Email input (auto-focus on load).
  - Password input with visibility toggle.
  - "Remember me" checkbox (controls refresh token cookie persistence).
  - Submit button with loading spinner during API call.
  - Link to Register and Forgot Password.
- **User Actions:** Type credentials, toggle password visibility, submit form.
- **API Calls:** `POST /api/v1/auth/login`.
- **Validation Rules:** Email required and valid format; password required (min 8 chars).
- **Loading State:** Button shows spinner; inputs disabled.
- **Error States:**
  - Invalid credentials: inline error below password field.
  - Account locked: modal with countdown timer.
  - Rate limited: inline message with retry-after timer.

### 7.3 Register Page
- **Purpose:** Create a new account.
- **Accessible by:** Unauthenticated users.
- **Entry Points:** `/register`, landing page CTA, post-demo prompt.
- **Exit Points:** Login (success), Landing Page.
- **Components:**
  - Full Name, Email, Password, Confirm Password inputs.
  - Password strength meter (real-time: Weak/Fair/Strong/Excellent).
  - Role selection radio group: Developer / Instructor.
  - Terms of service checkbox.
  - Submit button.
- **User Actions:** Fill form, select role, submit.
- **API Calls:** `POST /api/v1/auth/register`.
- **Validation Rules:**
  - Email: valid format, not already registered (async debounced check optional).
  - Password: min 8, 1 uppercase, 1 lowercase, 1 number, 1 special char.
  - Confirm Password: must match.
- **Loading State:** Button spinner; inputs disabled.
- **Error States:**
  - Email exists: inline error with "Log in instead" link.
  - Password too weak: inline error with requirements list.
- **Success State:** Toast "Account created! Welcome to CodeGuard AI." + auto-redirect to Dashboard after 1 second (user is already authenticated via registration response token).

### 7.4 Dashboard
- **Purpose:** Role-specific command center and entry point to all primary workflows.
- **Accessible by:** Authenticated users (all roles).
- **Entry Points:** Post-login redirect, sidebar "Dashboard" click, breadcrumb root.
- **Exit Points:** All sub-modules via sidebar or dashboard cards.
- **Components (Developer):**
  - "New Scan" primary action card (large, colorful).
  - Recent Scans list (5 items) with severity badges, timestamp, and quick actions (view, share, delete).
  - Vulnerability Trend sparkline card (last 7 days).
  - Knowledge Base recommendation card ("You recently had SQL injection findings — read this article").
- **Components (Instructor):**
  - "Create Class" primary action card.
  - Class cards grid (name, student count, avg severity).
  - Class Metrics preview chart.
- **Components (Admin):**
  - System Health cards (container count, API usage, active users).
  - Critical Events list (last 5 system events with severity color coding).
- **User Actions:** Click cards, navigate via sidebar, use global search.
- **API Calls:** `GET /api/v1/dashboard` (or aggregated calls to scans/classes/metrics).
- **Loading State:** Skeleton screens for all cards and lists.
- **Empty State (Developer):** "No scans yet" illustration + "Upload Code" button.
- **Error State:** "Failed to load dashboard" retry button.

### 7.5 New Scan Page
- **Purpose:** Initiate a new vulnerability scan.
- **Accessible by:** Developers, Instructors, Admins (Guests limited to Demo).
- **Entry Points:** Dashboard CTA, sidebar "New Scan," `/scan/new`.
- **Exit Points:** Scan Progress (`/scan/:id/progress`), Dashboard.
- **Components:**
  - Tab switcher: Upload File | Paste Code.
  - **Upload Tab:** Drag-and-drop zone with file type icons (.py, .js, .zip). File list preview with remove button. Max size badge (10MB).
  - **Paste Tab:** Monaco Editor instance with language mode selector (Python/JS). Line numbers enabled. Sample code snippet button for quick testing.
  - "Start Scan" primary button (disabled until valid input provided).
  - Privacy assurance banner: "Your code is analyzed in an ephemeral container and never stored." with shield icon.
- **User Actions:** Drag file, click to browse, paste code, switch language mode, click "Start Scan."
- **API Calls:** `POST /api/v1/scans` (multipart for upload; JSON for paste).
- **Validation Rules:**
  - File: extension in `.py`, `.js`, `.zip`; size <= 10MB.
  - Paste: non-empty string; language explicitly selected or auto-detected.
- **Loading State:** "Start Scan" button shows spinner; upload progress bar if file is large.
- **Error States:**
  - Invalid file type: inline dropzone error with accepted formats.
  - File too large: inline error "Maximum file size is 10MB."
  - Server error: toast with retry option.
- **Success State:** Redirect to Scan Progress with `scanId`.

### 7.6 Scan Progress Page
- **Purpose:** Real-time feedback on scan execution.
- **Accessible by:** Scan owner, Admins.
- **Entry Points:** Auto-redirect from New Scan, direct link `/scan/:id/progress`.
- **Exit Points:** Report Viewer (on completion), Dashboard (on cancel).
- **Components:**
  - Progress stepper: Queue -> Container Spawn -> AST Parsing -> AI Analysis -> Fix Validation -> Complete.
  - Animated progress bar with percentage.
  - Status text: "Analyzing syntax tree... (40%)"
  - Live log stream (collapsible, for power users): "Container spawned: abcd1234", "Found 3 risky nodes", "LLM enrichment in progress..."
  - "Cancel Scan" button (available until "AI Analysis" stage).
  - Estimated wait timer.
- **User Actions:** Watch progress, expand logs, cancel scan.
- **API Calls:**
  - WebSocket connection: `wss://api/v1/ws/scans/:scanId` (primary).
  - Fallback polling: `GET /api/v1/scans/:id/status` every 2 seconds.
  - Cancel: `POST /api/v1/scans/:id/cancel`.
- **Loading State:** Active progress animation.
- **Error States:**
  - Scan failure: stepper turns red at failed stage; detailed error message displayed ("AST parser failed: invalid syntax at line 42"); "Retry" button.
  - Docker unavailable: specific message "Scan engine temporarily offline. Please try again later."
- **Success State:** Auto-redirect to Report Viewer after 1-second completion pause.

### 7.7 Report Viewer Page
- **Purpose:** Interactive security report — the core product differentiator.
- **Accessible by:** Scan owner, Admins, anyone with share token.
- **Entry Points:** Auto-redirect from Scan Progress, history list click, shared link, `/reports/:scanId`.
- **Exit Points:** Scan History, Dashboard, Export (PDF/JSON), Share, Knowledge Base (via CWE links).
- **Components:**
  - **Header:** Filename, language badge, LOC count, severity summary chips (Critical/High/Medium/Low counts), action buttons (Export PDF, Export JSON, Share, Back).
  - **Left Pane (Code View):** Monaco editor in read-only mode. Vulnerable lines highlighted with colored gutter markers (red = Critical, orange = High, yellow = Medium, blue = Low). Hovering a marker shows a tooltip with CWE and severity.
  - **Right Pane (Findings Panel):**
    - Collapsible findings list sorted by severity (Critical first).
    - Each finding card: CWE badge, severity badge, confidence %, line range, vulnerability type.
    - Clicking a finding scrolls code view to the relevant lines and expands the finding detail.
    - **Finding Detail:**
      - AI Explanation (plain English, educational tone).
      - "Why this is risky" and "Impact" subsections.
      - "Preview Fix" button -> opens diff viewer.
      - "Apply Fix" button (disabled if `ast_validated = false`).
      - "View in Knowledge Base" link (deep-link to relevant CWE article).
  - **Diff Viewer (Modal / Inline):**
    - Side-by-side original vs. suggested code.
    - Syntax highlighting.
    - "Apply Fix" and "Reject" buttons.
  - **Severity Heatmap:** Mini-map of the file showing vulnerability density per line region.
- **User Actions:** Click findings, hover code markers, preview/apply fixes, export, share, navigate to KB.
- **API Calls:** `GET /api/v1/reports/:scanId` (initial load); `POST /api/v1/scans/:id/findings/:findingId/apply-fix`; `GET /api/v1/scans/:id/findings/:findingId/preview-fix`.
- **Loading State:** Skeleton code editor + shimmer findings list.
- **Empty State:** "No vulnerabilities found! Great job." with celebration illustration.
- **Error States:**
  - Report not found: 404 page with "This report may have been deleted or the link is invalid."
  - Unauthorized: 403 modal.

### 7.8 Scan History Page
- **Purpose:** Paginated list of all past scans with trend analytics.
- **Accessible by:** Developers, Instructors, Admins (own history + students' shared reports for instructors).
- **Entry Points:** Sidebar "History," Dashboard "View All" link, `/history`.
- **Exit Points:** Report Viewer, Dashboard.
- **Components:**
  - Filter bar: Language dropdown, Severity multi-select, Date range picker.
  - Trend chart: Line chart of findings over time (grouped by severity).
  - Scan cards/table rows: Filename, date, language, total findings, severity breakdown, actions (View, Share, Delete).
  - Pagination: Cursor-based "Load More" button or numbered pages.
- **User Actions:** Filter, sort, paginate, click scan to view, share, delete.
- **API Calls:** `GET /api/v1/users/me/scans` with query params for filters.
- **Loading State:** Skeleton table rows.
- **Empty State:** "No scan history yet. Run your first scan to see it here."
- **Error State:** "Failed to load history. Retry?"

### 7.9 Shared Report (Public View)
- **Purpose:** Read-only report accessible via token without authentication.
- **Accessible by:** Anyone with the link (public).
- **Entry Points:** Direct link `/reports/share/:token`.
- **Exit Points:** Login/Register CTA ("Sign up to run your own scans"), Knowledge Base.
- **Components:**
  - Simplified Report Viewer (same components as authenticated view but without "Apply Fix" button).
  - Watermark/header: "Shared Report — Read Only" with original owner name and scan date.
  - Floating banner at bottom: "Want to scan your own code? Register for free." with dismiss button.
- **User Actions:** Read findings, view code highlights, navigate to KB articles, click CTA to register.
- **API Calls:** `GET /api/v1/reports/share/:token`.
- **Loading State:** Skeleton.
- **Error State:** "This shared link has expired or been revoked." if token invalid.

### 7.10 Instructor Panel — Class List
- **Purpose:** Manage classes and view aggregated metrics.
- **Accessible by:** Instructors, Admins.
- **Entry Points:** Sidebar "My Classes," Dashboard card.
- **Exit Points:** Class Detail, Dashboard.
- **Components:**
  - "Create Class" modal (name input, auto-generated join code).
  - Class cards: Name, join code (with copy button), student count, avg severity, last activity.
  - Quick action: View Metrics, Manage Students, Delete Class.
- **User Actions:** Create class, copy join code, click class to view detail, delete class.
- **API Calls:** `GET /api/v1/instructor/classes`, `POST /api/v1/instructor/classes`, `DELETE /api/v1/instructor/classes/:id`.
- **Loading State:** Skeleton cards.
- **Empty State:** "No classes yet. Create your first class to get started."

### 7.11 Instructor Panel — Class Detail / Metrics
- **Purpose:** Deep-dive into a single class's security posture.
- **Accessible by:** Instructors, Admins.
- **Entry Points:** Class List click, `/instructor/classes/:id`.
- **Exit Points:** Class List, Shared Student Reports.
- **Components:**
  - Class info header: Name, join code, student list (avatars + names).
  - Metrics dashboard:
    - Vulnerability type distribution (horizontal bar chart).
    - Average severity trend over time (line chart).
    - Most common issues table (ranked by frequency across all student scans).
  - Filters: Vulnerability type, severity, date range.
  - Student submissions list: Student name, latest scan date, findings count, quick link to shared report.
- **User Actions:** Apply filters, click student report, view charts.
- **API Calls:** `GET /api/v1/instructor/classes/:id/metrics`, `GET /api/v1/instructor/classes/:id/students`, `GET /api/v1/instructor/classes/:id/reports`.
- **Loading State:** Skeleton charts and tables.
- **Empty State:** "No student submissions yet. Share the join code with your students."

### 7.12 Admin Panel — User Management
- **Purpose:** CRUD operations on user accounts.
- **Accessible by:** Admins only.
- **Entry Points:** Sidebar "Users," `/admin/users`.
- **Exit Points:** Admin Dashboard.
- **Components:**
  - Search/filter bar: Name/email search, role filter, status filter.
  - User table: Avatar, name, email, role, status (active/locked/deactivated), created date, actions (View, Deactivate, Delete).
  - Bulk actions: Deactivate selected, export CSV.
- **User Actions:** Search, filter, deactivate/activate user, delete user (with confirmation), paginate.
- **API Calls:** `GET /api/v1/admin/users`, `PATCH /api/v1/admin/users/:id`, `DELETE /api/v1/admin/users/:id`.
- **Loading State:** Skeleton table.
- **Empty State:** "No users found."
- **Error State:** "Failed to update user status. Retry?"

### 7.13 Admin Panel — System Health
- **Purpose:** Real-time operational monitoring.
- **Accessible by:** Admins only.
- **Entry Points:** Sidebar "System Health," `/admin/system/health`.
- **Exit Points:** Event Logs.
- **Components:**
  - Metric cards: Active containers, idle containers, failed containers (last hour), API requests/min, LLM token usage today.
  - Live-updating charts: Container state transitions, API latency percentiles.
  - LLM provider status: OpenAI (green/red), Groq (green/red), Ollama (green/red).
  - Action buttons: "Purge Orphaned Containers," "Clear Rate Limit Cache."
- **User Actions:** Refresh metrics, click chart data points, trigger admin actions.
- **API Calls:** `GET /api/v1/admin/system/health`, `GET /api/v1/admin/system/metrics`, `POST /api/v1/admin/system/purge-containers`.
- **Loading State:** Skeleton cards; charts show "Loading..."
- **Error State:** "Metrics unavailable. Check system connectivity."

### 7.14 Admin Panel — System Event Logs
- **Purpose:** Audit trail and debugging.
- **Accessible by:** Admins only.
- **Entry Points:** Sidebar "Event Logs," `/admin/system/events`.
- **Exit Points:** N/A.
- **Components:**
  - Filter bar: Event type dropdown, severity multi-select, date range, user search.
  - Event table: Timestamp, event type, severity (color-coded), user, message, metadata JSON (collapsible).
  - Pagination.
- **User Actions:** Filter, expand metadata, paginate, export logs.
- **API Calls:** `GET /api/v1/admin/system/events`.

### 7.15 Knowledge Base Page
- **Purpose:** Educational resource for vulnerability learning.
- **Accessible by:** All authenticated users + Guests (read-only).
- **Entry Points:** Sidebar "Knowledge Base," report CWE deep-links, `/kb`.
- **Exit Points:** Report Viewer (back link), Dashboard.
- **Components:**
  - Article grid/list: Title, CWE badges, OWASP category, short description.
  - Search bar: Full-text search across article content.
  - Category filters: SQL Injection, XSS, Hardcoded Secrets, etc.
- **Article Detail:**
  - Markdown-rendered content.
  - Vulnerable code example (syntax highlighted, non-executable).
  - Safe code example.
  - Related CWE references.
  - "Back to Reports" breadcrumb if accessed from a finding.
- **API Calls:** `GET /api/v1/kb`, `GET /api/v1/kb/:slug`, `GET /api/v1/kb/search?q=...`.
- **Loading State:** Skeleton cards / article shimmer.
- **Empty State (Search):** "No articles found for 'X'. Try a different search term."

### 7.16 Guest Demo Page
- **Purpose:** Zero-commitment product trial.
- **Accessible by:** Guests (public).
- **Entry Points:** Landing page "Try Demo," `/demo`.
- **Exit Points:** Register page (CTA), Landing Page.
- **Components:**
  - Sample code selector: Dropdown of pre-loaded vulnerable snippets (SQLi, XSS, Hardcoded Secrets, Unsafe Eval).
  - Monaco editor displaying selected sample (read-only for guest).
  - "Run Demo Scan" button.
  - Privacy note: "Demo scans use synthetic code only."
- **User Actions:** Select sample, run scan, view results.
- **API Calls:** `GET /api/v1/demo/samples`, `POST /api/v1/demo/scan`.
- **Loading State:** Same as Scan Progress.
- **Success State:** Simplified Report Viewer (no apply fix, no export, no share). "Create an account to unlock all features" banner.
- **Error State:** "Demo temporarily unavailable. Please try again later."

### 7.17 Settings — Profile Page
- **Purpose:** Manage user profile.
- **Accessible by:** Authenticated users.
- **Entry Points:** Avatar dropdown "Profile," `/settings/profile`.
- **Exit Points:** Settings sidebar items.
- **Components:**
  - Editable form: Full Name, Email (read-only or verified-only change), Avatar upload (optional).
  - Save button.
- **API Calls:** `GET /api/v1/auth/me`, `PATCH /api/v1/auth/me`.
- **Validation:** Name min 2 chars.
- **Success State:** Toast "Profile updated."

### 7.18 Settings — Password Page
- **Purpose:** Update password.
- **Accessible by:** Authenticated users.
- **Components:** Current password, New password, Confirm new password.
- **Validation:** New password must pass strength meter; must differ from current.
- **API Calls:** `PATCH /api/v1/auth/me/password`.
- **Success State:** Toast "Password updated. Please log in again." -> logout redirect.

### 7.19 Error Pages
- **404 Not Found:** Friendly illustration, "This page doesn't exist," link to Dashboard.
- **403 Forbidden:** "You don't have permission to access this page." Link to Dashboard.
- **500 Internal Server Error:** "Something went wrong on our end. Our team has been notified." Retry button.
- **Offline / Network Error:** "You appear to be offline. Some features may be unavailable." Banner at top of page; cached data displayed if available.

---

## 8. AI Interaction Flow

### 8.1 User Prompt Lifecycle (Scan Initiation)
The user does not directly "prompt" the AI. Instead, the AI pipeline is triggered deterministically by the scan engine. The flow is:

1. **User Uploads/Pastes Code** -> `POST /api/v1/scans` -> Backend accepts file/snippet.
2. **Scan Orchestrator (Celery Task)** begins:
   - `stage: container_spawn` — Spin up ephemeral Docker container.
   - `stage: ast_parsing` — Parse code with `ast` (Python) or `acorn` (JS).
3. **Flagged Nodes Detected** — AST parser returns risky nodes with line numbers, context, and CWE mappings.
4. **AI Pipeline Triggered** — For each flagged node (or batched by CWE type):
   - **Prompt Construction (LangChain):**
     - Template loaded from version-controlled Jinja2 file.
     - Variables injected: `language`, `code_snippet`, `vulnerability_type`, `cwe_id`, `line_start`, `line_end`.
     - Delimiter wrapping prevents prompt injection: user code is treated as data, never as instruction.
   - **Cache Check:** Redis queried with SHA-256 hash of `(prompt_template_version + code_snippet_hash + cwe_id)`. If hit, return cached response.
   - **LLM Call (Async HTTP):**
     - Primary: `POST https://api.openai.com/v1/chat/completions` (or Groq).
     - Timeout: 15 seconds.
     - Structured output enforced via JSON schema in prompt + Pydantic parser.
   - **Fallback Chain:**
     - If cloud timeout/rate-limit -> call local Ollama (`POST http://ollama:11434/api/generate`).
     - If Ollama unavailable -> rule-based fallback (cached generic explanation + heuristic severity).
5. **Response Parsing:**
   - LLM returns JSON: `{ "explanation": "...", "severity": "high", "confidence_percent": 94, "suggested_fix": "..." }`.
   - Pydantic model `AIExplanationResponse` validates schema.
   - If parse fails: retry once; if still invalid, use rule-based fallback.
6. **Fix Validation (AST Re-validation):**
   - `suggested_fix` is parsed through the same AST parser for the target language.
   - If syntactically valid: `ast_validated = true`.
   - If invalid: request alternative fix from LLM (max 2 attempts); if still invalid, discard fix and set `suggested_fix = null`.
7. **Container Teardown:** Source code deleted; container destroyed.
8. **Database Write:** Anonymized findings inserted into PostgreSQL.
9. **Frontend Update:** WebSocket pushes `stage: completed` + report data; frontend redirects to Report Viewer.

### 8.2 Context Management
- **No Cross-Scan Memory:** Each LLM call is stateless. Only the current vulnerable snippet + minimal surrounding context (±3 lines) is sent.
- **Prompt Caching:** Redis stores successful prompt/response pairs for 24 hours. This speeds up repeated scans of common patterns (e.g., basic SQLi in student assignments) and reduces API costs.
- **No User PII in Prompts:** LLM never receives user email, name, or file paths.

### 8.3 Streaming Responses
- **Future Enhancement:** If the provider supports SSE (Server-Sent Events), the explanation can be streamed token-by-token to the frontend, reducing perceived latency.
- **Phase 1:** Entire response awaited before display; acceptable given short explanations (target <200 tokens).

### 8.4 AI Moderation Flow
- **Input Sanitization:** Before sending to LLM, code snippet is stripped of any non-printable characters and truncated to max 500 lines. If the full file is >500 lines, only the vulnerable function block is sent.
- **Output Sanitization:** LLM output parsed through Pydantic; any output attempting to inject HTML/JS/markdown scripts is rejected. Explanations rendered as plain text or Markdown with DOMPurify-equivalent sanitization.
- **Token Abuse Prevention:** Per-user daily token quota enforced at backend. If exceeded, user is notified and Ollama/local fallback is enforced.

### 8.5 Retry / Fallback Logic
```
Cloud LLM Request
  ├─ Success (200) -> Parse JSON -> Validate Schema -> Success
  ├─ Timeout / 429 / 5xx -> Log Warning -> Ollama Request
  │   ├─ Success -> Parse/Validate -> Success
  │   └─ Timeout / Unavailable -> Log Warning -> Rule-Based Fallback
  │       └─ Return cached generic explanation + heuristic severity
  └─ Parse Error -> Retry Once -> If still error -> Rule-Based Fallback
```

### 8.6 AI Analytics Tracking
- Every LLM call logged to `system_events`:
  - `event_type: "llm_request"`, `provider: "openai"/"groq"/"ollama"`, `tokens_used`, `latency_ms`, `status: "success"/"fallback"/"error"`.
- Admin dashboard surfaces: daily token burn, average latency per provider, fallback rate.

---

## 9. Admin Flow

### 9.1 User Management Flow
1. Admin navigates to Admin Panel -> Users.
2. System loads paginated user list (`GET /api/v1/admin/users`).
3. Admin searches by name/email; filters by role or status.
4. Admin clicks "Deactivate" on a user.
5. Confirmation modal: "Deactivate Zara Ali? They will be unable to log in."
6. `PATCH /api/v1/admin/users/:id` with `{ "is_active": false }`.
7. Backend: update user record; revoke all refresh tokens; broadcast logout to active sessions (via Redis pub/sub or short token expiry).
8. UI: user row greyed out; status badge updated to "Deactivated"; toast "User deactivated."
9. Admin can "Reactivate" with the same flow in reverse.

### 9.2 Content Moderation Flow
- **Phase 1:** Limited to scan report metadata. No user-generated content beyond code snippets (which are ephemeral).
- **Future:** If community features (shared code snippets, forums) are added, admin flow includes:
  - Flagged content queue.
  - Review and approve/reject actions.
  - Automated moderation via LLM toxicity classifier.

### 9.3 System Monitoring Flow
1. Admin opens System Health.
2. Frontend establishes WebSocket or polling connection for real-time metrics.
3. Live updates stream: container counts, API request rate, LLM latency.
4. Admin observes anomaly (e.g., spike in failed containers).
5. Admin clicks into Event Logs, filters by `event_type: "container_failure"`.
6. Admin identifies pattern; clicks "Purge Orphaned Containers."
7. Backend executes cleanup; logs action to `system_events`.
8. UI refreshes metrics; toast "X orphaned containers purged."

### 9.4 Role Management Flow
- **Phase 1:** Role assigned at registration and fixed. Admins can manually promote/demote users via `PATCH /api/v1/admin/users/:id` with `{ "role": "instructor" }`.
- **Future:** Granular permission matrix with custom roles.

### 9.5 Reports Management Flow
- Admin can view any user's scan report (override ownership check).
- Admin can revoke share tokens: `DELETE /api/v1/admin/reports/:scanId/share`.
- Admin can cancel any running scan: `POST /api/v1/admin/scans/:id/cancel`.

---

## 10. Notification Flow

### 10.1 In-App Notifications
- **Toast System:** Ephemeral pop-ups at bottom-right (desktop) or top-center (mobile).
  - Types: Success (green), Info (blue), Warning (yellow), Error (red).
  - Duration: 4 seconds auto-dismiss; errors persist until manually dismissed.
  - Actionable toasts: "Scan complete" with "View Report" button.
- **Notification Center:** Dropdown in header showing last 20 events.
  - Events: Scan started, scan completed, fix applied, account locked, password changed.
  - Mark-all-read button clears unread badges.
  - Clicking an event navigates to relevant screen.

### 10.2 Email Notifications
- **Account Lockout:** "Your account has been locked for 15 minutes due to 3 failed login attempts."
- **Password Reset:** "Click here to reset your password. Link expires in 15 minutes."
- **Welcome Email:** "Welcome to CodeGuard AI. Start your first scan." (optional, post-registration).
- **Implementation:** Celery async task dispatched to email provider (SendGrid/AWS SES or SMTP fallback).

### 10.3 Real-Time Alerts
- **WebSocket Push Events:**
  - `scan.completed` — triggers toast + notification center entry.
  - `scan.failed` — triggers error toast.
  - `fix.applied` — triggers success toast.
- **Admin Alerts:**
  - `container.failed` — triggers warning toast + event log entry.
  - `llm.fallback_activated` — info toast if fallback rate exceeds threshold.

### 10.4 Notification Preferences (Future)
- Settings page allows users to toggle: Email notifications (on/off), In-app toasts (on/off), Scan completion sound (on/off).
- Phase 1: all notifications enabled by default; no granular preferences.

---

## 11. Payment Flow

### 11.1 Applicability
- **Phase 1:** CodeGuard AI is free/open-core for academic use. No payment flow implemented.
- **Future:** If transitioning to SaaS, the following flow is pre-designed:

### 11.2 Subscription Flow (Future)
1. User clicks "Upgrade to Pro" in header or settings.
2. Screen: Plan comparison (Free vs. Pro vs. Enterprise).
3. User selects plan; clicks "Subscribe."
4. Stripe Checkout session created (`POST /api/v1/billing/checkout`).
5. Redirect to Stripe hosted checkout page.
6. Payment success -> Stripe webhook `checkout.session.completed` -> backend activates subscription, updates `users.subscription_tier`.
7. Frontend webhook handler (or polling) detects activation -> toast "Welcome to Pro!" -> unlock premium features (higher scan limits, CI/CD integration).

### 11.3 Failed Payment / Cancellation
- Stripe webhook `invoice.payment_failed` -> backend sets `subscription_status = "past_due"`.
- Email notification sent to user.
- Grace period of 7 days before downgrading to Free tier.

---

## 12. Search & Filter Flow

### 12.1 Search Lifecycle
1. **Trigger:** User presses `Cmd/Ctrl + K` or clicks search bar in header.
2. **Input:** Search modal appears with auto-focused input.
3. **Debounced Query:** Input debounced at 150ms.
4. **API:** `GET /api/v1/search?q=query&scope=all` (or scoped to scans/kb/users).
5. **Results Grouped by Category:**
   - Scans: "app.py — 3 findings, 2026-05-10"
   - KB Articles: "SQL Injection (CWE-89)"
   - Users: "Zara Ali (Developer)" (admin-only)
6. **Navigation:** Clicking a result navigates directly to the target screen and closes modal.
7. **Empty State:** "No results for 'X'. Try different keywords."

### 12.2 Filter Application
1. User clicks filter chip/button on list screens (History, Instructor Metrics, Admin Events).
2. Filter panel slides in from right (desktop) or opens as bottom sheet (mobile).
3. User selects filters; "Apply" button enabled.
4. Clicking "Apply" updates URL query params (`?severity=high,critical&language=python`).
5. React Query refetches data with new params.
6. Active filters shown as removable chips below the filter bar.

### 12.3 Sorting
- History page: sort by Date (default, newest first), Findings Count (desc/asc), Filename (A-Z).
- Sort state persisted in URL (`?sort=-created_at`).

### 12.4 Pagination
- **Cursor-Based (Recommended):** "Load More" button at bottom of list. Next page fetched via `?cursor=last_item_id`.
- **Numbered (Alternative):** Standard page numbers for admin tables where jump-to-page is useful.
- **Infinite Scroll:** Optional for mobile scan history (intersection observer triggers fetch).

---

## 13. File & Media Flow

### 13.1 Upload Process
1. User drags file onto dropzone or clicks to browse.
2. **Client Validation:**
   - File extension check against whitelist `.py`, `.js`, `.zip`.
   - File size check against `MAX_FILE_SIZE_MB` (10MB).
3. **Preview:** File name and size displayed in a chip with remove button.
4. **Upload:** `POST /api/v1/scans` with `multipart/form-data`.
5. **Server Validation:**
   - `python-magic` verifies actual file content matches extension.
   - ZIP files: inspected for path traversal attempts, symlinks, nested archives, zip bombs (compression ratio check).
6. **Processing:** File streamed into ephemeral container tmpfs; never written to persistent disk.

### 13.2 Validation Rules
- Extensions: `.py`, `.js`, `.zip` only.
- Max size: 10,485,760 bytes (10 MB).
- ZIP contents: max 100 files, max total uncompressed size 50MB.
- Rejected types: executables, binaries, encrypted archives.

### 13.3 Compression & Storage
- No client-side compression.
- Server-side: file exists only in container tmpfs; no persistent storage.
- Report exports (PDF/JSON): generated on-demand, stored in temporary cache (Redis/S3 presigned URL) for 1 hour, then auto-deleted.

### 13.4 Preview & Deletion
- **Preview:** Monaco editor renders uploaded file content for user confirmation before scan (optional step).
- **Deletion:** Removing a file from the dropzone simply clears the client state. Since no persistent storage exists, no server deletion needed.

### 13.5 Security Handling
- All file I/O happens inside ephemeral containers with no network egress and non-root user privileges.
- `tmpfs` mount size-limited to prevent container memory exhaustion.
- `seccomp` and `AppArmor` profiles restrict container syscalls (future hardening).

---

## 14. Error Handling Flow

### 14.1 Network Errors
- **Detection:** Axios interceptor catches `navigator.onLine === false` or request timeout (>30s).
- **UI:** Sticky banner at top: "You appear to be offline. Some features may be unavailable."
- **Behavior:**
  - React Query retries failed requests with exponential backoff (1s, 2s, 4s, 8s).
  - Cached data displayed if available (stale-while-revalidate strategy).
  - Mutations (e.g., apply fix) queued and replayed when connection restored (optional optimistic UI).
- **Recovery:** Banner auto-dismisses when `online` event fires and a health check ping succeeds.

### 14.2 Validation Errors
- **Client-Side:** Zod schemas validate forms before submission. Errors displayed inline next to fields with red border + helper text.
- **Server-Side:** FastAPI returns `422 Unprocessable Entity` with structured `detail` array. Frontend maps each detail to corresponding field.
- **Pattern:** Never display raw server error messages to users unless they are human-readable. Map technical codes to friendly strings via an error dictionary.

### 14.3 Authentication Failures
- **401 Unauthorized:**
  - If refresh token valid: silently refresh and retry original request.
  - If refresh fails: show session expiry modal; redirect to `/login?redirect=currentPath`.
- **403 Forbidden:** Toast "You don't have permission to access this." User remains on current page or redirected to Dashboard.
- **423 Locked:** Modal with countdown timer; disable all authenticated actions.

### 14.4 AI Failures
- **LLM Timeout:** Backend returns scan report with rule-based fallback severity + cached generic explanation. Frontend shows non-blocking banner: "AI explanations temporarily unavailable. Severity scores are rule-based. Retry scan later for AI insights."
- **AST Parse Failure:** Scan marked as `failed`. Frontend shows error with specific line number and syntax error description. User can fix syntax and re-upload.
- **Fix Validation Failure:** Fix not applied. Toast: "The suggested fix could not be validated. An alternative has been requested." If alternative also fails, finding shows "No automated fix available — see Knowledge Base for manual guidance."

### 14.5 Server Errors (5xx)
- **Generic:** Toast "Something went wrong on our end. Our team has been notified." with a "Retry" button.
- **Specific:**
  - `502 Bad Gateway` (nginx -> API down): "The application is temporarily unavailable. Please refresh in a moment."
  - `503 Service Unavailable` (maintenance): "CodeGuard AI is under maintenance. We'll be back shortly."

### 14.6 Error Recovery Logic
- **Retry with Exponential Backoff:** All idempotent GET requests retry automatically. Mutations (POST/PUT/PATCH) require explicit user retry.
- **Graceful Degradation Matrix:**
  | Failure | UX Degradation |
  |---|---|
  | LLM API down | Rule-based scoring + cached explanations |
  | DB timeout | Cached report served with stale timestamp |
  | Docker down | Scan disabled; user sees maintenance banner |
  | Redis down | Synchronous request handling; no real-time updates |

---

## 15. Real-Time Flow

### 15.1 WebSocket Lifecycle
1. **Connection:** On scan initiation, frontend opens WebSocket `wss://api/v1/ws/scans/:scanId` with access token in query param.
2. **Auth Handshake:** Backend validates JWT from query param before accepting connection. If invalid, close with `1008 Policy Violation`.
3. **Event Streaming:** Backend pushes JSON events:
   ```json
   { "type": "stage_update", "stage": "ast_parsing", "progress": 40, "message": "Analyzing syntax tree..." }
   ```
4. **Client Handling:**
   - Update progress stepper and bar.
   - Append to live log stream (if expanded).
   - On `type: "completed"`, close WebSocket and redirect to Report Viewer.
   - On `type: "error"`, display error state and close WebSocket.
5. **Disconnection Handling:**
   - If WebSocket closes unexpectedly, frontend falls back to polling `GET /api/v1/scans/:id/status` every 2 seconds.
   - Reconnection attempts with exponential backoff (max 5 retries).

### 15.2 Live Updates
- **Scan Progress:** Primary real-time use case.
- **Admin Metrics:** Optional WebSocket channel `/ws/admin` pushing container health and API usage every 10 seconds.
- **Notification Center:** New in-app notifications pushed via WebSocket (future) or polled every 30 seconds.

### 15.3 Presence System
- **Not implemented in Phase 1.**
- **Future:** If collaborative editing is added, presence indicators show who is viewing a shared report.

### 15.4 Typing Indicators
- **Not applicable** (no real-time chat or collaborative editing in Phase 1).

---

## 16. State Management Flow

### 16.1 Global State (Zustand)
- **Auth State:** `user` (id, email, name, role), `accessToken`, `isAuthenticated`, `tokenExpiry`.
  - Persistence: Not persisted to `localStorage` (security). Stored in memory only. Refresh token in `httpOnly` cookie handles persistence.
- **UI State:** `theme` (persisted to `localStorage`), `sidebarOpen` (persisted to `localStorage`), `activeModal`, `toastQueue`.

### 16.2 Server State (React Query / TanStack Query)
- **Cache Strategy:**
  - Scan reports: staleTime 5 minutes; cacheTime 10 minutes.
  - Scan history: staleTime 2 minutes.
  - User profile: staleTime Infinity (refetched only on manual refresh or mutation).
  - KB articles: staleTime 30 minutes.
- **Background Refetching:** When user returns to a previously visited screen, data refetches in background while stale data is displayed.
- **Optimistic Updates:**
  - Fix application: UI immediately shows "Remediated" badge; if API fails, rollback to "Pending" with error toast.
  - User profile update: UI reflects new name immediately; rollback on failure.

### 16.3 Local State (React useState / useReducer)
- Form inputs, component-level UI toggles (e.g., diff viewer open/closed, log panel expanded).
- Monaco editor internal state (cursor position, selection).

### 16.4 Cache Handling
- **API Synchronization:** React Query `queryClient.invalidateQueries(['scans'])` triggered after scan creation or deletion to ensure lists are fresh.
- **Shared Report Cache:** Public report data cached aggressively (staleTime 1 hour) since it's immutable.

### 16.5 Persistence
- **Theme preference:** `localStorage`.
- **Onboarding flag:** `localStorage` ("Don't show tour again").
- **Sidebar state:** `localStorage`.
- **Auth tokens:** Access token in memory; refresh token in `httpOnly` cookie.

---

## 17. Mobile Responsive Flow

### 17.1 Mobile Navigation
- **Header:** Hamburger icon opens sidebar drawer from left. Logo centered.
- **Bottom Tab Bar (optional for PWA):** 5 tabs — Dashboard, New Scan, History, KB, Profile.
- **Gesture:** Swipe right from left edge opens drawer. Swipe left closes.

### 17.2 Tablet Adaptation
- **Layout:** Two-column layout where appropriate (e.g., Report Viewer stacks vertically instead of side-by-side).
- **Sidebar:** Collapsed icon-only by default; expands on hover/focus.

### 17.3 Responsive Layouts
- **Breakpoints:**
  - Mobile: < 768px — single column, stacked layouts, bottom actions.
  - Tablet: 768–1024px — two-column grids, persistent icon sidebar.
  - Desktop: > 1024px — full sidebar, split-pane report viewer, wide tables.
- **Report Viewer:**
  - Desktop: 60/40 split (code left, findings right).
  - Tablet: 50/50 split.
  - Mobile: Full-width code view; findings as a bottom sheet drawer draggable to 50% height.

### 17.4 Gesture Interactions
- **Pull-to-Refresh:** On history list and dashboard (mobile).
- **Pinch-to-Zoom:** Disabled on report code view (Monaco handles its own zoom via Ctrl+scroll).
- **Swipe Actions:** History list items support swipe-left to delete (with confirmation) on mobile.

### 17.5 Bottom Navigation
- If bottom tab bar is implemented, active tab highlighted with primary color indicator.
- "New Scan" center tab uses a raised circular button for prominence.

---

## 18. Accessibility Flow

### 18.1 Keyboard Navigation
- **Global Shortcuts:**
  - `Cmd/Ctrl + K` — Open global search.
  - `Cmd/Ctrl + B` — Toggle sidebar.
  - `Esc` — Close modals, dropdowns, search.
- **Focus Traps:** Modals and drawers trap focus within their bounds until dismissed.
- **Tab Order:** Logical top-to-bottom, left-to-right flow. Skip link provided to jump to main content.
- **Report Viewer:**
  - `Tab` navigates between findings list items.
  - `Enter` on a finding scrolls code view and opens detail panel.
  - `Space` on "Apply Fix" button triggers action.

### 18.2 Screen Reader Support
- **ARIA Labels:** All interactive elements have descriptive `aria-label` or visible labels.
- **Live Regions:**
  - Scan progress announced via `aria-live="polite"` region: "Scan 40 percent complete. AST parsing stage."
  - Toast notifications announced via `aria-live="assertive"`.
- **Severity Badges:** Color alone does not convey meaning. Each badge includes text label ("Critical") and an icon with `aria-label`.
- **Monaco Editor:** Uses `role="application"` with `aria-roledescription="code editor"`. Alternative: provide a plain-text readonly view for screen-reader users if Monaco accessibility is insufficient.

### 18.3 Focus Management
- **Route Changes:** Focus programmatically moved to `<h1>` of new page (route announcer pattern).
- **Modal Open:** Focus moved to modal title; on close, focus restored to trigger element.
- **Error States:** Focus moved to first invalid form field on submission failure.

### 18.4 Contrast Handling
- **WCAG AA Compliance:** All text meets 4.5:1 contrast ratio.
- **Severity Colors:**
  - Critical: `#DC2626` on white (7.2:1) ✅
  - High: `#EA580C` on white (4.6:1) ✅
  - Medium: `#CA8A04` on white (4.5:1) ✅
  - Low: `#16A34A` on white (5.1:1) ✅
- **Dark Mode:** All severity colors re-mapped for dark backgrounds to maintain contrast.

### 18.5 Error Accessibility
- Error messages linked to fields via `aria-describedby`.
- Error toasts include an audible tone (optional, user-controlled).
- Scan failure messages explain what happened and how to recover in plain language.

---

## 19. User Journey Maps

### 19.1 New User Journey (Zara — CS Student)
| Stage | Action | Thought | Emotion | Opportunity |
|---|---|---|---|---|
| **Awareness** | Sees CodeGuard AI mentioned in class by Dr. Ahmed | "Another security tool? Probably complicated." | Skeptical | Landing page must immediately show simplicity (demo CTA). |
| **Consideration** | Clicks "Try Demo" | "Let's see if this actually explains things." | Curious | Guest demo must execute in <30s with clear results. |
| **Onboarding** | Runs demo scan, sees AI explanation and diff viewer | "Wait, it actually tells me WHY and shows the fix?" | Surprised | Post-demo CTA to register with pre-filled sample context. |
| **Registration** | Registers as Developer | "Quick form, no credit card. Good." | Relieved | Minimal fields; instant login without email verification gate. |
| **First Scan** | Uploads her `app.py` | "Hope it doesn't store my code." | Anxious | Privacy banner and shield icon must be prominent during upload. |
| **Report** | Views findings, reads AI explanation, applies fix | "I finally understand SQL injection! And the fix actually works." | Confident | Positive reinforcement toast after first fix application. |
| **Sharing** | Shares report with Dr. Ahmed via link | "Easy share, no login required for him." | Proud | One-click share with copy-to-clipboard feedback. |
| **Retention** | Returns before next assignment to scan again | "This is faster than Stack Overflow for security bugs." | Habituated | Dashboard trend chart shows improvement over time. |

### 19.2 Returning User Journey (Raza — Junior Developer)
| Stage | Action | Thought | Emotion | Opportunity |
|---|---|---|---|---|
| **Entry** | Logs in during work break | "Need to quickly check this JS file before PR." | Focused | Dashboard loads <2s; "New Scan" is the primary visual. |
| **Scan** | Pastes JS snippet | "Copy-paste is faster than file upload for snippets." | Efficient | Monaco editor auto-detects language; cmd+V works instantly. |
| **Report** | Sees XSS finding, previews fix | "The diff looks correct. Let me apply it." | Assured | AST validation badge next to fix increases trust. |
| **Export** | Exports PDF report | "Attaching this to the PR for the senior dev." | Professional | One-click PDF export with clean, print-ready formatting. |
| **History** | Reviews past scans | "My XSS count is going down. Progress." | Motivated | Trend chart should default to 30-day view showing improvement. |

### 19.3 Power User Journey (Dr. Ahmed — Instructor)
| Stage | Action | Thought | Emotion | Opportunity |
|---|---|---|---|---|
| **Entry** | Logs in to check class metrics before lecture | "Need to see which students are struggling with injection flaws." | Analytical | Instructor dashboard loads class overview immediately. |
| **Metrics** | Filters by SQL injection, last 7 days | "3 students still haven't fixed their login forms." | Concerned | Highlight at-risk students with direct message action. |
| **Drill-down** | Clicks a student's shared report | "Let me see exactly what the AI suggested to them." | Inquisitive | Instructor view shows student report with AI explanation intact. |
| **Action** | Notes students to address in next class | "I'll focus tomorrow's session on parameterized queries." | Proactive | Export class metrics as CSV/PDF for lesson planning. |

### 19.4 Admin Journey (Sana — System Admin)
| Stage | Action | Thought | Emotion | Opportunity |
|---|---|---|---|---|
| **Entry** | Checks System Health first thing | "Are containers running? Did we hit the LLM rate limit overnight?" | Vigilant | System health cards show status at a glance (green/yellow/red). |
| **Alert** | Sees 2 failed containers | "Probably from a bad zip upload. Let me purge them." | Annoyed | One-click "Purge Orphaned Containers" with confirmation. |
| **User Mgmt** | Reviews new registrations | "Any suspicious signups?" | Cautious | Filter by registration date and failed login attempts. |
| **Logs** | Checks API usage trend | "We're at 60% of our monthly LLM budget. Still safe." | Relieved | Visual budget bar with yellow threshold at 80%. |

---

## 20. Flow Optimization Suggestions

### 20.1 UX Improvements
1. **Command Palette:** Implement a `Cmd/Ctrl + Shift + P` command palette for power users to jump to any screen, start a scan, or search KB articles without mouse interaction.
2. **Scan Templates:** Allow users to save frequently scanned code patterns as "templates" for one-click re-scanning (e.g., "My auth module").
3. **Inline Fix Preview on Hover:** In the findings list, hovering a finding shows a mini-tooltip preview of the fix without opening the full diff viewer.
4. **Progressive Onboarding for Instructors:** After an instructor creates their first class, show a contextual tooltip on the "Join Code" explaining how to share it with students.

### 20.2 Performance Optimizations
1. **Virtualized Lists:** Scan history and admin user tables should use `react-window` or `react-virtuoso` for smooth scrolling with 1000+ rows.
2. **Monaco Editor Lazy Loading:** Load Monaco chunks only when the user navigates to a scan-related page. Use `@monaco-editor/react` loader configuration to delay CDN fetch.
3. **PDF Generation Offloading:** Move PDF export entirely to a Celery worker and deliver via email or temporary download link to prevent API blocking.
4. **Image Optimization:** All illustrations and icons served as SVG or WebP with lazy loading and blur-up placeholders.

### 20.3 Navigation Simplification
1. **Contextual Sidebar:** Collapse sidebar sections that are irrelevant to the current role (e.g., hide "Admin" entirely rather than disabling it) to reduce cognitive load.
2. **Smart Redirects:** After applying a fix, the "Next" button should jump to the next unremediated finding rather than requiring manual scan.
3. **Breadcrumb Clickable Segments:** Make parent breadcrumb segments always return to the list view, not just the dashboard.

### 20.4 AI Experience Improvements
1. **Explanation Verbosity Toggle:** Allow users to switch between "Beginner" (plain English, analogy-rich) and "Advanced" (technical, CVE-referenced) explanation modes.
2. **Fix Confidence Visualization:** Instead of a plain percentage, use a segmented progress bar with color bands to visualize confidence (red <50%, yellow 50-80%, green >80%).
3. **Multi-Fix Batch Apply:** Allow users to select multiple findings and apply all validated fixes at once, reducing click fatigue for files with many similar issues.
4. **AI Chat Follow-up (Future):** After viewing an explanation, users can ask follow-up questions ("Why is parameterized query better than escaping?") via an embedded chat widget powered by the same LLM with conversation memory.

### 20.5 Engagement Enhancements
1. **Achievement System:** Gamify learning with badges: "First Scan," "Fix Master" (10 fixes applied), "Security Scholar" (read 5 KB articles), shared on dashboard.
2. **Weekly Digest Email:** Automated email summarizing scan activity, new findings, and KB article recommendations (opt-in).
3. **Class Leaderboard (Optional):** Instructors can enable a voluntary leaderboard showing most-improved security posture (anonymized) to encourage healthy competition.
4. **GitHub Integration Teaser:** On report export screen, show a "Coming Soon: Auto-create PR with fixes" banner to build anticipation for CI/CD integration.

---

## Appendices

### A. Screen-to-API Mapping Quick Reference
| Screen | Primary API | Method |
|---|---|---|
| Landing Page | — | — |
| Login | `/api/v1/auth/login` | POST |
| Register | `/api/v1/auth/register` | POST |
| Dashboard | `/api/v1/dashboard` | GET |
| New Scan | `/api/v1/scans` | POST |
| Scan Progress | WebSocket `/ws/scans/:id` or `GET /api/v1/scans/:id/status` | WS / GET |
| Report Viewer | `/api/v1/reports/:scanId` | GET |
| Apply Fix | `/api/v1/scans/:id/findings/:findingId/apply-fix` | POST |
| Scan History | `/api/v1/users/me/scans` | GET |
| Shared Report | `/api/v1/reports/share/:token` | GET |
| Class List | `/api/v1/instructor/classes` | GET |
| Class Metrics | `/api/v1/instructor/classes/:id/metrics` | GET |
| Admin Users | `/api/v1/admin/users` | GET |
| System Health | `/api/v1/admin/system/health` | GET |
| Event Logs | `/api/v1/admin/system/events` | GET |
| Knowledge Base | `/api/v1/kb` | GET |
| KB Article | `/api/v1/kb/:slug` | GET |

### B. Frontend State Transition Diagram
```
[Unauthenticated]
   ├─ Login Success ──> [Authenticated]
   ├─ Register Success ──> [Login]
   └─ Guest Demo ──> [Demo Report (ephemeral)]

[Authenticated]
   ├─ Token Expire + Refresh Fail ──> [Unauthenticated]
   ├─ Logout ──> [Unauthenticated]
   ├─ New Scan ──> [Scan Progress]
   ├─ Scan Complete ──> [Report Viewer]
   ├─ Apply Fix ──> [Fix Applied / Report Updated]
   └─ Navigate ──> [Dashboard / History / Settings / etc.]
```

---

**End of Document**

**CodeGuard AI — App Flow Document v1.0 | G1F22FYPCS001 | University of Central Punjab | May 12, 2026**
