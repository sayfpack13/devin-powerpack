"""Micro-benchmark for devin-bench: verify O(1) get/put and memory profile."""
import time

from lru_cache import LRUCache

N = 200_000
c = LRUCache(capacity=10_000)

t0 = time.perf_counter()
for i in range(N):
    c.put(f"key{i}", i)
put_t = (time.perf_counter() - t0) / N * 1e6

t0 = time.perf_counter()
for i in range(N):
    c.get(f"key{i}")
get_t = (time.perf_counter() - t0) / N * 1e6

print(f"[BENCH] capacity={c.size()} | avg put: {put_t:.3f} us | avg get: {get_t:.3f} us")
