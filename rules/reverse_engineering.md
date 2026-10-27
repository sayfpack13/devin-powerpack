---
name: reverse_engineering_protocols
description: Surgical guidelines for reverse engineering binaries, protocols, and complex obfuscated systems
trigger: always_on
---

# Reverse Engineering & Complex Analysis Protocols

When handling reverse engineering, disassembling, decompiling, or analyzing complex unfamiliar architectures:

## 1. Zero-Memory-Bloat Analysis
- **Never cat or display raw disassembly/decompiled source over 100 lines.**
- Use command-line tools to filter output to disk before viewing:
  * For binaries: `strings -n 6 <binary> | grep -i <target> > .mythos/strings.txt`
  * For symbols: `nm -C <binary> | grep <symbol>` or `dumpbin /exports`
  * For packet/protocol captures: parse with targeted python one-liners outputting JSON schemas, not raw hex dumps.
- Always read `.mythos/strings.txt` using targeted line ranges or regex.

## 2. Dynamic Hypothesis Testing (Harness-First)
- Before writing complex patches or reimplementations, build a minimal test harness:
  * Create a standalone script (Python, Node.js, C++) that isolates the algorithm or endpoint.
  * Feed controlled inputs and record expected outputs.
  * Verify the behavioral model before touching the main codebase.

## 3. Persistent Symbol Map
- When reversing obfuscated code (e.g., JavaScript webpack bundles, ProGuard Java, stripped binaries), immediately record mappings in `.mythos/re_symbols.md`:
  ```markdown
  # Symbol Dictionary
  - `_0x3a9f`: AES-256-GCM decrypt function
  - `_0x1b4c`: Authorization token header ('X-API-Signature')
  - `param_1`: Session struct pointer
  ```
- This prevents re-investigating the same symbols when context is compacted.

## 4. Bounded Deobfuscation
- Do not attempt to deobfuscate an entire codebase at once.
- Identify the critical path (e.g., authentication flow, decryption routine, signature generator).
- Slice the critical path into isolated, testable modules.
