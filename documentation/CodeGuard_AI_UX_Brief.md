# CodeGuard AI — UI/UX Design Brief Document

**Document Version:** 1.0  
**Date:** 2026-05-12  
**Status:** Final — Design System & Experience Specification  
**Audience:** UI/UX Designers, Frontend Engineers, Product Managers, Branding Teams, Stakeholders  

---

## 1. Project Overview

### 1.1 Product Name
**CodeGuard AI** — Intelligent Code Vulnerability Scanner with Explainable AI Feedback

### 1.2 Product Summary
CodeGuard AI is a privacy-first, AI-augmented static application security testing (SAST) platform built for the next generation of developers. It transforms cryptic security warnings into plain-English explanations, confidence-scored findings, and one-click validated fixes — all within ephemeral containers that guarantee zero persistent source code storage.

The platform serves four user archetypes: Guests evaluating the tool, Developers/Students learning secure coding, Instructors monitoring class-wide security trends, and System Administrators maintaining operational health. The product bridges the gap between enterprise-grade security tools and accessible educational software.

### 1.3 Product Vision
To make secure coding accessible and understandable to every developer, regardless of experience level, by transforming opaque security warnings into clear, actionable, educational guidance.

### 1.4 Core Objectives
- **Educate:** Turn vulnerability detection into a learning moment, not a scolding.
- **Empower:** Enable junior developers to fix issues independently without senior escalation.
- **Assure:** Guarantee absolute privacy through ephemeral architecture, visually communicated at every touchpoint.
- **Scale:** Support classroom-scale usage (40+ students, 5 concurrent scans) while maintaining sub-5-second small-file scan latency.
- **Differentiate:** Be the only SAST tool that combines deterministic AST analysis with explainable AI and validated fix suggestions.

### 1.5 Business Goals
- Lower the cost and time of early-stage vulnerability remediation for students and junior developers.
- Enhance security literacy among BSCS students and bootcamp graduates.
- Demonstrate a viable open-core alternative to enterprise SAST tools (SonarQube, Bandit, ESLint).
- Build a modular platform with a future path to CI/CD integration and IDE plugins.

### 1.6 Design Goals
- **Trust-First Interface:** Every screen must visually reinforce the privacy promise. No dark patterns, no hidden data collection, no ambiguity about where code goes.
- **Clarity Over Density:** The interface should feel spacious, breathable, and focused. Avoid the "enterprise dashboard vomit" of traditional security tools.
- **Progressive Disclosure:** A first-time user sees only what they need (upload, scan, result). Advanced features (batch fixes, trend analytics, class metrics) reveal themselves naturally.
- **Emotional Safety:** Vulnerability reports must feel educational, not accusatory. Use supportive language, constructive visuals, and gamified progress to reduce anxiety.
- **Developer-Native Aesthetic:** The UI should feel like a premium developer tool (Linear, Vercel, GitHub Copilot) rather than a corporate compliance dashboard.

### 1.7 Expected User Experience
A user should be able to go from landing on the homepage to applying their first validated security fix in under **3 minutes**. Every interaction should feel instantaneous (feedback within 200ms), intelligent (AI anticipates next steps), and respectful (no patronizing tooltips, no alert fatigue).

---

## 2. Product Understanding

### 2.1 What the Platform Does
1. **Ingests Code:** Accepts Python/JavaScript files, ZIP archives, or raw code snippets via drag-and-drop or Monaco editor paste.
2. **Isolates & Parses:** Spins up ephemeral Docker containers, parses code into Abstract Syntax Trees (ASTs), and flags risky syntactic patterns.
3. **Explains with AI:** Routes flagged nodes to a Large Language Model (LLM) pipeline that generates human-readable explanations, severity scores, confidence percentages, and suggested fixes.
4. **Validates Fixes:** Re-parses AI-generated fixes through the AST parser to confirm syntactic correctness before human display.
5. **Teaches & Tracks:** Provides a knowledge base, scan history with trend charts, instructor class metrics, and shareable read-only reports.
6. **Destroys Evidence:** Auto-deletes all source code and destroys containers immediately after scan completion.

### 2.2 Main User Problems Solved
- **Alert Fatigue:** Traditional SAST tools (SonarQube, ESLint) produce cryptic regex-based warnings. CodeGuard AI explains *why* and *how* in plain English.
- **Knowledge Gap:** Junior developers don't know what "CWE-89" means. The platform maps every finding to educational content.
- **Fix Uncertainty:** Most tools flag problems but offer no remediation path. CodeGuard AI provides validated, one-click fixes with diff previews.
- **Privacy Paranoia:** Students and professionals hesitate to upload proprietary code to cloud scanners. Ephemeral containers guarantee zero storage.
- **Classroom Chaos:** Instructors manually reviewing 40 codebases is impractical. Aggregated class metrics surface at-risk students automatically.

### 2.3 Product Positioning
| Dimension | CodeGuard AI | SonarQube | Bandit/ESLint | GitHub Copilot |
|---|---|---|---|---|
| **UX Philosophy** | Educational & Explorable | Enterprise Compliance | Minimal CLI Output | Generative Assistant |
| **Explanations** | Full natural language | None | None | Partial |
| **Fix Quality** | AST-validated | None | None | Unvalidated |
| **Privacy Model** | Ephemeral / Zero Storage | Persistent | Local | Cloud |
| **Target User** | Student / Junior Dev | Enterprise Team | Python Dev | General Developer |
| **Cost** | Free / Open-core | Expensive | Free | Paid |

### 2.4 Competitive Advantages (Design Perspective)
- **Only SAST tool with an interactive diff viewer** as a first-class UI component (not a separate IDE plugin).
- **Only tool that gamifies security posture** with trend charts and class leaderboards for educational contexts.
- **Only tool that uses AI confidence percentages** alongside severity to reduce alert fatigue (users can triage low-confidence findings first).
- **Only tool with a public, shareable report link** that requires no authentication — perfect for student-advisor feedback loops.

### 2.5 User Expectations
- **Speed:** Scans should feel faster than compiling code. Sub-5s for typical student assignments.
- **Transparency:** Users expect to know *exactly* what happened to their code and *why* a fix is correct.
- **Control:** One-click apply, one-click revert. No irreversible actions without confirmation.
- **Beauty:** Developers spend hours in beautiful tools (VS Code, Figma, Notion). A clunky UI signals untrustworthy engineering.
- **Offline Resilience:** If the cloud LLM is down, the tool should still provide rule-based scoring without crashing.

---

## 3. Target Audience

### 3.1 Persona 1: Zara — The Curious Student
- **Demographics:** 21-year-old female, 3rd-year BSCS student at University of Central Punjab.
- **Technical Proficiency:** Strong Python basics; limited security knowledge. Knows SQL but not injection. Never used a SAST tool before.
- **Goals:** Submit secure code for her final-year project; understand why her database queries are "flagged" without Googling for hours.
- **Frustrations:**
  - Traditional tools list 50 warnings with zero context.
  - OWASP documentation is too dense and theoretical.
  - She is afraid uploading her project to a cloud tool will get her flagged for plagiarism or data leakage.
- **Device Usage:** Laptop (primary), occasionally checks shared reports on her phone.
- **Behavioral Patterns:** Skims content, clicks shiny buttons, trusts visual indicators (green checkmarks, shield icons). Needs positive reinforcement.
- **Accessibility Needs:** May use screen readers during late-night study sessions. Needs high-contrast severity indicators because she is mildly colorblind (deuteranopia).

### 3.2 Persona 2: Raza — The Anxious Junior Developer
- **Demographics:** 24-year-old male, bootcamp graduate, 6 months into first professional JavaScript role.
- **Technical Proficiency:** Writes JavaScript daily. Knows XSS exists but doesn't know how to spot it in his own code. Uses VS Code, GitHub, and Stack Overflow religiously.
- **Goals:** Catch vulnerabilities before code review to avoid embarrassing senior dev feedback. Export clean PDF reports to attach to PRs.
- **Frustrations:**
  - Enterprise SAST tools cost $500+/month — impossible on his salary.
  - Free alternatives (ESLint security plugins) give regex warnings he doesn't understand.
  - Copilot sometimes writes vulnerable code and doesn't warn him.
- **Device Usage:** Desktop workstation (dual monitor). Wants the report on one screen while he edits code on the other.
- **Behavioral Patterns:** Keyboard-heavy user. Expects shortcuts (Cmd+K search, Cmd+B sidebar toggle). Values speed and precision.
- **Accessibility Needs:** Prefers dark mode for all-day screen use. Needs keyboard-navigable diff viewer because he rarely touches the mouse.

### 3.3 Persona 3: Dr. Ahmed — The Data-Driven Instructor
- **Demographics:** 45-year-old male, PhD in Computer Science, teaches Secure Software Development to 40 students across 3 project groups.
- **Technical Proficiency:** Expert in security theory. Can read ASTs manually. Wants aggregated data, not individual line-by-line reports.
- **Goals:** Monitor class-wide security trends; identify struggling students for targeted guidance; review shared student reports efficiently.
- **Frustrations:**
  - Manually reviewing 40 codebases is physically impossible.
  - Students submit vulnerable code repeatedly because they don't understand the feedback from basic linters.
  - No existing tool provides a "classroom dashboard" view.
- **Device Usage:** Desktop in office, iPad Pro during lectures for live metrics projection.
- **Behavioral Patterns:** Analytical. Filters and sorts data aggressively. Wants exportable CSV/PDFs for grading rubrics.
- **Accessibility Needs:** Projects dashboard to a classroom projector — needs large, readable fonts and colorblind-safe charts.

### 3.4 Persona 4: Sana — The vigilant System Admin
- **Demographics:** 30-year-old female, DevOps engineer managing the university server hosting CodeGuard AI.
- **Technical Proficiency:** Expert in Docker, Kubernetes, and cloud infrastructure. Wants raw metrics, not fluffy UI.
- **Goals:** Keep the platform healthy, monitor API usage quotas, manage user accounts, and prevent resource exhaustion.
- **Frustrations:**
  - No visibility into container health or LLM API burn rate until things break.
  - Academic tools usually have terrible admin panels.
- **Device Usage:** Laptop with multiple terminal windows. Checks admin panel between deploys.
- **Behavioral Patterns:** Scan-heavy information seeker. Wants dense data tables, not card-based layouts. Needs one-click remediation actions.
- **Accessibility Needs:** Works in dark environments (server rooms); prefers dark mode with amber accent colors to reduce eye strain.

---

## 4. UX Goals

### 4.1 Simplicity Goals
- **Three-Click Rule:** From dashboard to applied fix should never exceed 3 intentional clicks: 1) Upload, 2) View Finding, 3) Apply Fix.
- **Zero-Config Scanning:** A new user should not need to configure rules, thresholds, or integrations before running their first scan.
- **Flat Information Architecture:** No nested menus deeper than 2 levels. Every primary feature accessible from the sidebar.
- **Consistent Action Patterns:** Every primary action uses the same button style, placement (bottom-right or top-right), and confirmation behavior.

### 4.2 Accessibility Goals
- **WCAG 2.1 AA Compliance:** All 50+ screens must pass automated (axe-core) and manual screen-reader testing.
- **Color Independence:** Severity must never be communicated by color alone. Every severity badge includes an icon + text label.
- **Keyboard-First Dashboard:** Every workflow must be fully operable without a mouse.
- **Focus Visibility:** All interactive elements have a 2px solid focus ring with 4px offset (never rely on browser defaults).
- **Reduced Motion Respect:** All animations respect `prefers-reduced-motion: reduce` and degrade to instant state changes.

