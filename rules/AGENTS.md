# Devin Global Directives (Mythos v3.0 Evolutionary Edition)

## Core Execution, Intelligence & Performance Discipline
- **First-Principles & Minimal Diff (Occam's Razor)**: Avoid 100-line naive patches. Always seek the highest-leverage, smallest possible change. Reuse existing project helpers and native standard library primitives before inventing new code.
- **Compounding Reflexion Memory**: Check the lessons vault (`.mythos/lessons/` and `%APPDATA%\Devin\lessons\`) before debugging known libraries. When an obscure bug, trap, or high-performance pattern is resolved, index it permanently using `devin-learn`. Never repeat a known mistake.
- **Runtime & Memory Efficiency**: Avoid full-data cloning ($O(N)$ snapshots). Use $O(1)$ delta journaling and streaming iterators. Verify algorithms using `devin-bench <file>`.
- **Accuracy Over Speed**: Never claim a task or bug fix is complete without providing exact terminal command output demonstrating a passing test/build. Speculation is strictly prohibited.
- **Reproduce Before Remediation**: Before fixing any bug, execute or create a test command that reproduces the failure (`FAIL`). Only declare it resolved when that exact command turns green (`PASS`).
- **Tool Failure Triage**: Distinguish environment/tooling failures (missing dependency, blocked port, wrong path) from code logic errors. Fix the tool/environment root cause; never alter application code to bypass a tooling failure.
- **Dual-Track Testing**: Run the specific test for the change AND the broader regression suite (`npm test`, `pytest`, `cargo test`) to ensure zero breaks across untouched modules.
- **Auto-Generate Test Harness**: If no test exists for a target feature, create a standalone verification script in `.mythos/verify_<feature>.<ext>` to physically prove correct execution.
- **Disk is Memory, Context is RAM**: The filesystem, `.mythos/state.md`, and `git status` / `git diff` are the ultimate sources of truth. Never rely on chat history.
- **262K Hard Context Budget**: Forbid reading files over 200 lines entirely into context. Use symbol navigation, grep, or line slices (`sed -n 'X,Yp'`).
- **Bounded Atomic Slices**: Break any task touching >5 files or 3 architectural layers into vertical slices (max 15 tool steps per slice). Verify each slice immediately.
- **Circuit Breaker (3 Strikes)**: Max 3 consecutive attempts on any bug. On Strike 3, immediately rollback dirty changes (`git checkout -- <file>`), log the blocker in `.mythos/state.md`, and pivot or escalate.
- **Subagent Delegation**: Delegate complex search, deep file scanning, or architectural evaluation to subagents (`architect`, `researcher`, `qa_tester`) to shield the parent context window.
