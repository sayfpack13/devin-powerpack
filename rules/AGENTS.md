# Devin Global Directives (Mythos v2.6 Accuracy Edition)

## Core Execution & Accuracy Discipline
- **Accuracy Over Speed**: Never claim a task or bug fix is complete without providing exact terminal command output demonstrating a passing test/build. Speculation ("this should work now") is strictly prohibited.
- **Reproduce Before Remediation**: Before fixing any bug, execute or create a test command that reproduces the failure (`FAIL`). Only declare it resolved when that exact command turns green (`PASS`).
- **Tool Failure Triage**: Distinguish environment/tooling failures (missing dependency, blocked port, wrong path) from code logic errors. Fix the tool/environment root cause; never alter code to bypass a tooling failure.
- **Dual-Track Testing**: Run the specific test for the change AND the broader regression suite (`npm test`, `pytest`, `cargo test`) to ensure zero breaks across untouched modules.
- **Auto-Generate Test Harness**: If no test exists for a target feature, create a standalone verification script in `.mythos/verify_<feature>.<ext>` to physically prove correct execution.
- **Disk is Memory, Context is RAM**: The filesystem, `.mythos/state.md`, and `git status` / `git diff` are the ultimate sources of truth. Never rely on chat history.
- **262K Hard Context Budget**: Forbid reading files over 200 lines entirely into context. Use symbol navigation, grep, or line slices (`sed -n 'X,Yp'`).
- **Bounded Atomic Slices**: Break any task touching >5 files or 3 architectural layers into vertical slices (max 15 tool steps per slice). Verify each slice immediately.
- **Circuit Breaker (3 Strikes)**: Max 3 consecutive attempts on any bug. On Strike 3, immediately rollback dirty changes (`git checkout -- <file>`), log the blocker in `.mythos/state.md`, and pivot or escalate.
- **Subagent Delegation**: Delegate complex search, deep file scanning, or adversarial testing to subagents (`researcher`, `qa_tester`) to shield the parent context window.
