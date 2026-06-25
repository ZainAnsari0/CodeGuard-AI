# CodeGuard AI — Demo Script

## Overview

This script walks through the core features of CodeGuard AI for a live demonstration. Target duration: 8-10 minutes.

## Prerequisites

- Application running with at least one registered user account
- Test code files ready for upload (Python and JavaScript)
- Ollama running locally or API keys configured

## Demo Flow

### 1. Landing Page & Registration (1 min)

**Show:**
- Navigate to the landing page
- Highlight key features: AI-powered scanning, educational feedback, zero-persistence privacy

**Action:**
- Click "Register" and create an account (or log in with existing credentials)
- Note: Account creation is instant, no email verification required

**Talking Point:**
> "CodeGuard AI starts with a privacy-first approach. Accounts require minimal information, and all scanned code is processed in ephemeral temporary workspaces that are automatically deleted after analysis."

### 2. Dashboard Overview (1 min)

**Show:**
- Dashboard after login
- Recent scans, vulnerability trends, quick actions

**Talking Point:**
> "The dashboard provides an at-a-glance view of your security posture. You can see recent scan results, trending vulnerability types, and quick access to start a new scan."

### 3. Code Upload & Scan (3 min)

**Action:**
- Click "New Scan" or "Upload Code"
- Upload a Python file with intentional vulnerabilities (e.g., `eval()` usage, SQL injection, hardcoded credentials)

**Show:**
- File upload progress
- Scan status progression (Queued → Running → Completed)
- Real-time progress updates

**Talking Point:**
> "The scanning process uses AST-based deterministic analysis first, then enriches findings with AI explanations. All code is parsed in an isolated temporary workspace that's destroyed after scanning — your code never persists on our servers."

### 4. Scan Results & Findings (3 min)

**Show:**
- Vulnerability list with severity levels (Critical, High, Medium, Low, Info)
- Click on a finding to see:
  - Vulnerable code highlighted in the editor
  - CWE classification
  - AI-generated explanation in plain English
  - Suggested fix with diff view

**Talking Point:**
> "Each finding includes a plain-English explanation of why this code is vulnerable, what an attacker could exploit, and how to fix it. The AI explanations are generated through our fallback chain — if the primary model is unavailable, we fall back to deterministic explanations, ensuring you always get actionable feedback."

### 5. Apply Fix (1 min)

**Action:**
- Click "Apply Fix" on a finding
- Review the AI-suggested fix in the diff viewer
- Confirm the fix

**Show:**
- Diff view showing original vs. fixed code
- AST validation confirms the fix is syntactically correct

**Talking Point:**
> "Every AI-generated fix passes through AST re-validation before being shown to you. If the fix doesn't compile or introduces new syntax errors, it's rejected. This is our hallucination mitigation gate."

### 6. Share Report (1 min)

**Action:**
- Click "Share Report" on the scan results page
- Generate a shareable link

**Talking Point:**
> "Reports can be shared with instructors or teammates via a unique link. The shared view is read-only and accessible without authentication."

### 7. Knowledge Base (1 min)

**Show:**
- Navigate to Knowledge Base
- Browse vulnerability categories (Injection, XSS, etc.)
- Open a CWE article (e.g., CWE-89 SQL Injection)
- Show the educational content with examples and remediation guidance

**Talking Point:**
> "The Knowledge Base provides in-depth educational content for each vulnerability class, going beyond just 'fix this code' to teaching why certain patterns are dangerous and how to think about security."

### 8. Admin Panel (1 min, if applicable)

**Show:**
- Switch to admin account (or show if current user has admin role)
- User management, system health, event logs

**Talking Point:**
> "Instructors and administrators have access to a dashboard for managing users, viewing system health metrics, and auditing system events."

## Fallback Scenarios

### If AI Models Are Unavailable

- The fallback chain will use deterministic rule-based explanations
- Scans will still complete, but explanations will be more concise
- **Talking Point:** "Our multi-tier fallback chain ensures the platform remains functional even if all AI providers are down."

### If Node.js Is Unavailable

- JavaScript scanning falls back to regex-based pattern matching
- Python scanning still works (uses built-in `ast` module)
- All other features (dashboard, knowledge base, report viewing) work normally

### If Demo Environment Is Slow

- Use pre-uploaded scan results to show findings
- Skip the scan wait and jump to results view
- Emphasize the privacy-first design and educational value

## Key Metrics to Highlight

| Metric                  | Target          |
|-------------------------|-----------------|
| Scan latency (<1K LOC) | < 5 seconds     |
| Scan latency (<10K LOC) | < 30 seconds    |
| False Positive Rate     | < 15%           |
| Concurrent scans        | 5               |
| Platform uptime         | 95%+            |
| Test coverage           | 80%+ backend    |

## Closing Statement

> "CodeGuard AI bridges the gap between automated security tools and developer education. By combining deterministic AST analysis with AI-powered explanations, validated fixes, and a comprehensive knowledge base, we make security accessible to developers at every skill level — while maintaining strict privacy guarantees through ephemeral workspace isolation and a static analysis safety model."