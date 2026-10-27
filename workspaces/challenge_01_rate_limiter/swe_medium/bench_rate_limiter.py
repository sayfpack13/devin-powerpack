"""Memory-bound proof: hammer one client 200k times over many window
lifetimes; tracemalloc growth must stay tiny (bounded by max_requests)."""
import sys
import time
import tracemalloc

from rate_limiter import RateLimiter

rl = RateLimiter(10, 0.01)
tracemalloc.start()
# warmup
for _ in range(1000):
    rl.allow_request("c")
    rl._now()
base = tracemalloc.get_traced_memory()[0]

n = 200_000
t0 = time.perf_counter()
for i in range(n):
    rl.allow_request("c")
    if i % 100 == 0:
        time.sleep(0.001)  # let window expire repeatedly
elapsed = time.perf_counter() - t0
peak = tracemalloc.get_traced_memory()[1]
growth = peak - base
print(f"requests={n} elapsed={elapsed:.2f}s throughput={n/elapsed:,.0f} req/s")
print(f"tracemalloc growth over baseline: {growth} bytes")
print(f"deque size for 'c': {len(rl._hits['c'])} (max 10)")
tracemalloc.stop()
assert growth < 1_000_000, "memory leaked!"
assert len(rl._hits["c"]) <= 10
print("MEMORY BOUNDED: PASS")
sys.exit(0)
