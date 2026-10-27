# Devin SWE 2.0 PowerPack

A production-grade enhancement suite for **Devin SWE 2.0 (`swe-2-medium`)** that bridges the intelligence and reasoning gap, maximizes accuracy, enforces Occam's Razor minimal-diff solutions, automates debugging and verification, and overcomes context-window exhaustion (262K limit).

---

## ⚡ Overcoming the SWE 2.0 Intelligence & Reasoning Gap

Smaller, specialized coding models like `swe-2-medium` struggle compared to frontier reasoning models because they gravitate toward **naive brute-force bloat** (writing 100-line complex workarounds instead of a 3-line idiomatic fix).

| Frontier AI Advantage | Raw SWE 2.0 Failure | PowerPack Solution |
| :--- | :--- | :--- |
| **First-Principles Thinking** | Writes 100-line custom loops & reinvented helper functions | **Occam's Razor Mandate**: Forbids patches >30 lines without evaluating built-in standard library or framework primitives first. |
| **Finding the Best Angle** | Grabs the first naive idea and brute-forces it | **Dual-Angle Thinking & `architect` Subagent**: Formulates Angle 1 (obvious patch) vs Angle 2 (high-leverage root-cause fix) and chooses the smallest diff. |
| **Reusing Existing Levers** | Rewrites utilities that already exist in the repo | **Exploit Existing Primitives**: Mandates grepping `utils/`, `helpers/`, `lib/` before creating new helper code. |
| **Root-Cause vs Symptom** | Monkey-patches errors with blanket try/catch or null checks | **Eliminate Root Cause**: Prohibits symptom-masking; traces where bad state enters the pipeline. |
| **Premature "Done"** | Claims code is complete without runtime proof | **Zero-Speculation & Reproduction-First**: Mandates reproducible failing test before fix, and passing test with exit code 0 after. |
| **Context Exhaustion** | Dumps 1,000+ line files into memory | **Surgical Context Hygiene & `devin-run`**: Strict ban on reading files >200 lines; auto-truncates noisy CLI logs. |
| **Runaway Bug Loops** | Tries random edits 10+ times, breaking prior work | **3-Strike Circuit Breaker**: Hard limit of 3 attempts. On strike 3, automatically runs `git checkout -- <file>` to revert dirty state. |

---

## 📁 PowerPack Architecture

```
C:\Users\sayfp\devin-powerpack\
├── rules\
│   ├── mythos_v2.md             # Hardened Mythos v2.7 (Intelligence & First-Principles edition)
│   ├── reverse_engineering.md   # Guidelines for decompilation, binary & protocol reversing
│   └── AGENTS.md                # Global always-on directives
├── agents\                      # Custom Subagent profiles (Devin CLI & Desktop)
│   ├── architect.md             # First-principles problem solver & minimal-diff angle evaluator
│   ├── researcher.md            # Read-only deep exploration & AST analysis
│   ├── reverse_engineer.md      # Binary, protocol, and obfuscated code deconstruction
│   ├── code_reviewer.md         # Fast regression and security verification before commits
│   └── qa_tester.md             # Adversarial testing, edge-case validation & reproduction
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
3. Deploys custom subagents (`architect`, `researcher`, `reverse_engineer`, `code_reviewer`, `qa_tester`).
4. Configures production MCP servers (`context7`, `memory`, `playwright`).
5. Adds `tools\` to your user `PATH` so you can call `devin-run` anywhere.

---

## 🛠️ How to Use with SWE 2.0

### 1. Using Custom Subagents in Chat
In Devin Desktop or CLI, you can directly invoke the specialized workers:
- *"Think through this tough problem from first principles using the **architect** subagent to find the shortest, cleanest angle."*
- *"Stress-test this login logic with edge cases using the **qa_tester** subagent."*
- *"Research how auth tokens are signed across the repo using the **researcher** subagent."*
- *"Reverse engineer the payload encryption in `client.bundle.js` using the **reverse_engineer** subagent."*
- *"Review our latest edits against regressions using the **code_reviewer** subagent."*

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
This generates a clean `.mythos/state.md` so Devin stays strictly within its 15-step slice budget and logs verification evidence.
