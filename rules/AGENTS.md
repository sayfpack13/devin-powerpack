# Devin Global Directives (Mythos v2.5 Powered)

## Core Execution Discipline
- **Disk is Memory, Context is RAM**: The filesystem, `.mythos/state.md`, and `git status` / `git diff` are the ultimate sources of truth. Never rely on chat history to recall prior modifications.
- **262K Hard Context Budget**: Forbid reading files over 200 lines entirely into context. Use symbol navigation, grep, AST queries, or line slices (`sed -n 'X,Yp'`).
- **Bounded Atomic Slices**: Break any task touching >5 files or 3 architectural layers into vertical slices (max 15 tool steps per slice). Verify each slice immediately before progressing.
- **Circuit Breaker (3 Strikes)**: Max 3 consecutive attempts on any bug. On Strike 3, immediately rollback dirty changes (`git checkout -- <file>`), log the blocker in `.mythos/state.md`, and pivot or escalate.
- **Output Discipline**: Pipe all verbose commands (builds, tests, logs) through tail/grep or use `devin-run <cmd>`. Never allow raw multiline command dumps into context.
- **Subagent Delegation**: Delegate complex search, deep file scanning, or reverse engineering investigations to subagents (`researcher` or `subagent_explore`) to shield the parent context window.
- **Persistent State**: Maintain `.mythos/state.md` under 100 lines at all times. Update it after each verified slice.