### 4.3 Engagement Goals
- **First-Scan Celebration:** After a user's first scan completes, display a celebratory micro-animation (confetti or progress checkmark) to create a positive emotional association.
- **Knowledge Base Deep-Linking:** Every finding in a report links to a relevant KB article. Target: > 40% of users click through on their first report.
- **Shareability:** Users should be able to generate and copy a shareable link in 2 clicks. The shared report must be visually identical to the authenticated view.
- **Trend Visualization:** Users who view their trend chart at least once have 3x higher 7-day retention (hypothesis to validate).

### 4.4 Retention Goals
- **Sticky Dashboard:** The dashboard should feel like a personal command center. Show "Recent Scans," "Recommended Reading," and "Quick Scan" in one view.
- **Email Digest (Future):** Weekly summary of scan activity, new findings, and security tips (opt-in) to drive return visits.
- **Classroom Lock-In:** Instructors create classes; students join. This social loop increases retention for both roles.

### 4.5 AI Interaction Goals
- **Explainability at a Glance:** The AI explanation must be scannable in < 10 seconds. Use bullet points, bold keywords, and short paragraphs.
- **Trust Indicators:** Confidence percentage displayed prominently next to severity. Hovering the confidence badge shows a tooltip: "The AI is 94% confident in this assessment."
- **Fix Transparency:** The diff viewer must show *exactly* what changed, line by line. No hidden transformations.
- **Failure Grace:** If the AI fails, the interface should not display a dead-end. Show rule-based severity with a non-blocking banner: "AI insights temporarily unavailable.".

### 4.6 Productivity Goals
- **Batch Actions:** Scan history supports multi-select delete. Future: batch fix application.
- **Global Search:** `Cmd/Ctrl + K` opens a fuzzy search modal to jump to any screen, scan, or KB article within 500ms.
- **Context Preservation:** When a user applies a fix, the report scroll position and expanded finding state should persist.
- **Export Speed:** PDF/JSON export generation must not block the UI. User receives a "Preparing download..." toast and a notification when ready.

### 4.7 Emotional Design Goals
- **Non-Accusatory Language:** Use "This code could be safer" instead of "Vulnerability detected!" Use "Suggested improvement" instead of "Fix required."
- **Positive Framing:** When a scan finds zero issues, celebrate it. Don't just show an empty table.
- **Progressive Mastery:** As users fix more issues, subtly increase the sophistication of explanations (beginner → intermediate → advanced) based on their history.

---

## 5. Brand & Visual Identity

### 5.1 Brand Personality
- **Guardian:** Protective, reliable, always watching out for the user. Not authoritarian — more like a mentor.
- **Scholar:** Educational, articulate, evidence-based. Cites CWEs and OWASP references with confidence.
- **Architect:** Precise, structural, systematic. The UI reflects the rigor of code itself — grids, alignment, monospace.
- **Innovator:** AI-powered, forward-thinking, modern. Not stodgy or corporate.

### 5.2 Tone of Interface
- **Supportive, not Scolding:** "We found 3 opportunities to strengthen your code" beats "3 vulnerabilities detected."
- **Precise, not Vague:** Every explanation names the specific risk (e.g., "SQL injection via string concatenation") rather than generic warnings.
- **Humble, not Arrogant:** Confidence percentages and AST validation badges honestly communicate AI limitations.
- **Professional, not Boring:** The interface is clean but uses vibrant semantic colors and subtle animations to maintain energy.

### 5.3 Visual Mood
**"The intersection of a premium IDE and a modern wellness app."**
- Dark, immersive backgrounds (like VS Code or GitHub Dark) make long code sessions comfortable.
- Bright, accessible semantic colors (severity indicators) punctuate the darkness with meaning.
- Generous whitespace prevents the cognitive overload typical of security dashboards.
- Subtle glassmorphism and blurred backdrops (in modals and drawers) add depth without distraction.

### 5.4 Design Language
**Modern Developer SaaS with Educational Warmth**
- Inspired by: **Linear** (clarity and speed), **Vercel** (developer-native aesthetics), **Notion** (progressive disclosure), **Duolingo** (gamified learning energy — adapted for security education).
- Avoid: Corporate banking UI cliches (gradients from 2008, excessive borders, 12-column cluttered dashboards).

### 5.5 Style Direction
- **Primary Mode:** Dark mode (default). Developers spend hours in dark IDEs; the platform should feel native to their environment.
- **Secondary Mode:** Light mode (optional toggle). Useful for classroom projection, printing reports, and users with photophobia sensitivity.
- **Accent Strategy:** Electric blue for primary actions and AI branding. Warm amber for warnings. Emerald for success and "safe code." Crimson for critical severity.
- **Shape Language:** Predominantly rounded (8px–12px radius for cards, 6px for buttons) to feel approachable. Sharp 0px radius only for code blocks and data tables to signal "precision."
- **Elevation:** Subtle shadows for cards (0 4px 12px rgba(0,0,0,0.15)). No heavy drop shadows. Use layered backgrounds (surface-1, surface-2, surface-3) for depth instead of borders.

---

## 6. Color System

### 6.1 Design Tokens (CSS Variables / Tailwind Config)

#### Primary Colors
| Token | Hex | Usage |
|---|---|---|
| `--color-primary-50` | `#EEF4FF` | Lightest tint, backgrounds |
| `--color-primary-100` | `#D9E6FF` | Hover states, subtle fills |
| `--color-primary-200` | `#B3D1FF` | Focus rings (light mode) |
| `--color-primary-400` | `#4A90F8` | Secondary buttons, links |
| `--color-primary-500` | `#2563EB` | **Primary brand color.** Main CTAs, active nav, AI badge |
| `--color-primary-600` | `#1D4ED8` | Primary hover |
| `--color-primary-700` | `#1E40AF` | Primary pressed/active |

#### Secondary Colors
| Token | Hex | Usage |
|---|---|---|
| `--color-secondary-50` | `#F5F3FF` | Subtle purple backgrounds |
| `--color-secondary-500` | `#7C3AED` | Instructor accent, class cards |
| `--color-secondary-600` | `#6D28D9` | Instructor hover |

#### Semantic Colors (Severity & Status)
| Token | Hex | Usage | Contrast on Dark | Contrast on Light |
|---|---|---|---|---|
| `--color-critical` | `#DC2626` | Critical severity | 7.2:1 ✅ | 5.8:1 ✅ |
| `--color-high` | `#EA580C` | High severity | 4.6:1 ✅ | 3.8:1 ⚠️* | 
| `--color-medium` | `#CA8A04` | Medium severity | 4.5:1 ✅ | 3.5:1 ⚠️* |
| `--color-low` | `#16A34A` | Low severity | 5.1:1 ✅ | 4.2:1 ✅ |
| `--color-info` | `#3B82F6` | Informational banners | 4.8:1 ✅ | 4.0:1 ✅ |
| `--color-success` | `#10B981` | Fix applied, safe code | 5.4:1 ✅ | 4.5:1 ✅ |
| `--color-warning` | `#F59E0B` | Warnings, caution | 4.5:1 ✅ | 3.2:1 ⚠️* |

*For `high`, `medium`, and `warning` on light backgrounds, use a **darker text variant** (`#7C2D12` on amber bg, `#92400E` on orange bg) to guarantee 4.5:1 contrast.

#### Neutral Palette (Dark Mode — Default)
| Token | Hex | Usage |
|---|---|---|
| `--color-bg-base` | `#0F1117` | Deepest background (page root) |
| `--color-surface-1` | `#181B24` | Primary card/panel background |
| `--color-surface-2` | `#1F2330` | Elevated surfaces (dropdowns, modals) |
| `--color-surface-3` | `#2A2F3D` | Input backgrounds, hover states |
| `--color-border` | `#2E3548` | Subtle dividers, table borders |
| `--color-text-primary` | `#F1F5F9` | Headings, primary text |
| `--color-text-secondary` | `#94A3B8` | Body text, descriptions |
| `--color-text-tertiary` | `#64748B` | Timestamps, metadata, placeholders |
| `--color-text-inverse` | `#0F1117` | Text on primary buttons |

#### Neutral Palette (Light Mode)
| Token | Hex | Usage |
|---|---|---|
| `--color-bg-base` | `#F8FAFC` | Page background |
| `--color-surface-1` | `#FFFFFF` | Cards |
| `--color-surface-2` | `#F1F5F9` | Elevated surfaces |
| `--color-surface-3` | `#E2E8F0` | Inputs |
| `--color-border` | `#CBD5E1` | Borders |
| `--color-text-primary` | `#0F172A` | Headings |
| `--color-text-secondary` | `#475569` | Body |
| `--color-text-tertiary` | `#94A3B8` | Metadata |

### 6.2 Dark Mode Palette (Default)
The application **defaults to dark mode** to align with developer expectations. Light mode is an opt-in toggle in Settings.

### 6.3 Light Mode Palette
Activated via Settings > Theme. All semantic colors remain identical; only neutrals invert. Ensure severity badges use dark text on light semantic backgrounds to maintain contrast.

### 6.4 Psychological Reasoning
- **Dark Base:** Reduces eye strain for prolonged code review sessions. Signals "developer tool" rather than "consumer app."
- **Blue Primary:** Trust, intelligence, technology. Associated with security (SSL locks are blue).
- **Red/Orange/Amber/Green Severity Spectrum:** Universally understood traffic-light metaphor. Red = stop/critical; Green = go/safe.
- **Purple Secondary:** Differentiates instructor/classroom features from core scanning. Purple signals "premium" or "special" without clashing with semantic colors.
- **Generous Greys:** Prevent visual fatigue. Using a 12-step neutral scale ensures sufficient contrast between adjacent surfaces without relying on borders.

### 6.5 Accessibility Considerations
- **Never Color-Only Communication:** Every severity badge pairs color with an icon (shield with exclamation, warning triangle, info circle, checkmark) and text label.
- **Colorblind Simulation:** Design tested against deuteranopia, protanopia, and tritanopia filters. Severity distinctions remain clear via shape and text.
- **Focus Indicators:** Focus rings use `--color-primary-200` in dark mode (high contrast against dark surfaces).

---

## 7. Typography System

### 7.1 Font Families
- **Headings & UI:** **Inter** (Google Fonts / Fontsource). Clean, highly legible at small sizes, excellent tabular numerals for metrics.
- **Monospace / Code:** **JetBrains Mono** or **Fira Code**. Used exclusively in the Monaco editor, code snippets, diff viewer, and inline code tokens. Supports ligatures (optional).
- **Fallback Stack:** `system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`.

### 7.2 Font Hierarchy
| Level | Font | Size (Desktop) | Weight | Line Height | Letter Spacing | Usage |
|---|---|---|---|---|---|---|
| H1 | Inter | 36px / 2.25rem | 700 | 1.1 | -0.02em | Landing hero, page titles |
| H2 | Inter | 28px / 1.75rem | 700 | 1.2 | -0.01em | Section headers |
| H3 | Inter | 22px / 1.375rem | 600 | 1.3 | -0.01em | Card titles, panel headers |
| H4 | Inter | 18px / 1.125rem | 600 | 1.4 | 0 | Subsection titles |
| Body | Inter | 16px / 1rem | 400 | 1.6 | 0 | Paragraphs, descriptions |
| Body Small | Inter | 14px / 0.875rem | 400 | 1.5 | 0 | Metadata, timestamps |
| Caption | Inter | 12px / 0.75rem | 500 | 1.4 | 0.02em | Labels, badges, tags |
| Code | JetBrains Mono | 14px / 0.875rem | 400 | 1.6 | 0 | Code blocks, inline code |
| Code Small | JetBrains Mono | 12px / 0.75rem | 400 | 1.5 | 0 | Line numbers, file paths |

