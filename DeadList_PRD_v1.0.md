# DeadList — Product Requirements Document

> **The process that's dead to the system. Found alive by DeadList.**

---

| Field | Detail |
|---|---|
| **Project Name** | DeadList |
| **Version** | v1.0 |
| **Status** | 🟡 DRAFT |
| **Type** | Web Application — Memory Forensics & Malware Detection |
| **Engine** | Volatility 3 |
| **Date** | June 2025 |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Overview](#2-product-overview)
3. [User Personas & User Stories](#3-user-personas--user-stories)
4. [Functional Requirements](#4-functional-requirements)
5. [Technology Stack](#5-technology-stack)
6. [System Architecture](#6-system-architecture)
7. [Volatility 3 Plugin Specifications](#7-volatility-3-plugin-specifications)
8. [UI/UX Specification](#8-uiux-specification)
9. [User Flow](#9-user-flow)
10. [API Specification](#10-api-specification)
11. [Project Folder Structure](#11-project-folder-structure)
12. [Non-Functional Requirements](#12-non-functional-requirements)
13. [Environment Setup & Dependencies](#13-environment-setup--dependencies)
14. [Implementation Phases](#14-implementation-phases)
15. [Testing Strategy](#15-testing-strategy)
16. [Open Questions & Future Scope](#16-open-questions--future-scope)
17. [Glossary](#17-glossary)

---

## 1. Executive Summary

**DeadList** is a web-based memory forensics platform built on top of the Volatility 3 framework. It enables cybersecurity analysts, students, and incident responders to upload a RAM dump file and receive a comprehensive, visual threat analysis report — identifying hidden malware processes, suspicious network connections, and injected code that are completely invisible to Windows Task Manager.

The core insight the tool exploits is a fundamental gap in how Windows Task Manager works: it reads from a linked list (EPROCESS) that rootkits can easily manipulate. DeadList uses Volatility 3's raw memory scanning approach, which bypasses this list entirely and scans the full memory dump byte-by-byte — exposing any hidden process, no matter how cleverly it is concealed.

The name **DeadList** refers to exactly this phenomenon — a process that has been removed ("dead") from the OS process list, yet is still alive and running in memory. DeadList finds it.

---

### 1.1 Problem Statement

Sophisticated malware — particularly rootkits — uses a technique called **Direct Kernel Object Manipulation (DKOM)** to hide from operating system tools like Task Manager. By unlinking their EPROCESS structure from the Windows kernel's doubly-linked list, these processes become completely invisible to any tool that relies on that list.

The result: malware runs freely, exfiltrates data, communicates with command-and-control servers, and injects code into legitimate processes — all without detection.

---

### 1.2 Solution

DeadList provides a one-stop analysis pipeline: upload a RAM dump → run five Volatility 3 plugins automatically → compare results to detect anomalies → score each process for suspicion → display findings in a professional dark-theme SOC-style dashboard.

---

### 1.3 Key Metrics of Success

| Metric | Target |
|---|---|
| Time from upload to full report | Under 60 seconds |
| Hidden process detection accuracy | 100% (all psscan vs pslist diffs) |
| Plugins executed automatically | 5 (pslist, psscan, netscan, malfind, cmdline) |
| Supported OS memory dumps | Windows 10/11 x64 (primary), Linux (stretch goal) |
| Report export formats | PDF + JSON |
| UI theme | Signal-style dark professional SOC dashboard |

---

## 2. Product Overview

### 2.1 Product Name & Tagline

| Field | Value |
|---|---|
| **Product Name** | DeadList |
| **Tagline** | *The process that's dead to the system. Found alive by DeadList.* |
| **Type** | Web Application (Full-Stack) |
| **Primary Purpose** | Memory forensics analysis and malware detection via Volatility 3 |
| **Target Users** | Cybersecurity students, CTF players, DFIR analysts, academics |
| **Project Type** | Summer Project — Academic / Portfolio |

---

### 2.2 Core Value Proposition

- Zero CLI knowledge needed — upload a dump, get a full visual report
- Catches hidden malware that evades every GUI-based Windows tool
- Automated diff engine flags hidden PIDs in seconds
- Professional SOC-grade UI that looks and feels like real industry tooling
- Suspicion scoring system prioritizes threats automatically

---

### 2.3 Out of Scope (v1.0)

- Live / real-time RAM monitoring of a running machine
- macOS memory dump support
- Multi-user authentication and role-based access
- Cloud deployment and SaaS features
- Automated malware removal or remediation

---

## 3. User Personas & User Stories

### 3.1 Primary Personas

#### Persona 1 — The CTF Player

| Attribute | Detail |
|---|---|
| **Name** | Arjun, 20 years old, B.Tech CSE 3rd year |
| **Goal** | Solve memory forensics challenges in CTF competitions |
| **Pain Point** | Manually running 10+ Volatility commands and grepping output is slow |
| **What DeadList gives him** | One upload, all results visualized, hidden PIDs highlighted automatically |

#### Persona 2 — The Cybersecurity Student

| Attribute | Detail |
|---|---|
| **Name** | Sneha, 22 years old, M.Tech Information Security |
| **Goal** | Learn and demonstrate memory forensics concepts for her thesis |
| **Pain Point** | Raw Volatility CLI output is hard to interpret and present |
| **What DeadList gives her** | Visual process trees, color-coded threat levels, exportable PDF reports |

#### Persona 3 — The Incident Responder

| Attribute | Detail |
|---|---|
| **Name** | Rahul, 28 years old, Junior SOC Analyst |
| **Goal** | Quickly triage a memory dump from a suspected compromised machine |
| **Pain Point** | No GUI tool integrates all Volatility plugins with automatic anomaly detection |
| **What DeadList gives him** | Automated suspicion scoring, network map, one-click deep dive into any process |

---

### 3.2 User Stories

| ID | As a... | I want to... | So that... |
|---|---|---|---|
| US-01 | CTF player | Upload a `.raw` memory dump and see all running processes | I can find the hidden malware PID |
| US-02 | CTF player | See which PIDs appear in psscan but not pslist | I can instantly identify DKOM-hidden processes |
| US-03 | Student | View a process tree with parent-child relationships | I can spot suspicious process hierarchies |
| US-04 | Student | See all network connections from the dump | I can identify C2 communication IPs and ports |
| US-05 | Analyst | Get a suspicion score for each process | I can prioritize which process to investigate first |
| US-06 | Analyst | Click any process and see a full detail drawer | I can deep-dive without leaving the dashboard |
| US-07 | Any user | See a live progress feed during analysis | I know the tool is working and what step it is on |
| US-08 | Any user | Export the full analysis as a PDF report | I can submit it as documentation or evidence |
| US-09 | Any user | See injected code regions flagged by malfind | I can identify shellcode and process hollowing |
| US-10 | Any user | View the command line of every process | I can detect suspicious launch arguments |

---

## 4. Functional Requirements

### FR-01: RAM Dump Upload

- User can drag-and-drop or click-to-select a memory dump file
- Supported formats: `.raw`, `.mem`, `.dmp`, `.vmem`, `.img`
- Max file size: 4GB (configurable via `.env`)
- MD5/SHA256 hash calculated immediately on upload for evidence integrity
- File stored securely in `/uploads/` directory with UUID-based naming (no user-supplied paths)
- Upload progress shown as animated RAM stick fill visualization

---

### FR-02: Automated Volatility Plugin Execution

- On upload completion, backend automatically runs all 5 plugins in parallel
- Plugins: `windows.pslist`, `windows.psscan`, `windows.netscan`, `windows.malfind`, `windows.cmdline`
- Each plugin result is streamed to the frontend via WebSocket as it completes
- Plugin execution timeout: 120 seconds per plugin (configurable)
- Raw JSON output of each plugin stored in SQLite for later retrieval

---

### FR-03: Hidden Process Detection (Diff Engine)

- Backend compares pslist PID set vs psscan PID set
- Any PID in `psscan` but **NOT** in `pslist` → flagged as **HIDDEN** 🔴
- Any PID in `pslist` but **NOT** in `psscan` → flagged as **ANOMALOUS** 🔵
- Hidden processes displayed with RED badge and pushed to top of process table

---

### FR-04: Suspicion Scoring System

Each process receives an automated suspicion score from **0 to 100**:

| Condition | Score Added | Severity | Rationale |
|---|---|---|---|
| Hidden (in psscan, not pslist) | +50 | 🔴 CRITICAL | Classic DKOM rootkit behavior |
| Suspicious parent process (e.g. cmd.exe from winword.exe) | +25 | 🟠 HIGH | Possible macro malware |
| Empty or null command line | +15 | 🟡 MEDIUM | Malware often has no cmdline |
| Known malicious port (4444, 1337, 8888) | +20 | 🟠 HIGH | Common C2 ports |
| Foreign/unusual IP connection | +10 | 🟡 MEDIUM | Possible data exfiltration |
| RWX memory region found by malfind | +30 | 🔴 CRITICAL | Shellcode / injected code |
| Process name mimicking system process | +20 | 🟠 HIGH | e.g. `svch0st.exe` vs `svchost.exe` |

---

### FR-05: Process Table Dashboard

- Sortable, filterable table of all discovered processes
- Columns: PID, Process Name, PPID, Status, Suspicion Score, Connections, Actions
- Color coding: 🔴 Red = Hidden/Critical | 🟡 Amber = Suspicious | 🟢 Green = Clean
- Click any row → opens Process Detail Drawer (FR-07)
- Filter bar: filter by status, score threshold, process name search

---

### FR-06: Network Connections Panel

- Table of all TCP/UDP connections from netscan output
- Columns: PID, Process, Local Address:Port, Remote Address:Port, State, Protocol
- Known malicious ports highlighted in red
- GeoIP lookup on remote IPs (via `ip-api.com` free tier)
- World map visualization showing connection origins

---

### FR-07: Process Detail Drawer

- Slide-in panel from right side (480px wide) on process row click
- Shows: process name, PID, PPID, start time, command line, memory regions
- malfind results for that specific PID (if any)
- All network connections owned by that PID
- Hex dump preview of suspicious memory regions
- Close on `ESC` or clicking outside

---

### FR-08: Live Analysis Feed

- Terminal-style scrolling log shown during analysis
- Real-time WebSocket messages: plugin started, plugin complete, anomaly found
- Example output:
  ```
  [14:32:01] Running windows.psscan...
  [14:32:08] ✅ psscan complete — 849 process objects found
  [14:32:08] 🚨 ALERT: 2 hidden processes detected (psscan ∖ pslist)
  ```
- Animated radar/scan effect during processing

---

### FR-09: PDF Report Export

- One-click export of full analysis as formatted PDF
- Report includes: file metadata, hashes, all plugin results, hidden process list, suspicion scores
- Generated server-side using ReportLab (Python)
- Filename format: `DeadList_Report_<filename>_<timestamp>.pdf`

---

### FR-10: Analysis History

- All past analysis runs saved in SQLite database
- Sidebar panel shows history: filename, date, threat level, hidden process count
- Click any past run → reload its full dashboard without re-running Volatility

---

## 5. Technology Stack

### 5.1 Stack Overview

| Layer | Technology | Version | Reason for Choice |
|---|---|---|---|
| Forensics Engine | Volatility 3 | v2.26.x | World standard memory forensics. Plugin-based, Python 3, no profile needed |
| Backend Framework | FastAPI | 0.111+ | Async Python, auto API docs, WebSocket support, faster than Flask |
| Backend Language | Python | 3.11+ | Same language as Volatility — native integration, no subprocess complexity |
| WebSockets | FastAPI WebSockets | built-in | Real-time plugin progress streaming to frontend |
| Task Queue | Python asyncio + ThreadPoolExecutor | built-in | Parallel plugin execution without Celery overhead |
| Database | SQLite + SQLAlchemy | SQLAlchemy 2.0 | Zero-config, file-based, perfect for single-user forensics tool |
| PDF Generation | ReportLab | 4.x | Server-side PDF generation, full layout control |
| Frontend Framework | React 18 + Vite | React 18, Vite 5 | Fast dev server, component model, best ecosystem |
| Styling | TailwindCSS | v3.4 | Utility-first, rapid dark theme, no CSS bloat |
| Charts & Graphs | Recharts | 2.x | React-native charting, clean API, customizable |
| Process Tree | React D3 Tree | 3.x | Interactive collapsible tree for parent-child process view |
| World Map | React Simple Maps | 3.x | SVG world map for network connection visualization |
| Icons | Lucide React | 0.383+ | Clean, consistent icon set matching dark theme |
| HTTP Client | Axios | 1.x | Promise-based, interceptors, better than fetch for complex apps |
| State Management | Zustand | 4.x | Lightweight, no boilerplate, simpler than Redux for this scale |
| File Upload | react-dropzone | 14.x | Drag-and-drop upload with progress, widely used |
| GeoIP | ip-api.com | Free tier | IP to country/city lookup for network connection map |
| Containerization | Docker + Docker Compose | latest | One-command setup, Volatility + FastAPI + React all bundled |

---

### 5.2 Why NOT These Alternatives

| Rejected Option | Reason Rejected |
|---|---|
| Flask (instead of FastAPI) | No native async, no auto WebSocket, slower, less modern |
| Django (instead of FastAPI) | Too heavy for this use case, ORM overkill, slow to set up |
| Volatility 2 (instead of v3) | Officially deprecated 2025. Requires complex profile setup |
| Redux (instead of Zustand) | Too much boilerplate for a tool of this size |
| MySQL/PostgreSQL (instead of SQLite) | Overkill — no multi-user, no concurrent writes needed |
| Angular/Vue (instead of React) | Smaller ecosystem, less component availability for our needs |
| Celery (instead of asyncio) | Heavy dependency, Redis needed, unnecessary for 5 tasks |

---

## 6. System Architecture

### 6.1 High-Level Architecture

DeadList follows a clean client-server architecture with three distinct layers:

```
┌─────────────────────────────────────────────────────────────┐
│                     REACT FRONTEND                          │
│         (Upload → Analysis Feed → Dashboard)                │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST + WebSocket
┌──────────────────────────▼──────────────────────────────────┐
│                    FASTAPI BACKEND                          │
│     Upload Handler │ Analysis Router │ WS Manager          │
│     Diff Engine    │ Scoring Engine  │ GeoIP │ PDF Gen      │
└──────────────────────────┬──────────────────────────────────┘
                           │ subprocess / library call
┌──────────────────────────▼──────────────────────────────────┐
│                   VOLATILITY 3 ENGINE                       │
│    pslist │ psscan │ netscan │ malfind │ cmdline            │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   SQLITE DATABASE                           │
│      analyses │ processes │ connections │ memory_regions    │
└─────────────────────────────────────────────────────────────┘
```

---

### 6.2 Architecture Flow (Step by Step)

1. User uploads RAM dump file via React frontend (drag-and-drop)
2. FastAPI backend receives multipart file upload, saves to `/uploads/` with UUID
3. Backend calculates MD5/SHA256 hash of file immediately
4. Backend spawns 5 Volatility plugin tasks in parallel via `ThreadPoolExecutor`
5. As each plugin completes, its result is sent to frontend via WebSocket
6. **Diff Engine** compares pslist vs psscan outputs, flags hidden PIDs
7. **Scoring Engine** assigns suspicion score to each process
8. Full analysis result saved to SQLite database
9. Frontend renders final dashboard: process table, network panel, threat summary
10. User can click any process for detail drawer, or export PDF report

---

### 6.3 Backend Module Map

| Module | Responsibility |
|---|---|
| `main.py` | FastAPI app entry point, route registration, CORS config |
| `routers/upload.py` | Handles file upload, hash calculation, triggers analysis pipeline |
| `routers/analysis.py` | REST endpoints for fetching analysis results, history, process details |
| `routers/ws.py` | WebSocket manager — broadcasts plugin progress to connected clients |
| `core/volatility_runner.py` | Subprocess wrapper for Volatility 3 — runs each plugin, parses JSON output |
| `core/diff_engine.py` | Compares pslist vs psscan PIDs, returns hidden and anomalous processes |
| `core/scoring_engine.py` | Assigns suspicion score to each process based on 7 scoring criteria |
| `core/geoip.py` | Requests ip-api.com to resolve remote IPs to country/city |
| `core/pdf_generator.py` | Uses ReportLab to generate formatted PDF report from analysis data |
| `models/database.py` | SQLAlchemy models: Analysis, Process, Connection, MemoryRegion |
| `schemas/` | Pydantic schemas for request/response validation and serialization |
| `config.py` | Environment variables: upload path, Volatility path, DB URL, max file size |

---

### 6.4 Frontend Component Map

| Module / Directory | Responsibility |
|---|---|
| `src/pages/Upload.jsx` | Landing page with drag-and-drop zone, hash display, upload progress |
| `src/pages/Analysis.jsx` | Live analysis feed with terminal log and plugin progress stepper |
| `src/pages/Dashboard.jsx` | Main results dashboard: stat cards, process table, network panel |
| `src/pages/History.jsx` | Past analysis runs list with quick stats |
| `src/components/ProcessTable.jsx` | Sortable/filterable table of all processes with color coding |
| `src/components/ProcessDrawer.jsx` | Slide-in detail panel for single process deep-dive |
| `src/components/NetworkPanel.jsx` | Network connections table + world map visualization |
| `src/components/ThreatSummary.jsx` | Hero section: total threats, hidden count, risk level badge |
| `src/components/PluginStepper.jsx` | Step-by-step plugin execution progress with status indicators |
| `src/components/TerminalFeed.jsx` | Scrolling terminal-style log of WebSocket messages |
| `src/components/ProcessTree.jsx` | Interactive collapsible parent-child process tree |
| `src/store/analysisStore.js` | Zustand store: analysis results, selected process, UI state |
| `src/hooks/useWebSocket.js` | Custom hook for WebSocket connection and message handling |
| `src/utils/scoring.js` | Frontend suspicion score → color/label helpers |
| `src/utils/api.js` | Axios instance with base URL and interceptors |

---

### 6.5 Database Schema

#### Table: `analyses`

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | UUID (PK) | NO | Unique analysis identifier |
| `filename` | VARCHAR(255) | NO | Original uploaded filename |
| `filepath` | VARCHAR(512) | NO | Server-side file path |
| `md5_hash` | VARCHAR(32) | NO | MD5 hash for evidence integrity |
| `sha256_hash` | VARCHAR(64) | NO | SHA256 hash for evidence integrity |
| `file_size_bytes` | BIGINT | NO | Size of the memory dump file |
| `status` | ENUM | NO | `pending / running / complete / failed` |
| `risk_level` | ENUM | YES | `clean / low / medium / high / critical` |
| `hidden_process_count` | INTEGER | YES | Number of DKOM-hidden processes found |
| `created_at` | DATETIME | NO | Timestamp of upload |
| `completed_at` | DATETIME | YES | Timestamp of analysis completion |
| `os_profile` | VARCHAR(100) | YES | Detected OS (e.g. Win10x64) |

#### Table: `processes`

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | INTEGER (PK) | NO | Auto-increment primary key |
| `analysis_id` | UUID (FK) | NO | Foreign key → analyses table |
| `pid` | INTEGER | NO | Process ID |
| `ppid` | INTEGER | YES | Parent Process ID |
| `name` | VARCHAR(255) | NO | Process executable name |
| `in_pslist` | BOOLEAN | NO | Whether process appears in pslist output |
| `in_psscan` | BOOLEAN | NO | Whether process appears in psscan output |
| `is_hidden` | BOOLEAN | NO | Computed: in psscan but NOT in pslist |
| `cmdline` | TEXT | YES | Command line arguments from windows.cmdline |
| `suspicion_score` | INTEGER | NO | 0–100 calculated suspicion score |
| `status` | ENUM | NO | `hidden / anomalous / suspicious / clean` |
| `has_injected_code` | BOOLEAN | NO | Whether malfind found suspicious regions |

#### Table: `network_connections`

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | INTEGER (PK) | NO | Auto-increment primary key |
| `analysis_id` | UUID (FK) | NO | Foreign key → analyses table |
| `pid` | INTEGER | NO | Owning process PID |
| `protocol` | VARCHAR(10) | NO | TCP / UDP |
| `local_addr` | VARCHAR(45) | NO | Local IP address |
| `local_port` | INTEGER | NO | Local port number |
| `remote_addr` | VARCHAR(45) | YES | Remote IP address |
| `remote_port` | INTEGER | YES | Remote port number |
| `state` | VARCHAR(20) | YES | Connection state (ESTABLISHED, LISTENING, etc.) |
| `country` | VARCHAR(100) | YES | GeoIP-resolved country |
| `city` | VARCHAR(100) | YES | GeoIP-resolved city |
| `is_suspicious_port` | BOOLEAN | NO | Whether port is in known-bad list |

---

## 7. Volatility 3 Plugin Specifications

### 7.1 Plugin Execution Details

| Plugin | Command | What It Returns |
|---|---|---|
| `windows.pslist` | `vol -f dump.raw windows.pslist --output json` | All processes from EPROCESS linked list (same as Task Manager) |
| `windows.psscan` | `vol -f dump.raw windows.psscan --output json` | All processes by raw memory scan — includes DKOM-hidden ones |
| `windows.netscan` | `vol -f dump.raw windows.netscan --output json` | All TCP/UDP connections, listening sockets, owning PIDs |
| `windows.malfind` | `vol -f dump.raw windows.malfind --output json` | Memory regions with RWX permissions and no file backing |
| `windows.cmdline` | `vol -f dump.raw windows.cmdline --output json` | Command line arguments for each process at time of dump |

---

### 7.2 Diff Engine Logic

```python
pslist_pids  = set(p['PID'] for p in pslist_output)
psscan_pids  = set(p['PID'] for p in psscan_output)

hidden_pids    = psscan_pids - pslist_pids   # DKOM hidden — in RAM but not in list
anomalous_pids = pslist_pids - psscan_pids   # In list but not in raw scan — rare anomaly
```

- `hidden_pids` → CRITICAL status, +50 suspicion score, pushed to top of table
- `anomalous_pids` → ANOMALOUS status, +20 suspicion score, flagged blue

---

### 7.3 Parallel Execution Architecture

All five plugins execute concurrently using `ThreadPoolExecutor(max_workers=5)`. Each plugin writes its result to a shared dict keyed by plugin name. WebSocket manager broadcasts completion events as each `Future` resolves.

**Total analysis time = slowest single plugin** (not sum of all) — typically **20–40 seconds** for a 4GB dump.

```python
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = {
        executor.submit(run_plugin, dump_path, plugin): plugin
        for plugin in PLUGINS
    }
    for future in as_completed(futures):
        plugin_name = futures[future]
        result = future.result()
        await ws_manager.broadcast(analysis_id, {
            "event": "plugin_complete",
            "plugin": plugin_name,
            "count": len(result)
        })
```

---

## 8. UI/UX Specification

### 8.1 Design Inspiration

The UI is modeled after the **Signal Infrastructure Dashboard** — a professional dark-theme monitoring dashboard used in DevOps/SRE environments. This was chosen because it maps directly to real-world SOC tooling aesthetics, making DeadList look and feel like a production-grade forensics platform.

> Reference: Image 3 from the provided UI references. Key elements borrowed: dark base, green/amber/red semantic status system, service status grid, active incidents panel, deployment pipeline list, area chart with colored lines.

---

### 8.2 Color System

#### Primary Palette (CSS Custom Properties)

```css
:root {
  --bg-base:         #0A0E13;  /* Page/app background */
  --bg-surface:      #161B22;  /* Cards, panels, sidebar */
  --bg-elevated:     #21262D;  /* Dropdowns, modals, drawers */
  --border-subtle:   #30363D;  /* All borders, dividers */

  --text-primary:    #E6EDF3;  /* Main content text */
  --text-secondary:  #8B949E;  /* Labels, timestamps, metadata */
  --text-disabled:   #484F58;  /* Placeholder text */

  --accent-green:    #3FB950;  /* Safe / success / healthy */
  --accent-amber:    #D29922;  /* Warning / suspicious */
  --accent-red:      #F85149;  /* Critical / malicious / hidden */
  --accent-blue:     #58A6FF;  /* Info / links / interactive */

  --brand-primary:   #1F6FEB;  /* Brand color, CTA buttons */

  --glow-red:   rgba(248, 81, 73, 0.15);  /* Red glow on critical cards */
  --glow-green: rgba(63, 185, 80, 0.10);  /* Green glow on safe items */
}
```

#### Semantic Status Colors

| Status | Background | Text / Border | Usage |
|---|---|---|---|
| 🔴 HIDDEN (Critical) | `#3D0B09` | `#F85149` | DKOM-hidden process rows |
| 🟡 SUSPICIOUS (High) | `#2D1C00` | `#D29922` | High suspicion score processes |
| 🔵 ANOMALOUS (Medium) | `#0D1F38` | `#58A6FF` | pslist-only anomalies |
| 🟢 CLEAN (Safe) | `#0D1F14` | `#3FB950` | Clean process rows |

---

### 8.3 Typography

| Element | Specification |
|---|---|
| **Primary Font** | `Inter` — Google Fonts. All body and UI text |
| **Monospace Font** | `JetBrains Mono` — terminal feed, hex dumps, PIDs, hashes |
| Page Title / H1 | Inter Bold, 28px, `#E6EDF3` |
| Section Title / H2 | Inter SemiBold, 20px, `#E6EDF3` |
| Card Title / H3 | Inter Medium, 16px, `#8B949E`, UPPERCASE, `letter-spacing: 0.05em` |
| Body Text | Inter Regular, 14px, `#E6EDF3` |
| Secondary/Meta Text | Inter Regular, 12px, `#8B949E` |
| Terminal Feed | JetBrains Mono Regular, 13px, `#3FB950` on `#0A0E13` |
| Status Badges | Inter Bold, 11px, UPPERCASE, `letter-spacing: 0.08em` |
| Suspicion Score | JetBrains Mono Bold, 14px, color varies by score |
| Table Headers | Inter SemiBold, 12px, `#8B949E`, UPPERCASE, `letter-spacing: 0.05em` |
| Table Data | Inter Regular, 13px, `#E6EDF3` |

---

### 8.4 Spacing & Layout System

```
Base unit:      4px (all spacing = multiples of 4)
Sidebar width:  240px (collapses to 64px icon-only)
Header height:  56px
Card radius:    8px
Button radius:  6px
Badge radius:   4px
Card padding:   20px
Table row h:    48px
Drawer width:   480px
Grid:           12-column CSS Grid, 24px gutter
Breakpoints:    sm: 640px | md: 1024px | lg: 1280px+
```

---

### 8.5 Tailwind Config (design tokens)

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        'bg-base':       '#0A0E13',
        'bg-surface':    '#161B22',
        'bg-elevated':   '#21262D',
        'border-subtle': '#30363D',
        'text-primary':  '#E6EDF3',
        'text-secondary':'#8B949E',
        'accent-green':  '#3FB950',
        'accent-amber':  '#D29922',
        'accent-red':    '#F85149',
        'accent-blue':   '#58A6FF',
        'brand':         '#1F6FEB',
      },
      fontFamily: {
        sans:  ['Inter', 'sans-serif'],
        mono:  ['JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        card:   '8px',
        badge:  '4px',
        btn:    '6px',
      }
    }
  }
}
```

---

### 8.6 Component Specifications

#### Sidebar Navigation
- Width: 240px | Background: `--bg-surface`
- Logo: skull/ghost icon + "DeadList" in Inter Bold at top
- Sections: `OVERVIEW` | `ANALYSIS` | `HISTORY` | `SETTINGS`
- Active item: 2px left border in `--brand-primary`, background `--bg-elevated`
- Collapsible to icon-only on mobile

#### Stat Cards (Dashboard Hero)
- 4 cards: Hidden Processes | Suspicious Connections | Clean Processes | Risk Level
- Background: `--bg-surface` | Border: `1px --border-subtle` | Radius: `8px`
- Large number in Inter Bold 32px
- Color-coded icon top-right (red/amber/green)
- Critical card: `box-shadow: 0 0 20px rgba(248,81,73,0.2)`

#### Process Table
- Full-width, sticky header, subtle alternating row shading
- Hidden rows: `background: rgba(248,81,73,0.08)` + `border-left: 2px solid #F85149`
- Suspicious rows: `background: rgba(210,153,34,0.08)` + `border-left: 2px solid #D29922`
- Suspicion score: colored number + mini progress bar underneath
- Hover state: row background +5% lighter, `cursor: pointer`

#### Terminal Feed
- Background: `#0A0E13` | Font: JetBrains Mono 13px
- Timestamps in `--text-secondary`, log text in `--accent-green`
- `🚨 ALERT` lines in `--accent-red` with pulsing red dot
- Auto-scroll to bottom on new messages
- `max-height: 320px`, `overflow-y: auto`, custom dark scrollbar

#### Plugin Stepper
- Horizontal stepper, 5 steps: `pslist → psscan → netscan → malfind → cmdline`
- ⭕ Pending (grey) → 🔄 Running (spinning blue) → ✅ Complete (solid green)
- Connector line fills with green as each step completes

---

## 9. User Flow

### 9.1 Primary Flow — Upload to Dashboard

```
[Upload Page]
    ↓ Drag & drop .raw file
    ↓ MD5/SHA256 hash calculated and shown
    ↓ Upload progress → RAM stick animation
    ↓ Upload complete → auto-redirect

[Analysis Page]
    ↓ WebSocket connects
    ↓ 5 plugins start in parallel
    ↓ Terminal feed streams live logs
    ↓ Plugin stepper updates in real-time
    ↓ All complete → Red Alert banner (if threats found)
    ↓ "View Dashboard" button appears

[Dashboard Page]
    ↓ Stat cards: Hidden count | Risk Level
    ↓ Process table: sorted by suspicion score
    ↓ Network panel: connections + world map
    ↓ Click any process → Detail Drawer
    ↓ Export PDF → download report
```

---

### 9.2 Secondary Flow — Process Deep Dive

1. User spots red row in process table
2. Clicks row → Detail Drawer slides in from right (480px)
3. Drawer shows: name, PID, PPID, status badge, score breakdown
4. Command line (or `Empty — SUSPICIOUS 🔴` if null)
5. Network connections owned by this PID
6. malfind memory regions + hex preview (if any)
7. User presses `ESC` or clicks `✕` to close

---

### 9.3 Secondary Flow — Export Report

1. User clicks `Export PDF` in dashboard header
2. Loading spinner on button
3. Backend generates PDF via ReportLab
4. File auto-downloads: `DeadList_Report_<dump>_<timestamp>.pdf`

---

### 9.4 Navigation Structure

| Route | Page / Purpose |
|---|---|
| `/` | Upload page — drag and drop memory dump |
| `/analysis/:id` | Live analysis feed — plugin progress, terminal log |
| `/dashboard/:id` | Main results dashboard — all findings visualized |
| `/history` | List of all past analysis runs |
| `/dashboard/:id/process/:pid` | Dashboard with specific process drawer pre-opened |
| `/settings` | Config: Volatility path, max file size, theme toggle |

---

## 10. API Specification

### 10.1 REST Endpoints

| Method | Endpoint | Request | Response |
|---|---|---|---|
| `POST` | `/api/upload` | `multipart/form-data: file` | `{ analysis_id, filename, md5, sha256, status }` |
| `GET` | `/api/analysis/{id}` | — | Full analysis object with all plugin results |
| `GET` | `/api/analysis/{id}/processes` | `?status=hidden&min_score=50` | Paginated process list with filters |
| `GET` | `/api/analysis/{id}/process/{pid}` | — | Single process detail with connections, memory regions |
| `GET` | `/api/analysis/{id}/network` | — | All network connections with GeoIP data |
| `GET` | `/api/analysis/{id}/report/pdf` | — | Binary PDF file download |
| `GET` | `/api/history` | `?page=1&limit=20` | Paginated list of past analysis runs |
| `DELETE` | `/api/analysis/{id}` | — | Delete analysis and associated dump file |
| `GET` | `/api/health` | — | `{ status: "ok", volatility_version: "x.x.x" }` |
| `WS` | `/ws/{analysis_id}` | — | WebSocket for real-time plugin progress events |

---

### 10.2 WebSocket Event Types

| Event Type | Payload Fields | Description |
|---|---|---|
| `plugin_started` | `{ plugin, timestamp }` | Fired when a plugin begins execution |
| `plugin_complete` | `{ plugin, timestamp, process_count }` | Fired when plugin finishes successfully |
| `plugin_error` | `{ plugin, timestamp, error }` | Fired if plugin fails or times out |
| `anomaly_found` | `{ type, pid, name, score }` | Fired when hidden/suspicious process detected |
| `analysis_complete` | `{ analysis_id, risk_level, hidden_count }` | Fired when all 5 plugins are done |
| `progress` | `{ percent, message }` | General progress during scoring/diffing |

---

## 11. Project Folder Structure

### 11.1 Root

```
deadlist/
├── backend/                  # FastAPI Python backend
├── frontend/                 # React + Vite frontend
├── uploads/                  # Memory dumps (gitignored)
├── data/                     # SQLite DB (gitignored)
├── docker-compose.yml        # Orchestrates all containers
├── .env.example              # Environment variable template
└── README.md                 # Setup and usage instructions
```

---

### 11.2 Backend Structure

```
backend/
├── main.py                       # App entry, CORS, router registration
├── config.py                     # Pydantic BaseSettings from .env
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Docker image
├── routers/
│   ├── upload.py                 # POST /upload + file handling
│   ├── analysis.py               # GET analysis endpoints
│   └── ws.py                     # WebSocket endpoint + manager
├── core/
│   ├── volatility_runner.py      # Volatility 3 subprocess execution
│   ├── diff_engine.py            # pslist vs psscan comparison
│   ├── scoring_engine.py         # Suspicion score calculator
│   ├── geoip.py                  # ip-api.com IP resolution
│   └── pdf_generator.py          # ReportLab PDF generation
└── models/
    ├── database.py               # SQLAlchemy models + DB init
    └── schemas.py                # Pydantic request/response schemas
```

---

### 11.3 Frontend Structure

```
frontend/
├── index.html
├── vite.config.js
├── tailwind.config.js            # Design tokens
├── Dockerfile                    # nginx-based Docker image
└── src/
    ├── main.jsx                  # React entry point
    ├── App.jsx                   # React Router v6 setup
    ├── pages/
    │   ├── Upload.jsx            # Drop zone + hash display
    │   ├── Analysis.jsx          # Stepper + terminal feed
    │   ├── Dashboard.jsx         # Main results dashboard
    │   └── History.jsx           # Past runs list
    ├── components/
    │   ├── layout/
    │   │   ├── Sidebar.jsx
    │   │   └── Header.jsx
    │   ├── ProcessTable.jsx
    │   ├── ProcessDrawer.jsx
    │   ├── NetworkPanel.jsx
    │   ├── ThreatSummary.jsx
    │   ├── TerminalFeed.jsx
    │   ├── PluginStepper.jsx
    │   └── ProcessTree.jsx
    ├── store/
    │   └── analysisStore.js      # Zustand global state
    ├── hooks/
    │   └── useWebSocket.js       # WS connection hook
    └── utils/
        ├── api.js                # Axios instance
        └── scoring.js            # Score → color/label helpers
```

---

## 12. Non-Functional Requirements

| Category | Requirement | Target |
|---|---|---|
| Performance | Analysis time for 4GB dump | Under 60 seconds |
| Performance | API response time (non-analysis) | Under 200ms |
| Performance | Frontend initial load | Under 3 seconds |
| Performance | WebSocket message latency | Under 100ms |
| Reliability | Plugin failure handling | Single plugin fail = graceful error + continue rest |
| Reliability | Large file handling | Handle dumps up to 16GB without OOM crash |
| Security | File type validation | Server-side MIME type + magic bytes check (not just extension) |
| Security | Path traversal prevention | UUID-based filenames, no user paths in filesystem ops |
| Security | Input sanitization | All inputs validated via Pydantic schemas |
| Scalability | Concurrent analyses | v1.0: single at a time, queue if busy |
| Maintainability | Code documentation | All core modules have docstrings + inline comments |
| Compatibility | OS dump support | Windows 10/11 x64 (primary), Linux (stretch goal) |
| Usability | Zero-config setup | `docker-compose up` = fully running in one command |

---

## 13. Environment Setup & Dependencies

### 13.1 Prerequisites

- Docker Desktop (Windows/macOS) or Docker Engine + Compose (Linux)
- Git
- Minimum 8GB RAM on host machine
- 20GB free disk space (for dumps + Docker images)

---

### 13.2 Environment Variables (`.env`)

```env
VOLATILITY_PATH=vol                          # Path to vol executable
UPLOAD_DIR=./uploads                         # Memory dump storage dir
DATABASE_URL=sqlite:///./data/deadlist.db    # SQLite connection string
MAX_UPLOAD_SIZE_GB=16                        # Max dump file size
PLUGIN_TIMEOUT_SECONDS=120                   # Per-plugin timeout
GEOIP_API_URL=http://ip-api.com/json         # GeoIP endpoint
CORS_ORIGINS=http://localhost:5173           # Allowed frontend origins
LOG_LEVEL=INFO                               # Python log level
```

---

### 13.3 Python Dependencies (`requirements.txt`)

```
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
python-multipart>=0.0.9
sqlalchemy>=2.0.0
aiosqlite>=0.20.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
reportlab>=4.0.0
httpx>=0.27.0
volatility3>=2.26.0
python-jose>=3.3.0
```

---

### 13.4 Frontend Dependencies (`package.json`)

```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.23.0",
    "axios": "^1.7.0",
    "zustand": "^4.5.0",
    "recharts": "^2.12.0",
    "react-dropzone": "^14.2.0",
    "lucide-react": "^0.383.0",
    "react-d3-tree": "^3.6.0",
    "react-simple-maps": "^3.0.0",
    "react-hot-toast": "^2.4.0"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "@vitejs/plugin-react": "^4.3.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

---

## 14. Implementation Phases

### Phase 1 — Core Backend (Week 1–2)
- [ ] Set up FastAPI project structure, Docker, SQLite
- [ ] Implement file upload endpoint with MD5/SHA256 hash
- [ ] Write `volatility_runner.py` (subprocess execution, JSON parsing)
- [ ] Implement `diff_engine.py` (pslist vs psscan comparison)
- [ ] Implement `scoring_engine.py` (7-criteria scoring)
- [ ] Unit tests for diff engine and scoring engine
- [ ] Test all 5 plugins against a sample CTF memory dump

### Phase 2 — WebSocket & Streaming (Week 2–3)
- [ ] Implement WebSocket connection manager class
- [ ] Wire plugin execution to broadcast events via WebSocket
- [ ] Implement parallel plugin execution with `ThreadPoolExecutor`
- [ ] Test real-time streaming with mock frontend

### Phase 3 — Frontend Core (Week 3–4)
- [ ] Set up React + Vite + Tailwind project
- [ ] Configure design tokens in `tailwind.config.js`
- [ ] Build Layout: Sidebar + Header + main content area
- [ ] Build Upload page with animated drop zone
- [ ] Build Analysis page with `PluginStepper` + `TerminalFeed`
- [ ] Connect `useWebSocket` hook to Analysis page

### Phase 4 — Dashboard & Visualizations (Week 4–5)
- [ ] Build `ThreatSummary` stat cards
- [ ] Build `ProcessTable` with sorting, filtering, color coding
- [ ] Build `ProcessDrawer` with all detail sections
- [ ] Build `NetworkPanel` with table and world map
- [ ] Build `ProcessTree` (react-d3-tree)
- [ ] Implement GeoIP lookups on network connections

### Phase 5 — Polish & Export (Week 5–6)
- [ ] Implement PDF report generation (`ReportLab`)
- [ ] Build Analysis History page
- [ ] Add toast notifications for key events
- [ ] Add Red Alert animation on hidden process discovery
- [ ] Performance: lazy loading, pagination for large process lists
- [ ] Final Docker Compose config + README

---

## 15. Testing Strategy

### 15.1 Test Memory Dumps

Use publicly available CTF memory dumps containing known malware:

- **MemLabs** (GitHub) — educational memory forensics challenges, documented malware
- **BlueteamLabs Online** — free forensics challenges with sample dumps
- **Volatility Foundation samples** — official test images
- **CyberDefenders** — DFIR challenges with real memory images

---

### 15.2 Test Cases

| Test ID | Test Case | Expected Result |
|---|---|---|
| TC-01 | Upload valid `.raw` dump file | Hash displayed, analysis auto-starts |
| TC-02 | Upload invalid file (`.txt`) | Error: unsupported file type |
| TC-03 | Upload dump with known DKOM rootkit | Hidden PID(s) flagged red, confirmed by psscan∖pslist diff |
| TC-04 | Upload clean dump (no malware) | All processes green, risk level: CLEAN |
| TC-05 | Verify pslist vs psscan diff | Hidden PID count matches known rootkit behavior |
| TC-06 | netscan with known C2 connection | Suspicious IP flagged, shown in network panel |
| TC-07 | malfind on dump with injected code | RWX regions flagged for affected PIDs |
| TC-08 | Export PDF report | Valid PDF downloaded with all findings |
| TC-09 | WebSocket disconnection mid-analysis | Analysis completes, results accessible from history |
| TC-10 | History page loads past analysis | All runs listed, clicking reloads full dashboard |

---

## 16. Open Questions & Future Scope

### 16.1 Open Questions for v1.0

- Should OS profile auto-detection be implemented, or require manual selection?
- GeoIP rate limiting: ip-api.com free = 45 req/min. Cache or batch lookup?
- Should memory dumps be deleted after analysis or retained? Configurable TTL?
- Hard cap at 16GB or soft warning with user confirmation?

---

### 16.2 Future Scope (v2.0+)

- **YARA rule scanning** — scan memory for known malware signatures
- **Linux dump support** — `windows.*` plugins → `linux.*` plugins
- **Multi-user auth** — JWT-based login, per-user analysis history
- **VirusTotal integration** — hash lookup on suspicious processes
- **MITRE ATT&CK mapping** — tag findings with technique IDs (T1055, T1036, etc.)
- **ML malware classifier** — model trained on process feature vectors
- **Timeline view** — process creation/termination chronological view
- **Comparison mode** — diff two dumps side-by-side
- **Headless CLI mode** — run DeadList without the server, output JSON/PDF

---

## 17. Glossary

| Term | Definition |
|---|---|
| **RAM Dump / Memory Image** | A byte-for-byte copy of a computer's RAM at a specific point in time, saved to a file (`.raw`, `.mem`, `.dmp`) |
| **Volatility 3** | Open-source Python framework for analyzing memory dumps. The world standard for memory forensics |
| **EPROCESS** | Windows kernel structure representing a running process. Contains PID, name, and FLINK/BLINK list pointers |
| **DKOM** | Direct Kernel Object Manipulation — rootkit technique of modifying kernel structures to hide processes |
| **Rootkit** | Malware designed to hide its own presence and other malware from OS tools and security software |
| **pslist** | Volatility plugin listing processes by walking the EPROCESS doubly-linked list (same as Task Manager) |
| **psscan** | Volatility plugin finding processes by raw RAM scan for EPROCESS signatures, bypassing the linked list |
| **netscan** | Volatility plugin finding TCP/UDP socket objects in memory |
| **malfind** | Volatility plugin identifying executable memory regions not backed by a file (likely injected shellcode) |
| **C2 / Command & Control** | Attacker-operated server that communicates with malware to issue commands and receive stolen data |
| **DFIR** | Digital Forensics and Incident Response — professional field of investigating cybersecurity incidents |
| **SOC** | Security Operations Center — team/facility monitoring and responding to security incidents in real time |
| **Suspicion Score** | DeadList's computed 0–100 score per process indicating likelihood of malicious behavior |
| **PID** | Process Identifier — unique integer assigned by the OS to each running process |
| **PPID** | Parent Process Identifier — PID of the process that spawned the current one |
| **RWX** | Read-Write-Execute memory permissions — all three together is a major shellcode red flag |
| **Process Hollowing** | Malware technique: create legitimate process → empty its memory → inject malicious code |
| **FLINK / BLINK** | Forward Link / Backward Link — the two pointers in EPROCESS that form the doubly-linked process list |
| **WebSocket** | Bidirectional persistent protocol used to stream Volatility results in real-time to the browser |
| **FastAPI** | Modern async Python web framework used as the DeadList backend |
| **SQLite** | Lightweight file-based SQL database — stores all analysis results without a separate DB server |
| **ThreadPoolExecutor** | Python concurrency tool used to run all 5 Volatility plugins simultaneously |

---

*DeadList PRD v1.0 | Memory Forensics & Malware Detection Platform | Summer Project 2025*

*The process that's dead to the system. Found alive by DeadList.*
