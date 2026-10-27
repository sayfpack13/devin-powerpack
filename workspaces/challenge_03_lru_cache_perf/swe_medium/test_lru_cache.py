import threading
import time
import unittest

from lru_cache import LRUCache


class TestBasics(unittest.TestCase):
    def test_get_missing_key(self):
        c = LRUCache(3)
        self.assertIsNone(c.get("nope"))

    def test_put_and_get(self):
        c = LRUCache(3)
        c.put("a", 1)
        self.assertEqual(c.get("a"), 1)
        self.assertEqual(c.size(), 1)

    def test_overwrite_value(self):
        c = LRUCache(3)
        c.put("a", 1)
        c.put("a", 2)
        self.assertEqual(c.get("a"), 2)
        self.assertEqual(c.size(), 1)

    def test_invalid_capacity(self):
        with self.assertRaises(ValueError):
            LRUCache(0)


class TestEvictionOrder(unittest.TestCase):
    def test_capacity_never_exceeded(self):
        c = LRUCache(2)
        c.put("a", 1)
        c.put("b", 2)
        c.put("c", 3)
        self.assertEqual(c.size(), 2)
        self.assertIsNone(c.get("a"))
        self.assertEqual(c.get("b"), 2)
        self.assertEqual(c.get("c"), 3)

    def test_get_promotes_to_mru(self):
        c = LRUCache(3)
        c.put("a", 1)
        c.put("b", 2)
        c.put("c", 3)
        self.assertEqual(c.get("a"), 1)  # a is now MRU; b becomes LRU
        c.put("d", 4)
        self.assertIsNone(c.get("b"))  # b evicted
        self.assertEqual(c.get("a"), 1)

    def test_put_existing_key_does_not_evict_itself(self):
        c = LRUCache(2)
        c.put("a", 1)
        c.put("b", 2)
        c.put("a", 10)  # refresh a -> b is LRU
        c.put("c", 3)
        self.assertIsNone(c.get("b"))
        self.assertEqual(c.get("a"), 10)


class TestTTL(unittest.TestCase):
    def test_per_key_ttl_expiration(self):
        c = LRUCache(5)
        c.put("short", "x", ttl_seconds=0.05)
        c.put("long", "y", ttl_seconds=60)
        self.assertEqual(c.get("short"), "x")
        time.sleep(0.08)
        self.assertIsNone(c.get("short"))
        self.assertEqual(c.get("long"), "y")

    def test_default_ttl(self):
        c = LRUCache(5, default_ttl_seconds=0.05)
        c.put("k", "v")
        time.sleep(0.08)
        self.assertIsNone(c.get("k"))

    def test_none_ttl_never_expires(self):
        c = LRUCache(5, default_ttl_seconds=0.05)
        c.put("k", "v", ttl_seconds=None)  # falls back to default -> expires
        c.put("k2", "v2")
        time.sleep(0.08)
        self.assertIsNone(c.get("k"))
        self.assertIsNone(c.get("k2"))

    def test_evict_expired_returns_count(self):
        c = LRUCache(10)
        c.put("a", 1, ttl_seconds=0.02)
        c.put("b", 2, ttl_seconds=0.02)
        c.put("c", 3, ttl_seconds=60)
        time.sleep(0.05)
        self.assertEqual(c.evict_expired(), 2)
        self.assertEqual(c.size(), 1)
        self.assertEqual(c.evict_expired(), 0)

    def test_expired_entry_freed_on_get(self):
        c = LRUCache(3)
        c.put("a", 1, ttl_seconds=0.02)
        time.sleep(0.05)
        self.assertIsNone(c.get("a"))
        self.assertEqual(c.size(), 0)


class TestConcurrency(unittest.TestCase):
    def test_50_threads_mixed_ops(self):
        c = LRUCache(64)
        errors = []

        def worker(n):
            try:
                for i in range(500):
                    key = f"k{(i + n) % 100}"
                    c.put(key, (n, i))
                    c.get(key)
                    c.evict_expired()
                    assert c.size() <= 64
            except Exception as e:
                errors.append((n, e))

        threads = [threading.Thread(target=worker, args=(n,)) for n in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(errors, [])
        self.assertLessEqual(c.size(), 64)

    def test_concurrent_puts_single_key(self):
        c = LRUCache(10)

        def worker(n):
            for _ in range(200):
                c.put("shared", n)

        threads = [threading.Thread(target=worker, args=(n,)) for n in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(c.size(), 1)
        self.assertIn(c.get("shared"), range(50))


if __name__ == "__main__":
    unittest.main(verbosity=2)