### 7.3 Font Weights
- **400 (Regular):** Body text, descriptions.
- **500 (Medium):** Buttons, captions, labels.
- **600 (Semibold):** Card titles, navigation items, emphasis.
- **700 (Bold):** Headings, critical data points, empty state titles.

### 7.4 Responsive Typography
- **Mobile:** H1 scales to 28px, H2 to 22px, H3 to 18px. Body remains 16px (accessible baseline). Code remains 13px minimum for readability.
- **Tablet:** H1 at 32px. Line heights increase by 0.1 for touch-friendly readability.

### 7.5 Readability Considerations
- **Max Line Length:** 75 characters for body text (use `max-w-prose` or `max-w-2xl`).
- **Code Blocks:** Horizontal scroll enabled at 80 characters to prevent line wrapping that destroys AST line-number alignment.
- **Numerals:** Tabular figures (`font-variant-numeric: tabular-nums`) for all metrics, counts, and timestamps to prevent jitter during live updates.

---

## 8. Design System

### 8.1 Design Principles
1. **Consistency is Trust:** The same button behaves the same way everywhere. The same severity color means the same thing on every screen.
2. **Whitespace is Information:** Padding and margins are not "empty space" — they group related elements and separate unrelated ones.
3. **Motion is Meaning:** Animations communicate state changes (loading → loaded, pending → applied). Never animate for decoration alone.
4. **Accessibility is not a Feature:** It is the foundation. Every component is designed accessible first, then enhanced.
5. **Code is Content:** The UI must treat source code as first-class content — readable, selectable, and visually distinct from marketing copy.

### 8.2 Component System
All components are designed as reusable, theme-aware, and responsive primitives.

#### Buttons
| Variant | Background | Text | Border | Hover | Usage |
|---|---|---|---|---|---|
| Primary | `--color-primary-500` | `--color-text-inverse` | none | `--color-primary-600` | Main CTAs (Start Scan, Apply Fix) |
| Secondary | `--color-surface-2` | `--color-text-primary` | `--color-border` | `--color-surface-3` | Secondary actions (Preview Fix, Share) |
| Ghost | transparent | `--color-primary-500` | none | `--color-primary-50` (10% opacity) | Tertiary actions, icon buttons |
| Danger | `--color-critical` | `--color-text-inverse` | none | `#B91C1C` | Destructive actions (Delete, Revoke) |
| Success | `--color-success` | `--color-text-inverse` | none | `#059669` | Fix applied, confirm safe |

- **Shape:** 6px border radius (8px for large promotional CTAs).
- **Height:** 40px default (desktop), 44px (mobile touch targets).
- **Padding:** 12px horizontal, 0px vertical (flex centering).
- **Loading State:** Spinner replaces text; disabled state with reduced opacity (0.6).
- **Icon Support:** 16px icon + 8px gap + text. Icon-only buttons have 36px square footprint.

#### Inputs
- **Height:** 40px (desktop), 44px (mobile).
- **Background:** `--color-surface-3`.
- **Border:** 1px solid `--color-border`; focus: 2px solid `--color-primary-500` with 0px border-radius change.
- **Placeholder:** `--color-text-tertiary`.
- **Error State:** Border changes to `--color-critical`; error text 12px below input.
- **Monaco Editor Input:** Special case. Full-width container with 1px `--color-border` outline, `--color-bg-base` background, and its own internal theming matching the platform dark mode.

#### Cards
- **Background:** `--color-surface-1`.
- **Border Radius:** 12px (large cards), 8px (list items).
- **Shadow:** `0 1px 3px rgba(0,0,0,0.12)` (subtle, never harsh).
- **Padding:** 24px internal padding (desktop), 16px (mobile).
- **Hover (Interactive Cards):** Border color transitions to `--color-primary-500` at 30% opacity; translateY(-2px) with `transition: all 200ms ease`.
- **Active/Selected:** 2px solid `--color-primary-500` border.

#### Modals / Drawers
- **Overlay:** `rgba(0,0,0,0.6)` backdrop with `backdrop-filter: blur(4px)`.
- **Container:** `--color-surface-2`, 12px border radius, max-width 640px (modals), 480px (confirmation dialogs).
- **Animation:** Fade in 150ms; scale from 0.95 to 1.0 (200ms, ease-out). Drawers slide from right (desktop) or bottom (mobile).
- **Focus Trap:** Tab cycles within modal. Escape key closes.

#### Dropdowns / Menus
- **Trigger:** Button with chevron-down icon (12px).
- **Menu:** `--color-surface-2`, 8px radius, 4px padding. Items 36px height.
- **Hover:** `--color-surface-3` background.
- **Active Item:** `--color-primary-500` left border accent + subtle background tint.

#### Tables
- **Header:** `--color-surface-2` background, 12px uppercase caption text (`--color-text-tertiary`).
- **Row:** `--color-surface-1` alternating with `--color-bg-base` for zebra striping (optional).
- **Hover Row:** `--color-surface-3`.
- **Cell Padding:** 16px vertical, 16px horizontal.
- **Empty State:** Centered illustration + message inside a single-row table.

#### Charts
- **Library Style:** Recharts with custom theme wrapper.
- **Line Chart:** 2px stroke, `--color-primary-500` primary line, semantic colors for multi-line severity trends.
- **Bar Chart:** 8px rounded caps, `--color-surface-3` grid lines, no vertical grid.
- **Tooltip:** `--color-surface-2` card with 8px radius, no shadow. Values in tabular numerals.
- **Empty Chart:** "No data yet" with a subtle grey silhouette of the expected chart shape.

#### Navigation (Sidebar)
- **Width:** 240px expanded, 72px collapsed (icon-only).
- **Background:** `--color-surface-1` with 1px right border `--color-border`.
- **Item Height:** 40px.
- **Icon:** 20px, 12px gap before label.
- **Active:** Left 4px border accent `--color-primary-500`, background `--color-primary-50` at 10% opacity.
- **Hover:** Background `--color-surface-3`.
- **Section Label:** 12px uppercase, `--color-text-tertiary`, 24px top margin.

#### Alerts / Toasts
- **Toast Container:** Bottom-right (desktop), top-center (mobile). Stacked vertically with 12px gap.
- **Variants:**
  - Success: `--color-success` left border + icon.
  - Error: `--color-critical` left border + icon.
  - Warning: `--color-warning` left border + icon.
  - Info: `--color-info` left border + icon.
- **Auto-Dismiss:** 4 seconds (except errors, which persist).
- **Animation:** Slide up from 16px offset + fade in (200ms). Exit: fade out + slide down (150ms).

#### AI Chat / Explanation Components
- **AI Badge:** Small sparkle icon + "AI" label in `--color-primary-500`.
- **Explanation Card:** `--color-surface-2` with a subtle left gradient border (4px, `--color-primary-500`).
- **Confidence Meter:** Horizontal segmented bar (10 segments) filled proportionally. Color segments: red (0-40%), yellow (40-70%), green (70-100%).
- **Diff Viewer:** Dedicated component. See Screen Design Requirements.

### 8.3 Spacing System (Tailwind-Compatible)
Base unit: **4px**
| Token | Value | Usage |
|---|---|---|
| `space-1` | 4px | Icon gaps, tight padding |
| `space-2` | 8px | Inline element gaps |
| `space-3` | 12px | Button padding, small margins |
| `space-4` | 16px | Card internal padding, form gaps |
| `space-5` | 20px | Section sub-gaps |
| `space-6` | 24px | Standard card padding, section gaps |
| `space-8` | 32px | Large section separations |
| `space-10` | 40px | Page-level padding |
| `space-12` | 48px | Hero spacing |
| `space-16` | 64px | Major section breaks |

### 8.4 Grid System
- **Desktop:** 12-column grid, 24px gutter, max container width 1280px (centered with auto margins).
- **Tablet:** 8-column grid, 16px gutter.
- **Mobile:** 4-column grid, 16px gutter.
- **Dashboard Widgets:** Use CSS Grid with `grid-template-columns: repeat(auto-fill, minmax(320px, 1fr))` for responsive card layouts.

### 8.5 Border Radius Rules
- **0px:** Code blocks, data tables, terminal-style logs (sharp = precise).
- **6px:** Buttons, inputs, small tags.
- **8px:** List items, dropdown menus, small cards.
- **12px:** Main cards, modals, panels.
- **50% (Pill):** Status badges, user avatars, filter chips.

### 8.6 Shadow System
- **Level 1 (Cards):** `0 1px 3px rgba(0,0,0,0.12)`
- **Level 2 (Dropdowns, Popovers):** `0 4px 12px rgba(0,0,0,0.15)`
- **Level 3 (Modals):** `0 8px 24px rgba(0,0,0,0.20)`
- **Level 4 (Toasts):** `0 12px 32px rgba(0,0,0,0.25)`
- **No shadows on dark mode surfaces** unless necessary for elevation; rely on background color steps (`surface-1` vs `surface-2`).

### 8.7 Iconography
- **Library:** Lucide React (consistent stroke width, clean geometric shapes).
- **Stroke Width:** 1.5px (default), 2px for active states.
- **Size Scale:** 16px (inline), 20px (nav items), 24px (empty states), 32px (feature icons).
- **Icon + Color Rules:**
  - Navigation icons: `--color-text-secondary`, active `--color-primary-500`.
  - Severity icons: `--color-critical` (alert-octagon), `--color-high` (alert-triangle), `--color-medium` (alert-circle), `--color-low` (info), `--color-success` (shield-check).
  - Action icons: inherit button text color.

### 8.8 Illustration Style
- **Style:** Flat vector illustrations with subtle gradients (2-color max). Avoid 3D or photorealism.
- **Color Palette:** Illustrations use primary blue (`#2563EB`) and neutral slate accents. Severity-themed illustrations use the corresponding semantic color.
- **Empty States:** Custom spot illustrations (240x160px) for each empty state (no scans, no classes, no findings, offline, error).
- **Animated Illustrations:** Lottie JSON for loading states (scanning animation, AI thinking dots, success checkmark).

---

## 9. Information Architecture

### 9.1 App Structure
```
CodeGuard AI
├── Public Space (No Auth)
│   ├── Landing Page
│   ├── Guest Demo
│   ├── Knowledge Base (Articles + Detail)
│   └── Shared Report (Token-based)
├── Authentication Space
│   ├── Login
│   ├── Register
│   ├── Forgot Password
│   └── Reset Password
├── Developer Space (Auth + Developer Role)
│   ├── Dashboard
│   ├── Scan Upload
│   ├── Scan Progress (Transient)
│   ├── Report Viewer
│   ├── Scan History
│   └── Settings (Profile, Password, Preferences)
├── Instructor Space (Auth + Instructor Role)
│   ├── Dashboard (Instructor Variant)
│   ├── My Classes
│   ├── Class Detail / Metrics
│   └── Shared Student Reports
└── Admin Space (Auth + Admin Role)
    ├── Dashboard (Admin Variant)
    ├── User Management
    ├── System Health
    └── System Event Logs
```

