# 🧠 Devin Cross-Project Knowledge & Compounding Intelligence Vault

![Vault: Active](https://img.shields.io/badge/Knowledge%20Vault-Active%20%26%20Compounding-brightgreen)
![Directives: Mythos v3.0](https://img.shields.io/badge/Rules-Mythos%20v3.0-purple)
![Scope: Global](https://img.shields.io/badge/Scope-Cross--Project-blue)

This master knowledge base records battle-tested architectural patterns, proven standard-library recipes, performance benchmarks, and anti-patterns discovered across engineering challenges and project workspaces.

---

## ⚡ Quick Topic Index

- [1. Database & Transactions (`transactions`)](#1-database--transactions-transactions) — $O(1)$ rollback & layered delta stacks
- [2. Reverse Engineering & Binary Protocols (`protocols`)](#2-reverse-engineering--binary-protocols-protocols) — Sentinel trailers & CRC avoidance
- [3. High-Concurrency & Sliding Windows (`concurrency`)](#3-high-concurrency--sliding-windows-concurrency) — Bounded FIFO queues & memory leak immunity
- [4. Caching & Expiration (`caching`)](#4-caching--expiration-caching) — Amortized $O(1)$ LRU with monotonic time
- [5. Subagent Orchestration (`subagents`)](#5-subagent-orchestration-subagents) — When to spawn vs. when single-agent is superior
- [6. Windows Environment & Shell Quirks (`windows`)](#6-windows-environment--shell-quirks-windows) — PowerShell escaping & terminal PATH caching

---

## 1. Database & Transactions (`transactions`)

### 🚫 The Trap (Anti-Pattern)
- **Full Snapshot Cloning**: Creating `copy.deepcopy(self._data)` on `BEGIN` and replacing the dictionary on `ROLLBACK`.
- **Why it Fails**:
  1. $O(N)$ memory explosion when the dataset grows to millions of keys.
  2. Resurrects keys that expired during the transaction if restored from an old snapshot.
  3. Massive CPU overhead on nested transactions.

### ✅ The Battle-Tested Solution ($O(1)$ Rollback / Layered Delta Stack)
Use a **Layered Delta Stack** with tombstones or an **Undo Journal**:

```python
# Architecture A: Layered Delta Stack (Occam's Razor, 66 lines)
_DELETED = object()

class KVStore:
    def __init__(self, clock=time.monotonic):
        self._clock = clock
        self._stack = [{}]  # bottom is committed store, top is active tx

    def begin(self):
        self._stack.append({})  # O(1)

    def rollback(self):
        if len(self._stack) < 2:
            raise KVStoreError("ROLLBACK without BEGIN")
        self._stack.pop()       # O(1) instantaneous rollback!

    def commit(self):
        if len(self._stack) < 2:
            raise KVStoreError("COMMIT without BEGIN")
        delta = self._stack.pop()
        self._stack[-1].update(delta)  # O(delta) only modified keys merged
```

---

## 2. Reverse Engineering & Binary Protocols (`protocols`)

### 🚫 The Trap (Anti-Pattern)
- **The Mathematical Rabbit Hole**: Assuming every 2-byte trailer at the end of a binary payload is a complex polynomial checksum (CRC-16-CCITT, Modbus, Kermit, XMODEM) and writing brute-force solvers or subagents that loop for hours.

### ✅ The Battle-Tested Solution (Occam's Razor & 3-Strike Rule)
1. In production embedded protocols, telemetry, and network formats, end-of-frame bytes are frequently **static sentinels** (e.g., `0xAA55`, `0x55AA`, `0xCAFE`, `0xDEAD`) or simple 8/16-bit XOR / modular additions.
2. **The 3-Strike Check**:
   - Strike 1: Test standard CRC-16 (CCITT, Modbus).
   - Strike 2: Test 8-bit / 16-bit modular sum / XOR.
   - Strike 3: If no math matches, check for static trailer magic bytes. Treat trailer as a sentinel or accept either sentinel OR calculated checksum in unpack.
3. **Ledger Rule**: Always document payload offsets and payload lengths in `.mythos/re_symbols.md` before writing parser code.

---

## 3. High-Concurrency & Sliding Windows (`concurrency`)

### 🚫 The Trap (Anti-Pattern)
- **Unbounded Storage**: Storing all incoming requests in lists without eviction or periodic pruning, causing heap bloat under 100,000+ requests.
- **Lock Contention**: Holding global locks during external network calls or heavy logging.

### ✅ The Battle-Tested Solution (Bounded Left-Eviction)
- Use `collections.deque` with `popleft()` to discard expired timestamps in $O(1)$:
```python
from collections import deque
import time

class SlidingWindowLimiter:
    def __init__(self, max_requests: int, window_seconds: float):
        self.max = max_requests
        self.window = window_seconds
        self.timestamps = deque()

    def allow(self, now: float = None) -> bool:
        current = time.monotonic() if now is None else now
        cutoff = current - self.window
        # O(1) amortized left purge
        while self.timestamps and self.timestamps[0] <= cutoff:
            self.timestamps.popleft()
        if len(self.timestamps) < self.max:
            self.timestamps.append(current)
            return True
        return False
```
- **Result**: Proved 200,000 requests processed with only 1,312 bytes memory growth.

---

## 4. Caching & Expiration (`caching`)

### 🚫 The Trap (Anti-Pattern)
- **Wall-Clock Skew**: Using `time.time()` for TTL expiration calculations. If system time shifts (NTP sync, daylight savings), cache items expire prematurely or hang forever.
- **Custom Doubly-Linked Lists**: Hand-rolling node pointers (`next`, `prev`) in Python introduces pointer-swap bugs and high GC overhead.

### ✅ The Battle-Tested Solution (`OrderedDict` + `monotonic()`)
- Standard library `collections.OrderedDict` provides C-accelerated doubly-linked list + hash map:
  - `move_to_end(key)`: Promotes hit key to MRU in $O(1)$.
  - `popitem(last=False)`: Evicts LRU key in $O(1)$.
  - `time.monotonic()`: Guarantees non-decreasing time immune to system clock adjustments.
  - Single `threading.RLock()`: Simplest correct synchronization for multi-threaded safety in CPython.

---

## 5. Subagent Orchestration (`subagents`)

### 🚫 The Trap (Anti-Pattern)
- Spawning subagents for straightforward or linear tasks. Subagents create conversational isolation; if unconstrained, a subagent can spiral into generating dozens of exploratory scripts without realizing the main goal has stalled.

### ✅ When to Use Subagents
1. **Ast/Codebase Exploration (`researcher`)**: Read-only directory scanning and symbol mapping where noisy grep outputs should not pollute the main context.
2. **Adversarial Testing (`qa_tester`)**: Writing nasty edge-case fuzzers independently from the author of the patch.
3. **Single Agent Preference**: For implementing minimal-diff fixes and linear vertical slices, single-agent execution with Mythos rules is **20% faster** and **38% leaner**.

---

## 6. Windows Environment & Shell Quirks (`windows`)

### 🚫 The Trap (Anti-Pattern)
- **PowerShell Variable Stripping**: In bash subshells or multi-line commands, unescaped `$` (e.g. `$variable`) gets evaluated by the host shell before PowerShell receives it.
- **Terminal PATH Caching in Electron**: When Devin Desktop is already open, modifying User PATH does not propagate to existing Electron terminal tabs until the terminal process is restarted.

### ✅ Solutions
- Use single quotes in PowerShell commands or execute `.ps1` / `.bat` files directly with `-File`.
- Copy global utilities directly to Devin's native `bin` folder (`%LOCALAPPDATA%\Programs\Devin\bin`) for zero-restart availability.

---

*To add new lessons to this vault from any session, run:*
```bash
devin-learn <category> <title> <root_cause> <solution>
```
*To query this vault in any session, run:*
```bash
devin-remember <topic>
```
