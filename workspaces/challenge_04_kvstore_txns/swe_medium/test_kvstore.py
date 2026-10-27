import unittest

from kvstore import KVStore, KVStoreError


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += seconds


class TestBasicOps(unittest.TestCase):
    def setUp(self):
        self.kv = KVStore()

    def test_set_get(self):
        self.kv.set("a", 1)
        self.assertEqual(self.kv.get("a"), 1)

    def test_get_missing_key(self):
        self.assertIsNone(self.kv.get("nope"))

    def test_overwrite(self):
        self.kv.set("a", 1)
        self.kv.set("a", 2)
        self.assertEqual(self.kv.get("a"), 2)

    def test_delete(self):
        self.kv.set("a", 1)
        self.assertTrue(self.kv.delete("a"))
        self.assertIsNone(self.kv.get("a"))

    def test_delete_missing_key(self):
        self.assertFalse(self.kv.delete("nope"))


class TestTTL(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.kv = KVStore(now=self.clock)

    def test_expires_after_ttl(self):
        self.kv.set("k", "v", ttl_seconds=5)
        self.assertEqual(self.kv.get("k"), "v")
        self.clock.advance(5)
        self.assertIsNone(self.kv.get("k"))

    def test_alive_before_ttl(self):
        self.kv.set("k", "v", ttl_seconds=5)
        self.clock.advance(4.9)
        self.assertEqual(self.kv.get("k"), "v")

    def test_no_ttl_never_expires(self):
        self.kv.set("k", "v")
        self.clock.advance(1e9)
        self.assertEqual(self.kv.get("k"), "v")

    def test_ttl_inside_uncommitted_transaction(self):
        self.kv.begin()
        self.kv.set("k", "v", ttl_seconds=5)
        self.clock.advance(6)
        self.kv.commit()
        self.assertIsNone(self.kv.get("k"))


class TestTransactions(unittest.TestCase):
    def setUp(self):
        self.kv = KVStore()

    def test_commit_persists_changes(self):
        self.kv.set("a", 1)
        self.kv.begin()
        self.kv.set("a", 2)
        self.kv.set("b", 3)
        self.kv.commit()
        self.assertEqual(self.kv.get("a"), 2)
        self.assertEqual(self.kv.get("b"), 3)

    def test_rollback_reverts_changes(self):
        self.kv.set("a", 1)
        self.kv.begin()
        self.kv.set("a", 2)
        self.kv.delete("a")
        self.kv.set("b", 3)
        self.kv.rollback()
        self.assertEqual(self.kv.get("a"), 1)
        self.assertIsNone(self.kv.get("b"))

    def test_nested_commit_inner(self):
        self.kv.begin()
        self.kv.set("a", 1)
        self.kv.begin()
        self.kv.set("a", 2)
        self.kv.commit()
        self.assertEqual(self.kv.get("a"), 2)
        self.kv.rollback()  # outer rollback discards inner commit
        self.assertIsNone(self.kv.get("a"))

    def test_nested_rollback_inner_only(self):
        self.kv.begin()
        self.kv.set("a", 1)
        self.kv.begin()
        self.kv.set("a", 99)
        self.kv.set("b", 2)
        self.kv.rollback()
        self.assertEqual(self.kv.get("a"), 1)
        self.assertIsNone(self.kv.get("b"))
        self.kv.commit()
        self.assertEqual(self.kv.get("a"), 1)

    def test_commit_without_begin_raises(self):
        with self.assertRaises(KVStoreError):
            self.kv.commit()

    def test_rollback_without_begin_raises(self):
        with self.assertRaises(KVStoreError):
            self.kv.rollback()

    def test_transaction_depth(self):
        self.assertEqual(self.kv.transaction_depth, 0)
        self.kv.begin()
        self.kv.begin()
        self.assertEqual(self.kv.transaction_depth, 2)
        self.kv.rollback()
        self.assertEqual(self.kv.transaction_depth, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