### 9.2 Navigation Hierarchy
```
📂 Dashboard (Home)
📂 Scan
   ├─ New Scan
   └─ Scan Progress (auto-redirects)
📂 Reports
   ├─ Scan History
   ├─ Report Viewer
   └─ Shared Report (public)
📂 Instructor (Instructor/Admin)
   ├─ My Classes
   ├─ Class Detail
   └─ Class Metrics
📂 Admin (Admin only)
   ├─ User Management
   ├─ System Health
   └─ Event Logs
📂 Knowledge Base
   ├─ Article List
   └─ Article Detail
⚙️ Settings
   ├─ Profile
   ├─ Password
   └─ Preferences
```

### 9.3 Content Organization
- **Privacy-First Messaging:** "Zero code storage" assurance appears on Upload, Scan Progress, and Report Viewer screens — never buried in a footer.
- **Educational Content:** Knowledge Base articles are linked from findings (deep-link), dashboard recommendations, and the footer.
- **Action Hierarchy:** Primary actions (Start Scan, Apply Fix) are visually dominant. Secondary actions (Share, Export) are accessible but subdued. Tertiary actions (View Logs, Delete) are ghost buttons or hidden in overflow menus.

### 9.4 User Pathways
- **Guest -> Registered:** Landing → Demo → (Demo Report) → Registration Prompt → Register → Onboarding → First Scan → Report → Fix Applied.
- **Developer Daily:** Login → Dashboard → New Scan → Report → Apply Fix → Export PDF → History (trend check) → Logout.
- **Instructor Weekly:** Login → Dashboard → Class Metrics → Filter by SQL Injection → Review At-Risk Students → Open Shared Report → Prepare Lecture Notes.
- **Admin Reactive:** Login → System Health (red indicator) → Event Logs → Identify Pattern → Purge Orphaned Containers → Return to Health (green indicator).

### 9.5 Screen Relationships
- **Dashboard** is the hub; all primary features branch from it within 1 click.
- **Report Viewer** is the deepest screen in the core workflow. It links back to History and forward to Knowledge Base.
- **Scan Progress** is a transient bridge; it has no independent navigation value and auto-redirects on completion.
- **Settings** is a dead-end leaf; users return to their previous screen after making changes.

---

## 10. User Journey Design

### 10.1 Guest User Journey
| Stage | Screen | Action | Emotional State | Design Response |
|---|---|---|---|---|
| Discovery | Landing Page | Reads hero value prop, sees "Try Demo" | Curious, skeptical | Clean hero with animated code vulnerability visualization. Trust badges below fold. |
| Exploration | Guest Demo | Selects sample code, clicks "Run Scan" | Engaged, testing | Pre-loaded samples reduce friction. No form fields required. |
| Realization | Demo Report | Sees AI explanation + diff viewer | Surprised, impressed | Highlight the explanation card with a glow effect. Make the diff viewer the visual centerpiece. |
| Conversion | Post-Demo Banner | Clicks "Create Free Account" | Motivated | Sticky bottom banner with social proof: "Join 500+ students using CodeGuard." |
| Registration | Register Page | Fills short form | Hopeful | Minimal fields (4 inputs). Password strength meter provides real-time feedback. |
| First Value | Onboarding Scan | Uploads own file, gets report | Confident | Celebration micro-animation on first scan completion. |

### 10.2 New User Journey (First-Time Developer)
| Stage | Action | Thought | Friction Point | UX Solution |
|---|---|---|---|---|
| **Entry** | Logs in after registration | "Okay, what's first?" | Unclear starting point | Dashboard CTA is a massive, colorful "New Scan" card. No competing CTAs. |
| **Upload** | Drags `app.py` | "Is this safe? Will they keep my code?" | Privacy anxiety | Shield icon + "Your code is never stored" banner directly above the dropzone. Animated lock icon during upload. |
| **Wait** | Watches progress | "This is taking a while..." | Scan latency anxiety | Real-time WebSocket progress with human-friendly messages ("Teaching the AI about your code..."). |
| **Report** | Sees 3 findings | "Oh no, my code is bad." | Shame / anxiety | Positive framing: "We found 3 opportunities to make your code safer." Green "safe" lines shown alongside red "flagged" lines. |
| **Learn** | Reads AI explanation | "So *that's* why string concatenation is bad!" | Cognitive load | Explanation uses bold keywords, bullet points, and max 3 short paragraphs. |
| **Fix** | Clicks "Apply Fix" | "Will this break my code?" | Fear of automation | AST validation badge (green checkmark: "Fix verified by parser") shown *before* apply button. Preview diff is mandatory first step. |
| **Celebrate** | Fix applied | "I fixed a security bug by myself!" | Pride | Toast: "Fix applied and validated. You're getting safer!" Dashboard trend chart updates immediately. |

### 10.3 Returning User Journey
| Stage | Action | Thought | Design Response |
|---|---|---|---|
| **Entry** | Logs in | "Let me check how my code improved." | Dashboard shows trend sparkline and "Recent Scans" list immediately. |
| **Quick Scan** | Pastes snippet | "Just a quick check before PR." | Global `Cmd+K` search opens directly to "New Scan." Monaco editor auto-focuses. |
| **Review** | Views report | "Same XSS again? I need to learn this properly." | Finding card links directly to Knowledge Base article. "You've seen this 3 times" badge encourages KB reading. |
| **Batch Review** | Applies multiple fixes | "Let me clean this up fast." | Future: batch-select findings with checkboxes and "Apply Selected Fixes" action. |
| **Export** | Downloads PDF | "Attaching to Jira ticket." | Export is one-click from Report Viewer header. Toast provides download link without blocking navigation. |
| **Track** | Views history | "My critical findings are down 50%." | Trend chart defaults to 30-day view with a positive delta indicator (e.g., "↓ 50% Critical" in green). |

### 10.4 Instructor Journey
| Stage | Action | Thought | Friction Point | UX Solution |
|---|---|---|---|---|
| **Entry** | Logs in | "How is my class doing overall?" | Data scattered across individual reports | Instructor dashboard shows class cards with aggregate severity badges. |
| **Overview** | Clicks class card | "Which vulnerability is most common?" | No class-wide view exists in competing tools | Horizontal bar chart of vulnerability types. Clicking a bar filters the student list. |
| **Drill-down** | Filters by Critical, last 7 days | "Who needs help urgently?" | Identifying at-risk students manually is slow | Student list sorted by "most critical findings." Red avatar ring for students with >3 critical issues. |
| **Review** | Opens student report | "Let me see what the AI told them." | Switching contexts between class view and report | Report opens in a side drawer (desktop) instead of full page transition, preserving class context. |
| **Action** | Exports metrics PDF | "I need this for my lecture slides." | No exportable classroom view | "Export Class Report" generates a formatted PDF with charts and student summaries. |

### 10.5 Admin Journey
| Stage | Action | Thought | Design Response |
|---|---|---|---|
| **Monitor** | Opens System Health | "Are we running out of LLM quota?" | Dense metric cards: API requests/min, token usage bar with threshold warning, container counts. |
| **Alert** | Sees yellow warning | "Container failure rate is up." | Clicking the metric card auto-filters Event Logs to `container_failure` events. |
| **Remediate** | Purges orphaned containers | "Clean this up now." | One-click action button with confirmation. Success toast shows count of cleaned containers. |
| **Manage** | Reviews user list | "Any locked accounts to unlock?" | Table with inline actions (activate/deactivate) and bulk select. No modals for simple toggles. |

---

## 11. Screen Design Requirements

### 11.1 Landing Page
- **Purpose:** Convert visitors into registered users or demo participants.
- **Layout:** Single-page scroll with anchored sections.
  - **Hero:** Full-viewport height. Left: headline + subheadline + dual CTAs ("Get Started" primary, "Try Demo" secondary). Right: animated code vulnerability visualization (Lottie or canvas-based AST tree growing and being flagged).
  - **Social Proof:** "Trusted by 500+ students at UCP" with university logo.
  - **Feature Grid:** 3 cards (AI Explanations, One-Click Fixes, Privacy-First).
  - **Comparison Table:** Visual comparison against SonarQube, Bandit, ESLint (checkmarks vs. X marks).
  - **Persona Testimonials:** Zara, Raza, Dr. Ahmed quotes with avatar placeholders.
  - **Footer:** Knowledge Base link, GitHub repo link (MIT license), contact.
- **UX Priorities:** Trust, clarity, speed. Hero must load in <1.5s.
- **Responsive:** Mobile stacks to single column. Hero CTAs become full-width stacked buttons. Animated visualization replaced with static illustration on low-power devices.
- **Accessibility:** Skip-to-content link. All CTAs have visible focus rings. Testimonial avatars have alt text.

### 11.2 Login Page
- **Purpose:** Authenticate existing users with minimal friction.
- **Layout:** Centered card (max-width 420px) on a subtle gradient background (`--color-bg-base` to slightly lighter center). Left side of large screens shows a product illustration.
- **Components:** Email input (auto-focus), password input with visibility toggle, "Remember me" checkbox, "Forgot password?" link, Submit button, "Don't have an account? Register" link.
- **UX Priorities:** Speed, error clarity, security assurance.
- **Responsive:** Card becomes full-width with 16px padding on mobile.
- **Accessibility:** Focus starts on email. Password toggle has `aria-label="Show password"`. Error messages linked via `aria-describedby`.
- **Loading State:** Button shows spinner; inputs disabled.
- **Error State:** Inline error below failed field. Account lockout triggers a modal with countdown timer.

### 11.3 Register Page
- **Purpose:** Account creation with role selection.
- **Layout:** Same centered card pattern as Login, slightly taller (max-width 480px).
- **Components:** Full Name, Email, Password (with real-time strength meter), Confirm Password, Role radio group (Developer / Instructor), Terms checkbox, Submit.
- **UX Priorities:** Reduce abandonment. Password strength meter must feel encouraging, not punitive.
- **Responsive:** Same as Login.
- **Accessibility:** Radio group wrapped in `fieldset` with `legend`. Strength meter announced via `aria-live="polite"`.
- **Success State:** Toast "Account created! Welcome to CodeGuard AI." + auto-redirect to Dashboard after 1 second (user is authenticated via registration response token, no separate login needed).

### 11.4 Dashboard
- **Purpose:** Role-specific command center.
- **Layout:** Sidebar + Header + Content Grid.
  - **Developer:** 3-column grid (desktop). Col 1: "New Scan" hero card + recent scans list. Col 2: Vulnerability trend sparkline card + Knowledge Base recommendation. Col 3: Quick tips / achievements.
  - **Instructor:** 2-column grid. Col 1: Class cards (2-up). Col 2: Class-wide vulnerability heatmap + recent shared reports.
  - **Admin:** 4-column metric cards (containers, API usage, users, events) + full-width critical events table.
- **UX Priorities:** Information scent. Every card should make the user want to click deeper.
- **Responsive:** Mobile becomes a single-column stack. Cards maintain internal structure but reflow.
- **Accessibility:** All cards are keyboard-navigable (`tabindex="0"` with Enter to activate). Charts have `aria-label` describing the data trend.
- **Empty State (Developer):** Large illustration of a shield with a magnifying glass. Text: "No scans yet. Let's find your first security opportunity." Primary CTA: "Upload Code."
- **Loading State:** Skeleton cards with shimmer effect (never use spinners for dashboard loads).

