# Devin PowerPack: Continuous Experiments & Learning Ledger

| Run ID | Timestamp | Model | Task / Run Name | Time | Peak Memory | Angle / Architecture | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |

| [20261027_152345](RUN_20261027_152345_KVStore_SWE2_Medium_Benchmark.md) | 2026-10-27 15:23:45 | SWE-2 Medium | KVStore_SWE2_Medium_Benchmark | 0.237360s | 5667.62 KB | - Journal-based nested txns: stack of dicts recording pre-txn key state. | Verified |

| [20261027_152346](RUN_20261027_152346_KVStore_SWE2_High_Benchmark.md) | 2026-10-27 15:23:46 | SWE-2 High | KVStore_SWE2_High_Benchmark | 0.232550s | 5668.79 KB | - Angle 2: snapshot-per-BEGIN (`dict(self._data)` copy on a stack). COMMIT drops snapshot, ROLLBACK restores it. Smallest possible diff, correct arbitrary nesting; values stored as (value, expires_at) tuples so shallow copy suffices. Clock injected for deterministic TTL tests. | Verified |

| [20261027_153250](RUN_20261027_153250_Challenge01_RateLimiter_Medium.md) | 2026-10-27 15:32:50 | SWE-2 Medium | Challenge01_RateLimiter_Medium | 0.274119s | 6230.30 KB | Per-client `deque` of monotonic timestamps, lazy purge on access -> O(1) ops, memory <= max_requests/client. Single `threading.Lock` (GIL-friendly, minimal diff). | Verified |

| [20261027_153252](RUN_20261027_153252_Challenge01_RateLimiter_High.md) | 2026-10-27 15:32:52 | SWE-2 High | Challenge01_RateLimiter_High | 0.255508s | 5666.57 KB | Per-client `collections.deque` of `time.monotonic()` timestamps; purge expired from left on each call; evict empty deques. No unbounded lists; single Lock. Minimal-diff idiomatic fix. | Verified |

