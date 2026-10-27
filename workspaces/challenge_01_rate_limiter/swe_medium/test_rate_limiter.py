import concurrent.futures
import time
import unittest

from rate_limiter import RateLimiter


class TestRateLimiter(unittest.TestCase):
    def test_burst_within_limit(self):
        rl = RateLimiter(5, 1.0)
        self.assertTrue(all(rl.allow_request("c") for _ in range(5)))
        self.assertEqual(rl.get_remaining_allowance("c"), 0)

    def test_rejection_over_limit(self):
        rl = RateLimiter(3, 10.0)
        for _ in range(3):
            rl.allow_request("c")
        self.assertFalse(rl.allow_request("c"))
        self.assertFalse(rl.allow_request("c"))

    def test_window_slides(self):
        rl = RateLimiter(2, 0.1)
        rl.allow_request("c")
        rl.allow_request("c")
        self.assertFalse(rl.allow_request("c"))
        time.sleep(0.15)
        self.assertTrue(rl.allow_request("c"))

    def test_multi_client_isolation(self):
        rl = RateLimiter(2, 10.0)
        rl.allow_request("a")
        rl.allow_request("a")
        self.assertFalse(rl.allow_request("a"))
        self.assertTrue(rl.allow_request("b"))
        self.assertEqual(rl.get_remaining_allowance("b"), 1)

    def test_reset(self):
        rl = RateLimiter(1, 10.0)
        rl.allow_request("c")
        self.assertFalse(rl.allow_request("c"))
        rl.reset("c")
        self.assertTrue(rl.allow_request("c"))
        rl.reset("nonexistent")  # no error

    def test_remaining_for_unknown_client(self):
        rl = RateLimiter(4, 1.0)
        self.assertEqual(rl.get_remaining_allowance("new"), 4)

    def test_concurrent_requests_never_exceed_limit(self):
        max_req = 50
        rl = RateLimiter(max_req, 60.0)
        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
            results = list(ex.map(lambda _: rl.allow_request("hot"), range(500)))
        self.assertEqual(sum(results), max_req)
        self.assertEqual(rl.get_remaining_allowance("hot"), 0)

    def test_concurrent_multi_client(self):
        rl = RateLimiter(10, 60.0)
        clients = [f"c{i}" for i in range(8)]

        def hammer(cid):
            return sum(rl.allow_request(cid) for _ in range(100))

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
            counts = list(ex.map(hammer, clients))
        self.assertEqual(counts, [10] * 8)

    def test_memory_bounded_purge(self):
        # deque per client never exceeds max_requests entries
        rl = RateLimiter(5, 0.05)
        for _ in range(1000):
            rl.allow_request("c")
            time.sleep(0.001)
        dq = rl._hits["c"]
        self.assertLessEqual(len(dq), 5)


if __name__ == "__main__":
    unittest.main()