### 11.5 New Scan Page
- **Purpose:** Initiate a scan with maximum privacy assurance.
- **Layout:** Centered content (max-width 800px). Top: privacy assurance banner (sticky, dismissible). Middle: tab switcher (Upload | Paste). Bottom: action bar.
- **Components:**
  - **Upload Tab:** Drag-and-drop zone (dashed border, 2px, `--color-border`; active state changes to `--color-primary-500` solid border with background tint). File list chips with remove buttons. Max size helper text.
  - **Paste Tab:** Monaco Editor instance (min-height 400px). Language mode toggle (Python/JS). "Load Sample" ghost button for quick testing.
- **UX Priorities:** Trust, speed, clarity.
- **Responsive:** Mobile drops drag-and-drop in favor of a native file input. Monaco editor height reduces to 300px.
- **Accessibility:** Dropzone has `role="button"`, `tabindex="0"`, and responds to Enter/Space. Monaco editor has `aria-label="Code editor"`.
- **Error State:** Inline banner in dropzone for invalid file type or size. Shake animation on the dropzone for error.
- **Loading State:** "Start Scan" button transitions to spinner with text "Uploading..."

### 11.6 Scan Progress Page
- **Purpose:** Real-time feedback and anxiety reduction during scan execution.
- **Layout:** Centered card (max-width 640px). Top: animated illustration (shield with scanning radar). Middle: progress stepper + progress bar. Bottom: live log stream (collapsible) + cancel button.
- **Components:**
  - **Stepper:** 5 steps (Queue → Parse → Analyze → Validate → Complete). Active step highlighted with `--color-primary-500`. Completed steps show checkmarks.
  - **Progress Bar:** 8px height, rounded, `--color-primary-500` fill, animated with CSS transition.
  - **Status Text:** Human-friendly, rotating messages: "Spinning up secure container..." → "Parsing your code's structure..." → "Teaching the AI about your patterns..."
  - **Log Stream:** Monospace font, 12px, `--color-text-tertiary`. Collapsed by default. Expandable via "View Logs" ghost button.
- **UX Priorities:** Transparency, perceived speed, user control.
- **Responsive:** Mobile maintains same centered layout. Progress bar remains 8px (thumb-friendly is irrelevant here).
- **Accessibility:** `aria-live="polite"` region announces stage changes. Progress bar uses `role="progressbar"` with `aria-valuenow`.
- **Error State:** Stepper turns red at failed stage. Detailed error message with "Retry" or "Contact Admin" actions.
- **Success State:** 1-second pause with completion checkmark animation, then auto-redirect to Report Viewer.

### 11.7 Report Viewer Page (The Product Centerpiece)
- **Purpose:** Interactive security report — the core differentiator.
- **Layout:** Full-width, no max-width constraint (developers use wide screens). Three zones:
  - **Header Bar:** Sticky top. Left: filename + language badge + LOC. Center: severity summary chips (Critical / High / Medium / Low counts). Right: Export PDF, Export JSON, Share, Back.
  - **Main Content:** Split-pane (desktop). Left 55%: Monaco read-only code view with vulnerability gutter markers. Right 45%: Findings panel.
  - **Finding Detail (Right Pane):** Expandable cards. Each card: CWE badge, severity badge, confidence %, line range, vulnerability type, AI explanation (bulleted), "Preview Fix" button, "View in KB" link.
  - **Diff Viewer (Modal/Inline):** Side-by-side original vs. suggested code. Syntax highlighting. "Apply Fix" (primary) + "Reject" (secondary) buttons.
- **UX Priorities:** Learnability, trust, actionability.
- **Responsive:**
  - Tablet: 50/50 split.
  - Mobile: Full-width code view; findings as a bottom sheet drawer (draggable to 50% or 100% height).
- **Accessibility:**
  - Code view: `role="region"` with `aria-label="Vulnerable code"`.
  - Gutter markers: each marker is a button with `aria-label="Critical finding at line 42"`.
  - Findings panel: `aria-live="polite"` announces when a fix is applied.
- **Loading State:** Skeleton code editor + shimmer findings list. Never show a blank screen.
- **Empty State:** "No vulnerabilities found! Your code looks solid." with a celebratory illustration and a "Share Success" CTA.
- **Error State:** "Failed to load report" with retry button and link to history.

### 11.8 Scan History Page
- **Purpose:** Review past scans and track improvement.
- **Layout:** Full-width content. Top: filter bar (language, severity, date range). Below: trend chart (full width, 240px height). Below: scan cards or table.
- **Components:**
  - **Trend Chart:** Line chart with 4 lines (Critical, High, Medium, Low) over time. Interactive hover tooltips.
  - **Scan Cards:** Filename, date, language badge, total findings, severity breakdown mini-bars, actions (View, Share, Delete).
- **UX Priorities:** Retrospection, motivation, quick access.
- **Responsive:** Mobile switches cards to a compact list with swipe-to-delete (optional).
- **Accessibility:** Chart has `aria-label` summarizing the trend. Scan cards are keyboard-navigable.
- **Empty State:** "No scan history yet. Your security journey starts with a single scan." CTA to New Scan.

