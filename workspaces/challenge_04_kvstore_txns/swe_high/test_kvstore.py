import time
import unittest

from kvstore import KVStore, TransactionError


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class TestCoreOps(unittest.TestCase):
    def setUp(self):
        self.kv = KVStore()

    def test_set_get(self):
        self.kv.set("a", 1)
        self.assertEqual(self.kv.get("a"), 1)

    def test_get_missing_returns_none(self):
        self.assertIsNone(self.kv.get("nope"))

    def test_get_missing_custom_default(self):
        self.assertEqual(self.kv.get("nope", "d"), "d")

    def test_delete(self):
        self.kv.set("a", 1)
        self.assertTrue(self.kv.delete("a"))
        self.assertIsNone(self.kv.get("a"))

    def test_delete_missing_returns_false(self):
        self.assertFalse(self.kv.delete("nope"))

    def test_overwrite(self):
        self.kv.set("a", 1)
        self.kv.set("a", 2)
        self.assertEqual(self.kv.get("a"), 2)


class TestTTL(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.kv = KVStore(clock=self.clock)

    def test_expires_after_ttl(self):
        self.kv.set("a", 1, ttl=10)
        self.assertEqual(self.kv.get("a"), 1)
        self.clock.advance(10)
        self.assertIsNone(self.kv.get("a"))

    def test_alive_before_ttl(self):
        self.kv.set("a", 1, ttl=10)
        self.clock.advance(9.9)
        self.assertEqual(self.kv.get("a"), 1)

    def test_no_ttl_persists(self):
        self.kv.set("a", 1)
        self.clock.advance(10_000)
        self.assertEqual(self.kv.get("a"), 1)

    def test_overwrite_without_ttl_clears_expiry(self):
        self.kv.set("a", 1, ttl=5)
        self.kv.set("a", 2)
        self.clock.advance(100)
        self.assertEqual(self.kv.get("a"), 2)

    def test_negative_ttl_rejected(self):
        with self.assertRaises(ValueError):
            self.kv.set("a", 1, ttl=-1)

    def test_zero_ttl_expires_immediately(self):
        self.kv.set("a", 1, ttl=0)
        self.assertIsNone(self.kv.get("a"))

    def test_real_clock_expiry(self):
        kv = KVStore()
        kv.set("a", 1, ttl=0.05)
        time.sleep(0.06)
        self.assertIsNone(kv.get("a"))


class TestTransactions(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.kv = KVStore(clock=self.clock)

    def test_commit_persists(self):
        self.kv.begin()
        self.kv.set("a", 1)
        self.kv.commit()
        self.assertEqual(self.kv.get("a"), 1)
        self.assertEqual(self.kv.tx_depth, 0)

    def test_reads_see_uncommitted_writes(self):
        self.kv.begin()
        self.kv.set("a", 1)
        self.assertEqual(self.kv.get("a"), 1)

    def test_rollback_restores_value(self):
        self.kv.set("a", 1)
        self.kv.begin()
        self.kv.set("a", 2)
        self.kv.rollback()
        self.assertEqual(self.kv.get("a"), 1)

    def test_rollback_removes_new_key(self):
        self.kv.begin()
        self.kv.set("a", 1)
        self.kv.rollback()
        self.assertIsNone(self.kv.get("a"))

    def test_rollback_restores_deleted_key(self):
        self.kv.set("a", 1)
        self.kv.begin()
        self.kv.delete("a")
        self.kv.rollback()
        self.assertEqual(self.kv.get("a"), 1)

    def test_commit_without_begin_raises(self):
        with self.assertRaises(TransactionError):
            self.kv.commit()

    def test_rollback_without_begin_raises(self):
        with self.assertRaises(TransactionError):
            self.kv.rollback()

    def test_nested_inner_commit_then_outer_commit(self):
        self.kv.begin()
        self.kv.set("a", 1)
        self.kv.begin()
        self.kv.set("b", 2)
        self.kv.commit()
        self.kv.commit()
        self.assertEqual(self.kv.get("a"), 1)
        self.assertEqual(self.kv.get("b"), 2)

    def test_nested_inner_rollback_keeps_outer(self):
        self.kv.begin()
        self.kv.set("a", 1)
        self.kv.begin()
        self.kv.set("a", 2)
        self.kv.set("b", 9)
        self.kv.rollback()
        self.assertEqual(self.kv.get("a"), 1)
        self.assertIsNone(self.kv.get("b"))
        self.kv.commit()
        self.assertEqual(self.kv.get("a"), 1)

    def test_nested_inner_commit_then_outer_rollback(self):
        self.kv.set("a", 0)
        self.kv.begin()
        self.kv.set("a", 1)
        self.kv.begin()
        self.kv.set("a", 2)
        self.kv.commit()
        self.kv.rollback()
        self.assertEqual(self.kv.get("a"), 0)

    def test_rollback_does_not_resurrect_expired_key(self):
        self.kv.set("a", 1, ttl=5)
        self.clock.advance(10)  # a is expired but not yet reaped
        self.kv.begin()
        self.kv.set("a", 2)
        self.kv.rollback()
        self.assertIsNone(self.kv.get("a"))

    def test_rollback_restores_live_ttl_entry(self):
        self.kv.set("a", 1, ttl=100)
        self.kv.begin()
        self.kv.delete("a")
        self.kv.rollback()
        self.assertEqual(self.kv.get("a"), 1)
        self.clock.advance(101)
        self.assertIsNone(self.kv.get("a"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
