# Devin PowerPack: Continuous Experiments & Learning Ledger

| Run ID | Timestamp | Model | Task / Run Name | Time | Peak Memory | Angle / Architecture | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |

| [20261027_152345](RUN_20261027_152345_KVStore_SWE2_Medium_Benchmark.md) | 2026-10-27 15:23:45 | SWE-2 Medium | KVStore_SWE2_Medium_Benchmark | 0.237360s | 5667.62 KB | - Journal-based nested txns: stack of dicts recording pre-txn key state. | Verified |

| [20261027_152346](RUN_20261027_152346_KVStore_SWE2_High_Benchmark.md) | 2026-10-27 15:23:46 | SWE-2 High | KVStore_SWE2_High_Benchmark | 0.232550s | 5668.79 KB | - Angle 2: snapshot-per-BEGIN (`dict(self._data)` copy on a stack). COMMIT drops snapshot, ROLLBACK restores it. Smallest possible diff, correct arbitrary nesting; values stored as (value, expires_at) tuples so shallow copy suffices. Clock injected for deterministic TTL tests. | Verified |

