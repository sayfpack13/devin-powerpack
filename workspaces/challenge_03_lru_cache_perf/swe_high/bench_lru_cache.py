"""devin-bench workload: exercises LRUCache put/get/evict under load."""

import time

from lru_cache import LRUCache

CAPACITY = 10_000
N_OPS = 500_000

cache = LRUCache(CAPACITY, default_ttl_seconds=300)

t0 = time.perf_counter()
for i in range(N_OPS):
    cache.put(f"k{i % 20_000}", i)
put_t = time.perf_counter() - t0

hits = 0
t0 = time.perf_counter()
for i in range(N_OPS):
    if cache.get(f"k{i % 20_000}") is not None:
        hits += 1
get_t = time.perf_counter() - t0

evicted = cache.evict_expired()

print(f"puts:   {N_OPS:>9,} ops in {put_t:.3f}s  ({N_OPS / put_t:,.0f} ops/s)")
print(f"gets:   {N_OPS:>9,} ops in {get_t:.3f}s  ({N_OPS / get_t:,.0f} ops/s)")
print(f"hits:   {hits:>9,} | evicted_expired: {evicted} | final size: {cache.size()}")
assert cache.size() == CAPACITY
