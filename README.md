# Devin SWE 2.0 PowerPack

A production-grade enhancement suite for **Devin SWE 2.0 (`swe-2-medium`)** that overcomes context-window exhaustion (262K limit), prevents runaway multi-hour debugging loops, and enables high-speed reverse engineering and complex refactoring.

---

## ⚡ The Core Problem & The Fix

| Symptom in Raw SWE 2.0 | Root Cause | PowerPack Solution |
| :--- | :--- | :--- |
| **Blows past 262k context** | Dumps full 1,000+ line files and verbose terminal logs into prompt | **Surgical Context Hygiene & `devin-run`**: Forbids reading files >200 lines; automatically intercepts & truncates CLI outputs exceeding 80 lines into `.mythos/last_output.log`. |
| **Forgets edits after 40 mins** | Relies on conversational memory which truncates or slips past 160k | **Git Truth & State Ledger (`.mythos/state.md`)**: Forces the agent to consult `git status -s` and a strict 100-line disk state ledger before every edit. |
| **Infinite debugging spirals** | Tries random fixes 10 times in a row, breaking previously working code | **3-Strike Circuit Breaker**: Hard limit of 3 attempts. On strike 3, automatically reverts (`git checkout -- <file>`), logs root cause, and pivots. |
| **Slow on Reverse Engineering** | Ingests huge disassemblies/minified bundles; re-learns obfuscated symbols | **Harness-First Protocol & Symbol Ledger**: Requires minimal test harnesses and symbol dictionary (`.mythos/re_symbols.md`) to map obfuscated tokens once. |
| **Context Bloat during Research** | Orchestrator burns 80k tokens investigating 15 files | **Isolated Custom Subagents**: Spawns ephemeral workers (`researcher`, `reverse_engineer`) that burn tokens in their own sandbox and return a 10-line summary. |

---

## 📁 PowerPack Architecture

```
C:\Users\sayfp\devin-powerpack\
├── rules\
│   ├── mythos_v2.md             # Hardened Mythos v2.5 ruleset (262k cap, atomic slices, circuit breaker)
│   ├── reverse_engineering.md   # Guidelines for decompilation, binary & protocol reversing
│   └── AGENTS.md                # Compact global always-on directives
├── agents\                      # Custom Subagent profiles (Devin CLI & Desktop)
│   ├── researcher.md            # Read-only deep exploration & AST analysis
│   ├── reverse_engineer.md      # Binary, protocol, and obfuscated code deconstruction
│   └── code_reviewer.md         # Fast regression and security verification before commits
├── mcp\
│   └── mcp_config.json          # Live docs (Context7), Memory, and Playwright
├── tools\
│   ├── devin-run.bat            # Auto-truncator for noisy terminal commands
│   ├── devin-checkpoint.bat     # 1-command git shadow-commit
│   └── devin-state-init.bat     # Creates a clean .mythos/state.md in any project
├── install.bat                  # Idempotent installer (runs backup + syncs all configs)
├── install.ps1                  # Core PowerShell installer
├── uninstall.bat                # Rollback launcher
└── README.md                    # This guide
```

---

## 🚀 Installation & Update Resilience

Devin frequently updates its internal binaries in `%LOCALAPPDATA%\Programs\Devin`. Because this PowerPack lives in a dedicated persistent folder (`C:\Users\sayfp\devin-powerpack`), **your configurations and tools will never be wiped by Devin updates.**

### Running the Installer
Double-click `install.bat` (or execute via PowerShell):
```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\sayfp\devin-powerpack\install.ps1
```

The installer automatically:
1. Creates a timestamped backup of your current rules and MCP settings in `backups/`.
2. Syncs the rules to all active Devin directories (`%APPDATA%\Devin`, `%APPDATA%\devin`, `%LOCALAPPDATA%\devin`, `%USERPROFILE%\.devin`, `%USERPROFILE%\.config\devin`).
3. Deploys custom subagents (`researcher`, `reverse_engineer`, `code_reviewer`).
4. Configures production MCP servers (`context7`, `memory`, `playwright`).
5. Adds `tools\` to your user `PATH` so you can call `devin-run` anywhere.

---

## 🛠️ How to Use with SWE 2.0

### 1. Using Custom Subagents in Chat
In Devin Desktop or CLI, you can directly invoke the specialized workers:
- *"Research how auth tokens are signed across the repo using the researcher subagent."*
- *"Reverse engineer the payload encryption in `client.bundle.js` using the reverse_engineer subagent."*
- *"Review our latest edits against regressions using the code_reviewer subagent."*

### 2. Protecting Context During Heavy CLI Runs
Instead of running a verbose build or test command directly:
```bash
devin-run npm test
devin-run cargo build
```
`devin-run` outputs the top 35 and bottom 45 lines, saving the entire log to `.mythos/last_output.log`.

### 3. Quick State Template for New Projects
In any project folder, run:
```bash
devin-state-init
```
This generates a clean `.mythos/state.md` so Devin stays strictly within its 15-step slice budget.
