"""Unittest suite for RateLimiter."""

import time
import unittest
from concurrent.futures import ThreadPoolExecutor

from rate_limiter import RateLimiter


class TestBurstAllowance(unittest.TestCase):
    def test_burst_within_window_all_allowed(self):
        rl = RateLimiter(max_requests=5, window_seconds=60.0)
        self.assertTrue(all(rl.allow_request("c1") for _ in range(5)))

    def test_remaining_allowance_decrements(self):
        rl = RateLimiter(max_requests=5, window_seconds=60.0)
        for expected in (4, 3, 2, 1, 0):
            rl.allow_request("c1")
            self.assertEqual(rl.get_remaining_allowance("c1"), expected)

    def test_fresh_client_has_full_allowance(self):
        rl = RateLimiter(max_requests=3, window_seconds=60.0)
        self.assertEqual(rl.get_remaining_allowance("unknown"), 3)


class TestRejection(unittest.TestCase):
    def test_rejects_once_max_exceeded(self):
        rl = RateLimiter(max_requests=3, window_seconds=60.0)
        for _ in range(3):
            self.assertTrue(rl.allow_request("c1"))
        self.assertFalse(rl.allow_request("c1"))
        self.assertFalse(rl.allow_request("c1"))
        self.assertEqual(rl.get_remaining_allowance("c1"), 0)


class TestSlidingWindow(unittest.TestCase):
    def test_window_slides_and_allows_new_requests(self):
        rl = RateLimiter(max_requests=2, window_seconds=0.15)
        self.assertTrue(rl.allow_request("c1"))
        self.assertTrue(rl.allow_request("c1"))
        self.assertFalse(rl.allow_request("c1"))
        time.sleep(0.25)
        self.assertTrue(rl.allow_request("c1"))
        self.assertEqual(rl.get_remaining_allowance("c1"), 1)

    def test_partial_window_slide(self):
        rl = RateLimiter(max_requests=2, window_seconds=0.30)
        self.assertTrue(rl.allow_request("c1"))
        time.sleep(0.20)
        self.assertTrue(rl.allow_request("c1"))
        self.assertFalse(rl.allow_request("c1"))
        time.sleep(0.15)  # only the oldest timestamp has expired
        self.assertTrue(rl.allow_request("c1"))
        self.assertFalse(rl.allow_request("c1"))


class TestMultiClientIsolation(unittest.TestCase):
    def test_clients_do_not_share_allowance(self):
        rl = RateLimiter(max_requests=2, window_seconds=60.0)
        self.assertTrue(rl.allow_request("A"))
        self.assertTrue(rl.allow_request("A"))
        self.assertFalse(rl.allow_request("A"))
        self.assertTrue(rl.allow_request("B"))
        self.assertTrue(rl.allow_request("B"))
        self.assertEqual(rl.get_remaining_allowance("B"), 0)

    def test_reset_only_affects_target_client(self):
        rl = RateLimiter(max_requests=1, window_seconds=60.0)
        rl.allow_request("A")
        rl.allow_request("B")
        rl.reset("A")
        self.assertTrue(rl.allow_request("A"))
        self.assertFalse(rl.allow_request("B"))


class TestConcurrency(unittest.TestCase):
    def test_exact_allowance_under_parallel_load(self):
        rl = RateLimiter(max_requests=500, window_seconds=60.0)
        workers, calls_per_worker = 20, 50  # 1000 total calls vs 500 allowance
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(lambda _: rl.allow_request("hot"),
                                    range(workers * calls_per_worker)))
        self.assertEqual(sum(results), 500)
        self.assertEqual(rl.get_remaining_allowance("hot"), 0)

    def test_many_clients_parallel_isolation(self):
        rl = RateLimiter(max_requests=10, window_seconds=60.0)
        clients = [f"client-{i}" for i in range(50)]
        with ThreadPoolExecutor(max_workers=25) as pool:
            results = list(pool.map(rl.allow_request,
                                    [c for c in clients for _ in range(20)]))
        allowed = {}
        for client, ok in zip((c for c in clients for _ in range(20)), results):
            allowed[client] = allowed.get(client, 0) + ok
        self.assertTrue(all(v == 10 for v in allowed.values()))


class TestMemoryBound(unittest.TestCase):
    def test_expired_clients_are_evicted(self):
        rl = RateLimiter(max_requests=2, window_seconds=0.10)
        for i in range(200):
            rl.allow_request(f"client-{i}")
        self.assertEqual(len(rl._clients), 200)
        time.sleep(0.15)
        rl.get_remaining_allowance("trigger")  # purge happens per touched client
        for i in range(200):
            rl.get_remaining_allowance(f"client-{i}")
        self.assertEqual(len(rl._clients), 0)


class TestValidation(unittest.TestCase):
    def test_rejects_nonpositive_params(self):
        with self.assertRaises(ValueError):
            RateLimiter(0, 1.0)
        with self.assertRaises(ValueError):
            RateLimiter(1, 0.0)
        with self.assertRaises(ValueError):
            RateLimiter(1, -1.0)


if __name__ == "__main__":
    unittest.main()
