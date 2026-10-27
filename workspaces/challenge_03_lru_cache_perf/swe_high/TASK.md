# Challenge 03: O(1) Concurrent LRU Cache with TTL & Eviction

## Objective
Build a production-grade, thread-safe LRU (Least Recently Used) cache with O(1) get/set complexity, TTL expiration, and exact capacity enforcement using standard library primitives.

## Instructions:
Paste the prompt below into Devin chat:

```markdown
Initialize this clean workspace using devin-state-init.

Build a thread-safe, high-concurrency LRU Cache with TTL support in Python.

Requirements:
1. Core API:
   - LRUCache(capacity: int, default_ttl_seconds: float = None)
   - get(key: str) -> Any (moves to most recently used)
   - put(key: str, value: Any, ttl_seconds: float = None)
   - evict_expired() -> int
   - size() -> int
2. Performance & Memory Mandates (Mythos v3.0):
   - O(1) Get and Put operations (use OrderedDict or doubly linked list + hash map).
   - Strict capacity limit: Never exceed capacity items; evict least recently used upon insertion.
   - Run devin-bench on the implementation to verify CPU time and peak RAM.
3. Automated Testing & Verification:
   - Write comprehensive tests for LRU eviction order, TTL expiration, thread-safety under 50 concurrent threads, and non-existent key handling.
   - Execute tests and output exit code 0 evidence.
```