### 11.9 Shared Report (Public View)
- **Purpose:** Read-only report for external stakeholders without auth.
- **Layout:** Simplified Report Viewer. No sidebar. No header navigation. Sticky banner at top: "Shared Report — Read Only" with owner name and scan date.
- **Components:** Same code view and findings panel as authenticated view, but "Apply Fix" button is hidden. Export disabled.
- **UX Priorities:** Trust (recipient knows it's safe to open), clarity, conversion.
- **Responsive:** Same as Report Viewer.
- **Conversion Element:** Floating bottom banner (mobile) or right-side panel (desktop): "Want to scan your own code? Create a free account." with dismiss button.
- **Accessibility:** Same standards as authenticated view.

### 11.10 Instructor Panel — Class List
- **Purpose:** Manage classes.
- **Layout:** Grid of class cards (3-up desktop, 1-up mobile). Top: "Create Class" primary button.
- **Components:**
  - **Class Card:** Class name, student count, avg severity badge, join code (with copy-to-clipboard icon), "View Metrics" link, "Delete" overflow menu.
- **UX Priorities:** Class creation must take < 30 seconds. Join code must be instantly copyable.
- **Responsive:** Cards stack vertically on mobile.
- **Accessibility:** Copy button has `aria-label="Copy join code"`. Delete requires confirmation modal.
- **Empty State:** "No classes yet. Create your first class to invite students."

### 11.11 Instructor Panel — Class Metrics
- **Purpose:** Deep-dive into class security posture.
- **Layout:** 2-column (desktop). Left: metrics charts (stacked vertically). Right: student list.
- **Components:**
  - **Vulnerability Type Distribution:** Horizontal bar chart (SQLi, XSS, Secrets, etc.).
  - **Severity Trend:** Line chart over selected date range.
  - **Most Common Issues:** Ranked table.
  - **Student List:** Avatar, name, latest scan date, findings count, severity badge, link to shared report.
- **UX Priorities:** Data density for analytical users. Filters must be instantly responsive.
- **Responsive:** Mobile stacks charts and student list vertically. Charts become full-width.
- **Accessibility:** Charts have `aria-label` summaries. Student list is sortable via keyboard.
- **Empty State:** "No student submissions yet. Share the join code to get started." with a prominent copy-code button.

### 11.12 Admin Panel — User Management
- **Purpose:** CRUD on user accounts.
- **Layout:** Full-width data table with sticky header.
- **Components:**
  - **Toolbar:** Search input, role filter dropdown, status filter, "Export CSV" secondary button.
  - **Table:** Avatar + name, email, role badge, status badge, created date, actions (Activate/Deactivate, Delete).
  - **Bulk Actions:** Checkbox column; top toolbar updates to "X selected" with bulk deactivate/delete.
- **UX Priorities:** Efficiency, safety. Destructive actions require confirmation.
- **Responsive:** Mobile converts table to card list with key-value pairs.
- **Accessibility:** Table uses semantic `table`, `th`, `tr`. Sortable headers have `aria-sort`.
- **Loading State:** Skeleton table rows.

### 11.13 Admin Panel — System Health
- **Purpose:** Real-time operational monitoring.
- **Layout:** 4-column metric cards (desktop, 2-up tablet, 1-up mobile). Below: live-updating charts.
- **Components:**
  - **Metric Cards:** Container count (with green/yellow/red dot), API requests/min, LLM token usage (progress bar to quota), active users.
  - **Charts:** Container state transitions, API latency percentiles.
  - **Provider Status:** 3 cards (OpenAI, Groq, Ollama) with status indicators.
  - **Actions:** "Purge Orphaned Containers" danger button.
- **UX Priorities:** Density, scan-ability, actionability.
- **Responsive:** Metric cards stack. Charts remain readable with reduced padding.
- **Accessibility:** Status dots have `aria-label` ("Healthy", "Degraded", "Down"). Live regions announce metric updates.
- **Error State:** "Metrics unavailable" card with retry button.

### 11.14 Knowledge Base Page
- **Purpose:** Educational resource.
- **Layout:** 2-column (desktop). Left 30%: category filters + search. Right 70%: article cards or article content.
- **Components:**
  - **Article Card:** Title, CWE badges, OWASP category, short description, reading time.
  - **Article Detail:** Markdown-rendered content. Vulnerable code block (syntax highlighted, labeled "❌ Vulnerable"). Safe code block (labeled "✅ Safe"). Related CWE references.
- **UX Priorities:** Readability, learning flow, deep-linking.
- **Responsive:** Mobile: filters become a top horizontal scroll or bottom sheet. Article content is single-column full-width.
- **Accessibility:** Code blocks have `aria-label="Vulnerable code example"`. Headings follow logical hierarchy (`h1` → `h2` → `h3`).
- **Empty State (Search):** "No articles found for 'X'. Try searching for 'SQL injection' or 'XSS'."

### 11.15 Guest Demo Page
- **Purpose:** Zero-commitment trial.
- **Layout:** Centered card (max-width 720px). Similar to New Scan but simplified.
- **Components:**
  - **Sample Selector:** Dropdown of 4 pre-loaded vulnerable samples (SQLi, XSS, Hardcoded Secrets, Unsafe Eval). Selecting updates the Monaco editor below.
  - **Monaco Editor:** Read-only for guest. Displays selected sample.
  - **"Run Demo Scan" button:** Primary, full-width.
- **UX Priorities:** Instant gratification. No typing required.
- **Responsive:** Same as New Scan.
- **Success State:** Simplified Report Viewer (no apply fix, no export). Banner: "This is a demo. Create an account to scan your own code."

### 11.16 Settings — Profile / Password / Preferences
- **Purpose:** User account management.
- **Layout:** 2-column (desktop). Left 25%: settings navigation (vertical tabs). Right 75%: form content.
- **Components:**
  - **Profile:** Editable name, read-only email, avatar upload (optional).
  - **Password:** Current password (required), new password, confirm. Strength meter on new password.
  - **Preferences:** Theme toggle (Light / Dark / System), notification toggles (future).
- **UX Priorities:** Safety (password change requires current), instant feedback (save button becomes "Saved" with checkmark).
- **Responsive:** Mobile uses full-width vertical tabs or a dropdown selector.
- **Accessibility:** Theme toggle has `aria-pressed`. Form errors announced via `aria-live`.

### 11.17 Error Pages (404 / 403 / 500 / Offline)
- **Purpose:** Recover from failures gracefully.
- **Layout:** Centered content (max-width 480px). Full viewport height.
- **Components:**
  - **Illustration:** Contextual spot illustration (lost astronaut for 404, broken robot for 500, unplugged cable for offline).
  - **Headline:** Human-friendly, non-technical. "We couldn't find that page" instead of "404 Not Found."
  - **Subtext:** Helpful next step. "Check the URL or return to the Dashboard."
  - **CTA:** Primary button linking to Dashboard. Secondary button for "Go Back" (if history exists).
- **Accessibility:** Illustration has `alt=""` (decorative). Focus starts on the primary CTA.

---

## 12. Dashboard UX Strategy

### 12.1 Widget Layout
- **Grid System:** CSS Grid with responsive `auto-fill` behavior. Widgets have a minimum width of 320px and grow to fill available space.
- **Widget Types:**
  - **Hero CTA Widget:** Spans 2 columns on desktop. Large, colorful, single action. "New Scan" for developers; "Create Class" for instructors.
  - **Data Widget:** 1 column. Charts, metric cards, lists.
  - **Feed Widget:** 1 column. Recent scans, system events, notifications.
- **Reorder Logic (Future):** Users can drag-and-drop widgets to customize their dashboard. Layout persisted per user.

### 12.2 Data Hierarchy
- **Primary Data:** The metric the user cares about most. For developers = "Last Scan Findings." For instructors = "Class Average Severity." For admins = "Container Health." This gets the largest visual weight.
- **Secondary Data:** Supporting context. Trend sparklines, lists, comparison badges.
- **Tertiary Data:** Metadata and deep-links. Timestamps, "View All" links, KB recommendations.

### 12.3 Analytics Presentation
- **Sparklines:** Small, inline, word-sized graphics (trend lines without axes) used in cards to show directionality at a glance.
- **Delta Badges:** "↓ 50% Critical" or "↑ 2 High" next to metrics. Green for improvement (downward severity), red for deterioration.
- **Tooltips:** All charts and metric cards provide detailed breakdowns on hover/focus.
- **Time Range Defaults:** 7 days for developers, 30 days for instructors, 24 hours for admins. Customizable via dropdown.

### 12.4 Card Systems
- **Uniform Padding:** 24px internal padding across all dashboard cards ensures visual rhythm.
- **Visual Grouping:** Related cards share a subtle background tint (e.g., all "Class Metrics" cards have a `--color-secondary-50` 5% opacity background).
- **Interactive Cards:** Hovering a data card reveals additional actions (e.g., "Export" or "Filter" buttons) to reduce permanent UI clutter.

### 12.5 Filtering UX
- **Filter Bar:** Sticky below the header on list screens. Uses pill-shaped filter chips that can be added/removed. Active filters are reflected in the URL.
- **Filter Panel:** Slide-in drawer (desktop) or bottom sheet (mobile) for complex multi-select filters. "Apply" and "Clear All" actions at the bottom.
- **Instant Feedback:** Filter changes trigger immediate data refresh with skeleton loaders. No "Apply" button needed for single-select filters.

### 12.6 Table UX
- **Sticky Headers:** Table headers stick to the top of the viewport when scrolling through long lists (admin user table, system logs).
- **Row Hover:** Subtle background color change on hover. Clicking anywhere on the row navigates to detail view (unless a row contains explicit action buttons).
- **Empty Rows:** Never show a completely blank table. At minimum, show an empty state illustration centered within the table bounds.
- **Pagination:** Cursor-based "Load More" for scan history (encourages scrolling). Numbered pagination for admin tables (jump-to-page is useful for dense data).

### 12.7 AI Assistant Placement
- **Dashboard AI Tip (Future):** A small card on the developer dashboard: "Tip of the day: Using `f-strings` with user input? Try parameterized queries instead." This positions the AI as a proactive mentor, not just a reactive scanner.
- **Report Viewer AI Badge:** Every finding prominently displays a sparkle icon + "AI Explained" badge to build trust and differentiate AI-enriched findings from raw AST flags.

---

## 13. AI UX Design

### 13.1 AI Interaction Patterns
- **Deterministic Trigger:** The AI is not a chatbot the user freely queries. It is triggered by the scan engine and presents results in structured cards. This reduces user anxiety ("What should I ask?") and ensures consistent output quality.
- **Structured Output Cards:** AI responses are not free-form text blocks. They are templated cards with fixed sections: "What we found," "Why it's risky," "How to fix it," and "Learn more."
- **Progressive Detail:** Default view shows a 2-sentence summary. "Expand" reveals the full explanation. This respects power users and beginners simultaneously.

### 13.2 Prompt Input UX (Future / Not Phase 1)
- If a future version adds a chat interface for follow-up questions:
  - Input bar fixed at bottom of explanation panel.
  - Placeholder: "Ask a follow-up... (e.g., 'Why is this better than escaping?')"
  - Send button activates only when input is non-empty.
  - Character limit indicator (max 200 chars for concise follow-ups).

### 13.3 Streaming Response Design
- **Phase 1 (Non-Streaming):** AI explanations are awaited in full before display. Show an animated "AI is analyzing..." skeleton card with a pulsing gradient to indicate active thought.
- **Phase 2 (Streaming):** If provider supports SSE, tokens stream into the explanation card word-by-word. A subtle cursor blink (`|`) at the end of the streaming text signals ongoing generation.

### 13.4 AI Suggestions
- **Fix Suggestion Card:**
  - Header: "Suggested Fix" with `wand-2` icon.
  - Body: Side-by-side diff viewer (original left, fixed right).
  - Footer: "Validated by AST parser" badge (green shield + checkmark) + "Preview" and "Apply" buttons.
- **Alternative Suggestions:** If the first fix fails validation, the card updates to show "Attempt 2 of 2" with a new diff. If both fail, the card transforms into a "Manual Guidance" state linking to the KB.

### 13.5 Context Awareness
- **Language Context:** The AI explanation adapts its terminology to the detected language. A Python SQLi explanation mentions `cursor.execute()` and parameter tuples. A JS XSS explanation mentions `textContent` vs. `innerHTML`.
- **User Proficiency Context (Future):** If a user has fixed 10+ SQLi issues, the AI switches to advanced mode: shorter explanations, references to CWE subtypes, and links to defensive design patterns.

### 13.6 AI Loading States
- **Scan Progress Stage "AI Analysis":** Progress bar pauses at 70% with a message "Teaching the AI about your code's structure..." and an animated brain/sparkle icon.
- **Explanation Card Loading:** Skeleton card with 3 shimmering lines (mimicking bullet points) and a pulsing "AI is thinking..." label.
- **Fix Validation Loading:** Inline spinner next to the "Apply Fix" button with text "Validating syntax..." This takes 1-2 seconds and builds trust by making validation visible.

### 13.7 AI Feedback Systems
- **Fix Feedback (Future):** After applying a fix, a subtle inline prompt appears: "Was this fix helpful? 👍 / 👎". Thumbs-down triggers a fallback to alternative suggestions or a "Report bad fix" flow.
- **Explanation Feedback (Future):** Small "Was this clear?" rating below each explanation. Aggregated for LLM prompt tuning.

### 13.8 AI Trust Indicators
- **Confidence Meter:** A 10-segment horizontal bar next to every finding. Filled segments color-coded: red (1-4), yellow (5-7), green (8-10). Tooltip: "The AI is 85% confident in this assessment. Low confidence may indicate an unusual code pattern."
- **AST Validation Badge:** Green checkmark with "Syntax verified" text appears on every fix suggestion. This is the ultimate trust signal — it proves the AI's output was checked by a deterministic system.
- **Fallback Banner:** If the LLM is unavailable, a non-blocking yellow banner appears at the top of the report: "AI insights are temporarily unavailable. Severity scores are rule-based. Scan again later for AI explanations." This honesty builds more trust than hiding failures.
- **Privacy Shield:** A persistent shield icon in the report header with tooltip: "Your source code was analyzed in an isolated container and permanently deleted after this scan."

---

## 14. Mobile UX Strategy

### 14.1 Responsive Behavior
- **Breakpoint Strategy:**
  - **Mobile First:** Design for 375px width first, then scale up.
  - **Tablet (768px+):** Sidebar becomes icon-only. Split-pane report viewer becomes 50/50.
  - **Desktop (1024px+):** Full sidebar, maximum content width 1280px centered.
- **Fluid Typography:** Root font size scales from 14px (mobile) to 16px (desktop) using `clamp()`.

### 14.2 Mobile-First Adaptations
- **Scan Upload:** Drag-and-drop is replaced by a native file input button. "Paste Code" becomes the primary tab because mobile file management is cumbersome.
- **Report Viewer:** Code view is full-width. Findings become a bottom sheet drawer (draggable from the bottom edge) that can snap to 30% (peek), 50% (balanced), or 100% (full focus) height.
- **Dashboard:** 1-column card stack. Trend chart becomes a horizontal scroll if too wide.
- **Tables:** Convert to card lists with key-value pairs. Admin user table becomes a vertical stack of user cards.

### 14.3 Gesture Interactions
- **Pull to Refresh:** On Scan History and Dashboard.
- **Swipe Actions:** History items support swipe-left to reveal "Delete" and "Share" actions. Haptic feedback on supported devices.
- **Pinch to Zoom:** Disabled on code view (Monaco handles its own zoom). Enabled on shared report PDF view.
- **Bottom Sheet Drag:** Report findings drawer can be dragged up/down with rubber-band physics at the snap points.

### 14.4 Bottom Navigation (Optional for PWA)
If the app is installed as a PWA, a bottom tab bar improves thumb-reachability:
- Tabs: Home (Dashboard), Scan, History, KB, Profile.
- Active tab: Primary color icon + label.
- Center tab (Scan): Raised circular button for prominence.

### 14.5 Touch Targets
- **Minimum:** 44x44px for all interactive elements (Apple HIG / Material Design standard).
- **Buttons:** 48px height on mobile.
- **List Items:** 56px minimum height for comfortable tapping.
- **Input Fields:** 48px height with 16px font size to prevent iOS zoom on focus.

### 14.6 Performance Considerations
- **Lazy Load Monaco:** Only load the editor when the user navigates to a scan page. Use a lightweight textarea fallback if Monaco fails to load within 3 seconds on slow networks.
- **Image Optimization:** All spot illustrations served as WebP with LQIP (Low-Quality Image Placeholder) blur-up.
- **Reduced Data Mode (Future):** If user enables "Data Saver," disable charts, load text-only reports, and compress KB article images.

---

## 15. Accessibility Requirements

### 15.1 WCAG 2.1 AA Compliance
All screens must meet the following criteria:
- **1.4.3 Contrast (Minimum AA):** Text > 4.5:1 against background. Large text > 3:1.
- **1.4.11 Non-text Contrast (AA):** UI components (buttons, icons, focus rings) > 3:1 against adjacent colors.
- **2.1.1 Keyboard (A):** All functionality operable via keyboard.
- **2.4.7 Focus Visible (AA):** Focus indicators are always visible and distinct.
- **4.1.2 Name, Role, Value (A):** All interactive elements have accessible names and roles.

### 15.2 Keyboard Navigation
- **Global Shortcuts:**
  - `Tab` / `Shift+Tab`: Navigate focusable elements.
  - `Enter` / `Space`: Activate buttons, open modals, expand findings.
  - `Escape`: Close modals, dropdowns, drawers, toasts.
  - `Cmd/Ctrl + K`: Open global search.
  - `Cmd/Ctrl + B`: Toggle sidebar.
- **Report Viewer Shortcuts:**
  - `J` / `K`: Navigate to next/previous finding (Vim-inspired, beloved by developers).
  - `P`: Preview fix for selected finding.
  - `A`: Apply fix for selected finding (with confirmation).
- **Skip Links:** "Skip to main content" link is the first focusable element on every page.

### 15.3 Screen Reader Support
- **Semantic HTML:** Use `header`, `nav`, `main`, `section`, `article`, `footer` correctly.
- **Headings:** Exactly one `h1` per page. Logical hierarchy (no skipping levels).
- **Landmarks:** Sidebar is `nav` with `aria-label="Main navigation"`. Content is `main`.
- **Live Regions:**
  - Scan progress announcements: `aria-live="polite"` region.
  - Toast notifications: `aria-live="assertive"` region.
  - Fix application result: `aria-live="polite"`.
- **Icons:** All decorative icons have `aria-hidden="true"`. All functional icons have `aria-label`.
- **Charts:** All Recharts charts wrapped in a `figure` with `figcaption` describing the data trend in plain text.

### 15.4 Focus States
- **Focus Ring:** 2px solid `--color-primary-500` with 2px offset (`outline: 2px solid; outline-offset: 2px`).
- **Focus Visible Only:** Use `:focus-visible` (not `:focus`) to prevent focus rings on mouse clicks.
- **Modal Focus Trap:** When a modal opens, focus moves to the modal title. `Tab` cycles within the modal. On close, focus returns to the trigger element.
- **Page Change:** On route transition, focus programmatically moves to the `h1` of the new page (Route Announcer pattern).

### 15.5 Contrast Ratios
| Element | Foreground | Background | Ratio | Status |
|---|---|---|---|---|
| Body text (dark) | `#F1F5F9` | `#0F1117` | 15.8:1 | ✅ |
| Body text (light) | `#0F172A` | `#F8FAFC` | 16.2:1 | ✅ |
| Primary button text | `#FFFFFF` | `#2563EB` | 4.6:1 | ✅ |
| Critical badge text | `#FFFFFF` | `#DC2626` | 7.2:1 | ✅ |
| High badge text | `#FFFFFF` | `#EA580C` | 4.6:1 | ✅ |
| Warning badge text | `#0F172A` | `#F59E0B` | 3.2:1 | ⚠️ |

**Fix for Warning:** Use `#713F12` (dark amber) text on `#F59E0B` background to achieve 4.5:1.

### 15.6 Error Accessibility
- **Form Errors:** Inline errors linked to inputs via `aria-describedby`. Error text announced by screen readers on form submission.
- **Toast Errors:** `aria-live="assertive"` ensures immediate announcement. Includes actionable guidance: "Scan failed. Docker runtime unavailable. Please try again in 2 minutes."
- **Colorblind Safety:** Severity communicated via icon shape + text label, never color alone.

### 15.7 Motion Reduction
- **Respect `prefers-reduced-motion`:**
  - All transitions become instant (duration 0ms).
  - Progress bar animates without motion (instant fill to current value).
  - Skeleton screens replaced with static placeholder blocks.
  - Lottie animations paused or replaced with static frames.

---

## 16. Motion & Animation Guidelines

### 16.1 Transition Timing
- **Standard:** `200ms ease` for hover states, opacity fades, color changes.
- **Entrance:** `300ms cubic-bezier(0.16, 1, 0.3, 1)` (ease-out-expo) for modals, drawers, toasts. Feels snappy and premium.
- **Exit:** `150ms ease-in` for dismissals. Faster than entrance to feel responsive.
- **Page Transition:** `200ms fade` between routes. No sliding (can cause motion sickness).

### 16.2 Hover Effects
- **Cards:** `translateY(-2px)` + border color transition. Duration: 200ms.
- **Buttons:** Background color darkens by one shade. No scale transforms (avoids layout shift).
- **Navigation Items:** Background fill + left border accent slide-in (width 0 to 4px, 150ms).
- **Links:** Underline expands from center-out (`transform: scaleX(0)` to `scaleX(1)`).

### 16.3 Loading Animations
- **Skeleton Screens:** Shimmer animation (`linear-gradient` mask moving horizontally) with `1.5s` duration, infinite. Used for cards, tables, and code editor initial load.
- **Spinners:** 16px or 24px rotating SVG circle (1.5 turns per second, `stroke-dashoffset` animation). Never use CSS `rotate` on heavy DOM elements.
- **Progress Bar:** Smooth width transition (CSS `transition: width 300ms ease`). If `prefers-reduced-motion`, instant jump.
- **AI Thinking:** 3 bouncing dots (scale pulse) inside the explanation card skeleton.

### 16.4 Page Transitions
- **Route Change:** Content area fades out (100ms) -> router changes -> content fades in (200ms). Prevents jarring blank flashes.
- **Dashboard to Report:** Because the report is the "destination" of a scan, use a subtle slide-up entrance for the report header to signal progression.

### 16.5 Micro-Interactions
- **Copy to Clipboard:** Icon briefly changes to a checkmark for 2 seconds with a green tint.
- **Apply Fix:** Button text changes from "Apply Fix" to "Applying..." to "Fixed ✓" with color transition from primary to success.
- **Delete:** Item fades out + shrinks (scale 1 to 0.95, opacity 1 to 0) over 200ms before removal from DOM.
- **Toggle Switches:** Thumb slides with a spring physics feel (`cubic-bezier(0.34, 1.56, 0.64, 1)` — slight overshoot).
- **Toast Stack:** New toasts slide up from 16px offset + fade in. Existing toasts in the stack gently shift up.

---

## 17. UX Writing Guidelines

### 17.1 Tone of Voice
- **Supportive Mentor, Not Drill Sergeant:** "We found an opportunity to strengthen your code" > "Vulnerability detected!"
- **Precise but Approachable:** Use technical terms ("SQL injection," "parameterized query") but always explain them in the same breath.
- **Humble about AI:** "The AI suggests..." rather than "The AI knows..." Include confidence percentages to manage expectations.
- **Active Voice, Second Person:** "You can apply this fix" rather than "The fix can be applied by the user."

### 17.2 Error Messages
- **Rule:** State what happened, why it matters, and what to do next.
- **Bad:** "Error 500."
- **Good:** "We couldn't complete your scan because the analysis engine is temporarily unavailable. Please try again in a few minutes."
- **Bad:** "Invalid input."
- **Good:** "Please enter a valid email address like name@example.com."

### 17.3 Empty States
- **Rule:** Never blame the user. Offer a clear next step.
- **Scan History Empty:** "No scans yet. Your security journey starts with a single upload." CTA: "Scan Your First File."
- **Report Empty (No Findings):** "No vulnerabilities found! Your code looks solid. 🎉" CTA: "Share Your Success."
- **Class Empty:** "No students have joined yet. Share your class code to get started." CTA: "Copy Join Code."

### 17.4 Notifications / Toasts
- **Success:** Short, celebratory. "Fix applied and verified."
- **Error:** Clear, actionable. "Scan failed: Docker engine offline. [Retry]"
- **Info:** Helpful context. "AI insights are temporarily unavailable. Rule-based scores shown instead."
- **Warning:** Caution without panic. "Your account will be locked for 15 minutes after 2 more failed attempts."

### 17.5 AI Messaging
- **Explanation Header:** "Why this code could be safer" (not "Vulnerability explanation").
- **Fix Header:** "Suggested improvement" (not "Fix suggestion").
- **Confidence Label:** "AI confidence: 94%" with tooltip "Based on pattern matching against known vulnerability databases."
- **Fallback Message:** "Our AI assistant is taking a break. We've scored this finding using deterministic rules instead." (Personifies the AI to make the fallback feel friendly, not broken.)

### 17.6 Button Labels
- **Primary Actions:** Start with a verb. "Start Scan," "Apply Fix," "Create Class," "Export PDF."
- **Secondary Actions:** Clear but subdued. "Preview Fix," "Share Report," "Load Sample."
- **Destructive Actions:** Explicit about consequences. "Delete Scan Permanently," "Deactivate User Account."
- **Ghost Actions:** Minimal verb. "Cancel," "Close," "Back."

### 17.7 CTA Guidelines
- **One Primary CTA Per Screen:** The most important action is visually dominant. All other actions are secondary or ghost.
- **CTA Proximity:** Primary CTA is placed at the end of the user's reading flow (bottom-right for forms, top-right for dashboards).
- **CTA Consistency:** The "Start Scan" button always looks the same, whether on Dashboard, New Scan, or Guest Demo.

---

## 18. Performance UX Considerations

### 18.1 Perceived Performance
- **Instant Feedback:** Button clicks trigger a visual response (color change, ripple, or spinner) within 100ms.
- **Optimistic UI:** Fix application updates the UI immediately to "Remediated" before API confirmation. Rollback with toast if server rejects.
- **Progressive Loading:** Report viewer loads findings list first (priority), then renders the Monaco editor (heavy) in a deferred microtask.

### 18.2 Lazy Loading UX
- **Images:** All illustrations below the fold use `loading="lazy"` with a 4px blurred LQIP placeholder.
- **Charts:** Recharts components loaded via `React.lazy()` and rendered only when scrolled into viewport (`IntersectionObserver`).
- **Monaco Editor:** Loaded on demand. Display a lightweight code preview (syntax-highlighted `pre` block) while Monaco chunks download.

### 18.3 Skeleton Loaders
- **Pattern:** Rounded rectangles matching the shape of final content. Never use generic spinners for page-level loads.
- **Color:** `--color-surface-2` base with `--color-surface-3` shimmer gradient.
- **Timing:** 1.5s shimmer loop. Once data loads, skeleton fades out (150ms) and content fades in (200ms).

### 18.4 Optimistic Updates
- **Fix Apply:** UI immediately shows green "Remediated" badge and updates the code view with the fixed version. If API returns error, revert badge to "Pending" and show toast: "Fix couldn't be applied. No changes were made."
- **Profile Update:** Name change reflects immediately in header avatar dropdown. Reverts on failure.
- **Delete Scan:** Item removed from list immediately. "Undo" toast appears for 5 seconds. If user clicks undo, item reappears and deletion is cancelled.

### 18.5 Progressive Rendering
- **Scan Report:** Findings rendered in batches of 5 if >20 findings total. User sees first 5 immediately; "Loading more..." indicator below.
- **Charts:** Render grid and axes first, then animate data series in (staggered 100ms per series).

---

## 19. Design Constraints

### 19.1 Technical Constraints
- **Monaco Editor Bundle Size:** ~2MB+ of JS. Must be code-split and loaded on demand. Fallback to plain `pre` blocks on slow networks.
- **React Query Cache:** UI must gracefully display stale cached data while refetching. Never block the UI on network requests.
- **WebSocket Fallback:** If WebSockets are blocked by university firewalls, the UI must seamlessly degrade to polling without user intervention.

### 19.2 Device Limitations
- **Mobile Code Editing:** Monaco is not touch-optimized. On mobile < 768px, use a readonly Monaco view or a lightweight textarea for paste mode.
- **Low-End Hardware:** Skeleton screens and reduced animation for devices with < 4GB RAM or CPU cores < 2 (detected via `navigator.hardwareConcurrency`).

### 19.3 Browser Compatibility
- **Target Browsers:** Chrome 110+, Firefox 110+, Safari 16+, Edge 110+ (latest stable releases).
- **CSS Features:** Use `@supports` for modern features (backdrop-filter, container queries). Graceful degradation for older browsers.
- **Monaco Compatibility:** Requires modern JS engine. IE11 not supported (explicitly out of scope).

### 19.4 Accessibility Limitations
- **Monaco Editor Accessibility:** While Monaco has ARIA support, it is not fully screen-reader-friendly for complex navigation. Provide a "Plain Text View" toggle for screen-reader users that renders the code in a standard `pre` block with line-by-line vulnerability annotations.
- **Colorblind Users:** Severity colors are paired with icons and text, but charts (pie/bar) may still be challenging. Use patterns (stripes, dots) in addition to colors for chart differentiation.

### 19.5 AI Interaction Limitations
- **LLM Latency:** Explanations cannot appear instantaneously. The UI must tolerate 5–30 seconds of waiting without user abandonment.
- **Hallucination Risk:** No AI output is shown without AST validation. The UI must clearly communicate when a fix is "AI-generated but verified" vs. "rule-based only."
- **Offline Mode:** If both cloud LLM and local Ollama are unavailable, the UI degrades to deterministic rule-based scoring. This must not feel like a broken experience.

---

## 20. Competitor Design Analysis

### 20.1 SonarQube
- **Strengths:** Comprehensive dashboards, mature data visualization, enterprise trust.
- **Weaknesses:** Dense, cluttered UI. Overwhelming for junior developers. Explanations are absent or require clicking through to external docs. Dark mode is an afterthought.
- **UX Opportunities:** SonarQube's "Hotspots" concept is good, but CodeGuard AI can beat it with inline AI explanations and one-click fixes. The visual density of SonarQube is antithetical to educational use.

### 20.2 GitHub Copilot
- **Strengths:** Seamless IDE integration, conversational AI, developer-native.
- **Weaknesses:** Security is not its primary focus. Suggestions are unvalidated and can introduce vulnerabilities. No reporting or trend tracking.
- **UX Opportunities:** Copilot's inline ghost-text suggestions are brilliant. CodeGuard AI can adopt a similar "ghost fix" preview in the diff viewer. Copilot lacks transparency — CodeGuard AI's confidence meters and validation badges fill that gap.

### 20.3 Bandit / ESLint (CLI Tools)
- **Strengths:** Fast, local, free.
- **Weaknesses:** Terminal output is inscrutable to beginners. No visualizations, no fixes, no history.
- **UX Opportunities:** CodeGuard AI's entire value proposition is built on transforming CLI output into a beautiful, actionable UI. The gap is massive.

### 20.4 Snyk
- **Strengths:** Good vulnerability database, fix suggestions.
- **Weaknesses:** Expensive. UI feels corporate and sales-heavy. Focuses on dependencies (SCA), not source code AST analysis.
- **UX Opportunities:** Snyk's PR fix suggestions are good, but CodeGuard AI targets the *developer learning moment* rather than the *DevOps pipeline moment*. The UX should feel like a tutor, not a gatekeeper.

### 20.5 Design Gaps in Market
- **No educational SAST tool** combines gamified progress, class dashboards, and explainable AI.
- **No competitor** uses ephemeral container privacy as a first-class UI message.
- **No competitor** provides an interactive, AST-validated diff viewer in a web UI.

---

## 21. Recommended Design Tools

### 21.1 Figma Structure
```
CodeGuard AI (Figma File)
├── 📁 Design Tokens
│   ├── Colors (Light + Dark)
│   ├── Typography
│   ├── Spacing
│   ├── Shadows
│   └── Icons (Lucide set)
├── 📁 Components
│   ├── Buttons (Variants: Primary, Secondary, Ghost, Danger, Success)
│   ├── Inputs (Text, Select, Textarea, Monaco Wrapper)
│   ├── Cards (Dashboard Card, Finding Card, User Card)
│   ├── Modals (Confirmation, Form, Drawer)
│   ├── Navigation (Sidebar, Header, Breadcrumbs, Bottom Nav)
│   ├── Data Display (Table, Chart Wrapper, Badge, Avatar)
│   ├── Feedback (Toast, Alert, Skeleton, Spinner)
│   └── AI Components (Explanation Card, Diff Viewer, Confidence Meter)
├── 📁 Screens
│   ├── Public (Landing, Login, Register, Demo, KB)
│   ├── Developer (Dashboard, New Scan, Progress, Report, History, Settings)
│   ├── Instructor (Dashboard, Classes, Metrics)
│   └── Admin (Dashboard, Users, Health, Logs)
├── 📁 Prototypes
│   ├── Guest → Registered Flow
│   ├── Scan → Fix Applied Flow
│   └── Instructor Review Flow
└── 📁 Assets
    ├── Illustrations (Empty states, error states)
    ├── Lottie Files (Loading, success)
    └── Brand (Logo, wordmark, social assets)
```

### 21.2 Component Organization
- **Atomic Design:** Organize components as Atoms (buttons, inputs), Molecules (finding cards, search bars), Organisms (report viewer, sidebar), Templates (page layouts), and Pages (final screens).
- **Variant-Driven:** Use Figma variants extensively. A single "Button" component should handle all states (default, hover, active, disabled, loading) via variant properties.

### 21.3 Design Tokens
- **Token Format:** Use Figma Variables for colors, spacing, and typography. Export to JSON via a plugin (e.g., Tokens Studio) for direct consumption by the Tailwind config.
- **Naming Convention:** `category/subcategory/variant/state` — e.g., `color/semantic/critical/default`, `component/button/primary/hover`.

### 21.4 Collaboration Workflow
- **Design System Governance:** One Figma file for the Design System (read-only for most designers, editable by Design System Lead). Separate Figma files for feature exploration.
- **Design Reviews:** Weekly design critiques using Figma comments. All screens must pass a "Colorblind Check" and "Keyboard Navigation Check" before handoff.
- **Handoff Strategy:**
  - Use Figma Dev Mode for CSS inspection, asset export, and spacing measurements.
  - Link each screen to the corresponding App Flow Document section.
  - Provide annotated frames for complex interactions (e.g., WebSocket state transitions, drag-and-drop behavior).

### 21.5 QA Alignment
- **Design QA Checklist:** Before a feature is considered "designed," verify:
  - [ ] All states designed (default, hover, active, disabled, loading, empty, error, success).
  - [ ] Dark mode variant exists.
  - [ ] Mobile breakpoint (<768px) designed.
  - [ ] Accessibility annotations added (focus order, ARIA labels, alt text).
  - [ ] Animation specs documented (duration, easing, trigger).

---

## 22. Future UX Enhancements

### 22.1 AI Personalization
- **Adaptive Explanations:** The AI adjusts explanation depth based on user history. A beginner sees analogies; an advanced user sees CWE subtypes and references to secure design patterns.
- **Custom Vocabulary:** Users can opt into "Strict Technical Mode" (no analogies) or "ELI5 Mode" (heavy analogies, simple language).

### 22.2 Smart Recommendations
- **Proactive Scan Suggestions:** "You usually scan your `auth.py` on Mondays. Want to run a scheduled scan?"
- **KB Article Recommendations:** Dashboard card: "You've had 3 XSS findings this month. Read 'Modern XSS Defense' →"
- **Fix Pattern Learning:** If a user consistently rejects a certain type of AI fix, the system notes this and requests alternative patterns from the LLM.

### 22.3 Adaptive UI
- **Role-Based Dashboards:** The dashboard widget layout auto-configures based on role. If an instructor hasn't created a class yet, the "Create Class" hero takes up 2 columns. After creation, it shrinks to a standard card and metrics widgets expand.
- **Time-of-Day Adaptation:** If the user scans at 2 AM, reduce animation intensity and default to darker surface colors (future: auto ` prefers-color-scheme` detection).

### 22.4 Voice Interfaces (Future)
- **Voice Command:** "Hey CodeGuard, scan my last file." or "Explain CWE-89."
- **Screen Reader Enhancement:** AI explanations could be read aloud with a natural-sounding TTS voice, turning the report into an audio security briefing.

### 22.5 AR/VR Support (Very Future)
- **Immersive Code Review:** In a VR workspace (Apple Vision Pro, Meta Quest), the report viewer floats as a 3D panel next to the IDE. Findings appear as glowing annotations on the code "in space."

### 22.6 Gamification
- **Achievement Badges:** "First Scan," "Fix Master" (10 fixes), "Security Scholar" (read 5 KB articles), "Clean Slate" (10 scans with 0 findings).
- **Classroom Leaderboard:** Instructors can enable a voluntary, anonymized leaderboard of "most improved security posture" to encourage healthy competition.
- **Streak Tracking:** "You've scanned 5 days in a row. Keep your code safe!"

### 22.7 Advanced Analytics UX
- **Comparative Analytics:** "Your code is 40% safer than the class average." (Presented positively, never shaming.)
- **Predictive Warnings:** "Based on your recent patterns, you might be vulnerable to XXE injection next. Here's how to prevent it."
- **Cohort Analysis (Instructor):** "Students who read KB articles within 24 hours of a finding have 3x faster remediation times."

---

## Appendices

### A. Design Token Quick Reference (JSON Snippet)
```json
{
  "color": {
    "primary": { "500": "#2563EB", "600": "#1D4ED8" },
    "semantic": {
      "critical": "#DC2626",
      "high": "#EA580C",
      "medium": "#CA8A04",
      "low": "#16A34A",
      "success": "#10B981",
      "info": "#3B82F6",
      "warning": "#F59E0B"
    },
    "dark": {
      "bg-base": "#0F1117",
      "surface-1": "#181B24",
      "surface-2": "#1F2330",
      "text-primary": "#F1F5F9",
      "text-secondary": "#94A3B8",
      "border": "#2E3548"
    }
  },
  "font": {
    "heading": "Inter, sans-serif",
    "body": "Inter, sans-serif",
    "mono": "JetBrains Mono, monospace"
  },
  "spacing": {
    "unit": "4px",
    "scale": [4, 8, 12, 16, 20, 24, 32, 40, 48, 64]
  },
  "radius": {
    "sm": "6px",
    "md": "8px",
    "lg": "12px",
    "pill": "9999px"
  },
  "shadow": {
    "card": "0 1px 3px rgba(0,0,0,0.12)",
    "dropdown": "0 4px 12px rgba(0,0,0,0.15)",
    "modal": "0 8px 24px rgba(0,0,0,0.20)"
  },
  "animation": {
    "fast": "150ms",
    "standard": "200ms",
    "slow": "300ms",
    "easing": {
      "ease": "ease",
      "ease-out": "cubic-bezier(0.16, 1, 0.3, 1)"
    }
  }
}
```

### B. Iconography Mapping
| Context | Icon Name (Lucide) | Size |
|---|---|---|
| Dashboard | `layout-dashboard` | 20px |
| New Scan | `shield-plus` | 20px |
| Report | `file-text` | 20px |
| History | `history` | 20px |
| Instructor | `users` | 20px |
| Admin | `settings` | 20px |
| Knowledge Base | `book-open` | 20px |
| Critical Severity | `alert-octagon` | 16px |
| High Severity | `alert-triangle` | 16px |
| Medium Severity | `alert-circle` | 16px |
| Low Severity | `info` | 16px |
| Fix Applied | `check-circle-2` | 16px |
| AI Sparkle | `sparkles` | 16px |
| Privacy Shield | `shield-check` | 20px |
| Copy | `copy` | 16px |
| Share | `share-2` | 16px |
| Export | `download` | 16px |
| Delete | `trash-2` | 16px |
| Settings | `sliders-horizontal` | 20px |

---

**End of Document**

**CodeGuard AI — UI/UX Design Brief v1.0 | G1F22FYPCS001 | University of Central Punjab | May 12, 2026**
