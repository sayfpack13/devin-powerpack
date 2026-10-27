# Challenge 01: Thread-Safe Sliding Window Rate Limiter

## Objective
Build a lightweight, thread-safe, high-concurrency Sliding Window Rate Limiter in Python with bounded memory consumption and zero external dependencies.

## Instructions:
Paste the prompt below into Devin chat:

```markdown
Initialize this clean workspace using devin-state-init.

Build a thread-safe, high-concurrency Sliding Window Rate Limiter in Python (or Node.js) with zero external dependencies.

Requirements:
1. Core API:
   - RateLimiter(max_requests: int, window_seconds: float)
   - allow_request(client_id: str) -> bool
   - get_remaining_allowance(client_id: str) -> int
   - reset(client_id: str) -> None
2. Performance & Memory Mandates (Mythos v3.0):
   - Memory MUST be bounded: Expired timestamps must be purged lazily or via a ring-buffer/deque so memory does not leak over hours.
   - Use First-Principles & Occam's Razor: Do NOT store unbounded timestamp lists; use a sliding deque or ring-buffer with minimal diff.
   - Thread safety: Use threading.Lock() appropriately for concurrent calls.
3. Automated Testing & Verification:
   - Build a unittest suite covering:
     * Burst allowance within window limit
     * Rejection once max_requests is exceeded
     * Window sliding allowing new requests after elapsed time
     * Multi-client isolation (client A does not exhaust client B)
     * High-concurrency test using concurrent.futures
   - Profile the test with devin-bench to prove memory bounds.
   - Output exact exit code 0 evidence.
```
