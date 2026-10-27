"""Comprehensive tests for LRUCache: eviction order, TTL, thread-safety, edge cases."""

import threading
import time
import unittest

from lru_cache import LRUCache


class TestBasicOperations(unittest.TestCase):
    def test_put_and_get(self):
        c = LRUCache(3)
        c.put("a", 1)
        self.assertEqual(c.get("a"), 1)
        self.assertEqual(c.size(), 1)

    def test_missing_key_returns_none(self):
        c = LRUCache(3)
        self.assertIsNone(c.get("nonexistent"))
        self.assertIsNone(c.get(""))

    def test_invalid_capacity(self):
        for bad in (0, -1, -100):
            with self.assertRaises(ValueError):
                LRUCache(bad)

    def test_update_existing_key(self):
        c = LRUCache(2)
        c.put("a", 1)
        c.put("a", 2)
        self.assertEqual(c.get("a"), 2)
        self.assertEqual(c.size(), 1)

    def test_value_types(self):
        c = LRUCache(6)
        for k, v in [("s", "str"), ("i", 42), ("l", [1, 2]), ("d", {"x": 1}), ("n", None), ("t", (1,))]:
            c.put(k, v)
        for k, v in [("s", "str"), ("i", 42), ("l", [1, 2]), ("d", {"x": 1}), ("n", None), ("t", (1,))]:
            self.assertEqual(c.get(k), v)


class TestLRUEvictionOrder(unittest.TestCase):
    def test_capacity_never_exceeded(self):
        c = LRUCache(3)
        for i in range(100):
            c.put(f"k{i}", i)
            self.assertLessEqual(c.size(), 3)
        self.assertEqual(c.size(), 3)

    def test_evicts_least_recently_used(self):
        c = LRUCache(3)
        c.put("a", 1)
        c.put("b", 2)
        c.put("c", 3)
        c.put("d", 4)  # evicts "a"
        self.assertIsNone(c.get("a"))
        self.assertEqual(c.get("b"), 2)
        self.assertEqual(c.get("c"), 3)
        self.assertEqual(c.get("d"), 4)

    def test_get_refreshes_recency(self):
        c = LRUCache(3)
        c.put("a", 1)
        c.put("b", 2)
        c.put("c", 3)
        c.get("a")          # a becomes MRU; b is now LRU
        c.put("d", 4)       # evicts "b", not "a"
        self.assertEqual(c.get("a"), 1)
        self.assertIsNone(c.get("b"))

    def test_put_update_refreshes_recency(self):
        c = LRUCache(3)
        c.put("a", 1)
        c.put("b", 2)
        c.put("c", 3)
        c.put("a", 10)      # a becomes MRU; b is LRU
        c.put("d", 4)       # evicts "b"
        self.assertEqual(c.get("a"), 10)
        self.assertIsNone(c.get("b"))

    def test_eviction_order_sequence(self):
        c = LRUCache(3)
        for k in "abcde":
            c.put(k, k)
        # survivors should be c, d, e (the 3 most recent)
        self.assertIsNone(c.get("a"))
        self.assertIsNone(c.get("b"))
        for k in "cde":
            self.assertEqual(c.get(k), k)


class TestTTL(unittest.TestCase):
    def test_per_put_ttl_expires(self):
        c = LRUCache(5)
        c.put("short", 1, ttl_seconds=0.05)
        c.put("long", 2, ttl_seconds=60)
        self.assertEqual(c.get("short"), 1)
        time.sleep(0.08)
        self.assertIsNone(c.get("short"))
        self.assertEqual(c.get("long"), 2)

    def test_default_ttl_applies(self):
        c = LRUCache(5, default_ttl_seconds=0.05)
        c.put("a", 1)
        c.put("b", 2, ttl_seconds=60)   # explicit ttl overrides default
        c.put("c", 3, ttl_seconds=None) # uses default
        self.assertEqual(c.get("a"), 1)
        time.sleep(0.08)
        self.assertIsNone(c.get("a"))
        self.assertIsNone(c.get("c"))
        self.assertEqual(c.get("b"), 2)

    def test_no_ttl_never_expires(self):
        c = LRUCache(5)  # no default ttl
        c.put("a", 1)
        time.sleep(0.02)
        self.assertEqual(c.get("a"), 1)

    def test_expired_get_removes_entry(self):
        c = LRUCache(5)
        c.put("x", 1, ttl_seconds=0.03)
        time.sleep(0.05)
        self.assertIsNone(c.get("x"))
        self.assertEqual(c.size(), 0)

    def test_evict_expired_returns_count(self):
        c = LRUCache(10)
        c.put("e1", 1, ttl_seconds=0.03)
        c.put("e2", 2, ttl_seconds=0.03)
        c.put("e3", 3, ttl_seconds=0.03)
        c.put("keep", 4, ttl_seconds=60)
        time.sleep(0.05)
        self.assertEqual(c.evict_expired(), 3)
        self.assertEqual(c.size(), 1)
        self.assertEqual(c.get("keep"), 4)
        self.assertEqual(c.evict_expired(), 0)  # idempotent

    def test_expired_entry_evicted_first_on_overflow(self):
        # Expired-but-unpurged entries still occupy slots; a full cache evicts
        # oldest-first, so an expired LRU entry is naturally dropped first.
        c = LRUCache(2)
        c.put("old", 1, ttl_seconds=0.03)
        time.sleep(0.05)
        c.put("new1", 2)
        c.put("new2", 3)
        self.assertIsNone(c.get("old"))
        self.assertEqual(c.size(), 2)


class TestThreadSafety(unittest.TestCase):
    def test_50_threads_mixed_workload(self):
        c = LRUCache(100)
        n_threads = 50
        ops_per_thread = 500
        errors = []

        def worker(tid):
            try:
                for i in range(ops_per_thread):
                    k = f"key{(tid * ops_per_thread + i) % 250}"
                    if i % 3 == 0:
                        c.put(k, (tid, i))
                    elif i % 3 == 1:
                        c.get(k)
                    else:
                        c.put(k, (tid, i), ttl_seconds=0.5)
                    assert c.size() <= 100, f"capacity exceeded: {c.size()}"
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)
            self.assertFalse(t.is_alive(), "worker thread deadlocked")

        self.assertEqual(errors, [])
        self.assertLessEqual(c.size(), 100)

    def test_50_threads_same_key_no_lost_update_panic(self):
        c = LRUCache(10)
        errors = []

        def hammer(tid):
            try:
                for i in range(200):
                    c.put("hot", tid)
                    c.get("hot")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=hammer, args=(t,)) for t in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)
        self.assertEqual(errors, [])
        self.assertEqual(c.size(), 1)

    def test_concurrent_evict_expired(self):
        c = LRUCache(200, default_ttl_seconds=0.02)
        for i in range(200):
            c.put(f"k{i}", i)
        time.sleep(0.04)
        results = []

        def evictor():
            results.append(c.evict_expired())

        threads = [threading.Thread(target=evictor) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)
        self.assertEqual(sum(results), 200)  # each expired entry counted exactly once
        self.assertEqual(c.size(), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
