# Devin Global Directives (Mythos v3.0 Evolutionary Edition)

## Core Execution, Intelligence & Performance Discipline
- **First-Principles & Minimal Diff (Occam's Razor)**: Avoid 100-line naive patches. Always seek the highest-leverage, smallest possible change. Reuse existing project helpers and native standard library primitives before inventing new code.
- **Cross-Project Compounding Knowledge**: Before writing complex algorithms or architectures (Protocols, Transactions, Caching, Concurrency, Rate Limiting), check the global knowledge vault using `devin-remember <topic>` or read `%APPDATA%\devin\knowledge\CROSS_PROJECT_KNOWLEDGE.md`. When an obscure bug, trap, or high-performance pattern is resolved in ANY session, index it permanently via `devin-learn <category> <title> <root_cause> <solution>`.
- **Compounding Reflexion Memory**: Check the lessons vault (`.mythos/lessons/` and `%APPDATA%\Devin\lessons\`) before debugging known libraries. Never repeat a known mistake.
- **Runtime & Memory Efficiency**: Avoid full-data cloning ($O(N)$ snapshots). Use $O(1)$ delta journaling and streaming iterators. Verify algorithms using `devin-bench <file>`.
- **Accuracy Over Speed**: Never claim a task or bug fix is complete without providing exact terminal command output demonstrating a passing test/build. Speculation is strictly prohibited.
- **Reproduce Before Remediation**: Before fixing any bug, execute or create a test command that reproduces the failure (`FAIL`). Only declare it resolved when that exact command turns green (`PASS`).
- **Tool Failure Triage**: Distinguish environment/tooling failures (missing dependency, blocked port, wrong path) from code logic errors. Fix the tool/environment root cause; never alter application code to bypass a tooling failure.
- **Dual-Track Testing**: Run the specific test for the change AND the broader regression suite (`npm test`, `pytest`, `cargo test`) to ensure zero breaks across untouched modules.
- **Auto-Generate Test Harness**: If no test exists for a target feature, create a standalone verification script in `.mythos/verify_<feature>.<ext>` to physically prove correct execution.
- **Disk is Memory, Context is RAM**: The filesystem, `.mythos/state.md`, and `git status` / `git diff` are the ultimate sources of truth. Never rely on chat history.
- **Bounded Atomic Slices**: Break any task touching >5 files or 3 architectural layers into vertical slices (max 15 tool steps per slice). Verify each slice immediately.
- **Circuit Breaker (3 Strikes)**: Max 3 consecutive attempts on any bug. On Strike 3, immediately rollback dirty changes (`git checkout -- <file>`), log the blocker in `.mythos/state.md`, and pivot or escalate.
- **Subagent Delegation**: Delegate complex search, deep file scanning, or architectural evaluation to subagents (`architect`, `researcher`, `qa_tester`, `explorer`, `code_reviewer`, `reverse_engineer`) to shield the parent context window.

## Windows Environment & Shell Compatibility
- **Windows Command Execution**:
  - The default shell is Windows Command Prompt (`cmd.exe`) or PowerShell.
  - Never execute Linux-only utilities (`grep`, `sed`, `tail`, `head`) or bash subshell syntax `$(...)` in Windows CMD.
  - For searching in CMD: use `findstr /s /i "pattern" *` or standard Python/PowerShell one-liners.
  - For reading file parts: use Devin's native `read_file` tool with line ranges, or Python scripts.
  - Never run `timeout 30s` in Windows CMD. Use native Windows commands or Python for timing.
- **Context & File Inspection**:
  - Normal source files (under 800 lines) can and should be read fully with `read_file` to understand complete function definitions, types, and imports.
  - For massive generated bundles, minified code, or large log dumps (>1000 lines), use targeted search or line ranges.

## Anti-AFK & Zero Blind Sleep Mandate
- **No Blind Sleep Loops**:
  - Never run compound blind sleep loops in shell commands (e.g. `for i in 1 2 3 4; do sleep 15; done`).
  - Never insert long blind delays in Python test scripts (e.g. `time.sleep(10)` or `time.sleep(30)`).
- **Dynamic Polling with Early Exit**:
  - When waiting for a background process, file artifact, or network port in Python or scripts, poll in short intervals (250ms–500ms) with an explicit exit condition and break immediately when satisfied.
  - Cap all wait timeouts to 15–30 seconds maximum.
  - Fail fast: if the background process crashed or logged an error, inspect the log and halt in 2 seconds rather than waiting for a timeout.
