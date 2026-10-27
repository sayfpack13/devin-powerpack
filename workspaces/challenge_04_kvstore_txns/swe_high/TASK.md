# Challenge 04: In-Memory Key-Value Store with Nested Atomic Transactions & TTL

## Objective
Build a lightweight, production-grade In-Memory Key-Value Store with TTL (Time-To-Live) and Atomic Transactions in Python (or Node.js).

## Instructions:
Paste the prompt below into Devin chat:

```markdown
Initialize this clean workspace using devin-state-init.

Build a lightweight, production-grade In-Memory Key-Value Store with TTL (Time-To-Live) and Atomic Transactions in Python (or Node.js).

Requirements:
1. Core Operations: SET(key, value, ttl_seconds?), GET(key), DELETE(key).
2. Transaction Support: 
   - BEGIN: Starts a transaction.
   - COMMIT: Commits changes atomically.
   - ROLLBACK: Reverts all changes made since BEGIN. Supports at least 2 levels of nested transactions.
3. Architecture & Intelligence:
   - Use First-Principles & Occam's Razor: Do NOT install external packages; write clean, idiomatic code using standard library primitives with the smallest possible diff.
4. Automated Testing & Proof of Accuracy:
   - Build an automated test suite covering:
     * Basic GET/SET/DELETE
     * TTL key expiration
     * Transaction commit
     * Transaction rollback (including nested rollback)
     * Edge cases (getting non-existent key, committing without BEGIN)
   - Execute the test suite and provide the exact terminal output demonstrating that all assertions pass with exit code 0.
```
