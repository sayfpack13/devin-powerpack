"""Thread-safe, O(1) LRU cache with TTL support.

Uses OrderedDict (hash map + doubly linked list under the hood) so get/put
are amortized O(1). All mutations are guarded by a single reentrant lock,
which is the simplest correct design under CPython.
"""

import time
from collections import OrderedDict
from threading import RLock

_MISSING = object()


class LRUCache:
    def __init__(self, capacity: int, default_ttl_seconds: float = None):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self.default_ttl_seconds = default_ttl_seconds
        self._store = OrderedDict()  # key -> (value, expiry_monotonic)
        self._lock = RLock()

    def _expiry(self, ttl_seconds):
        ttl = self.default_ttl_seconds if ttl_seconds is None else ttl_seconds
        return None if ttl is None else time.monotonic() + ttl

    @staticmethod
    def _is_expired(expiry):
        return expiry is not None and time.monotonic() >= expiry

    def get(self, key):
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expiry = entry
            if self._is_expired(expiry):
                del self._store[key]
                return None
            self._store.move_to_end(key)
            return value

    def put(self, key, value, ttl_seconds=None):
        with self._lock:
            self._store[key] = (value, self._expiry(ttl_seconds))
            self._store.move_to_end(key)
            while len(self._store) > self.capacity:
                self._store.popitem(last=False)

    def evict_expired(self) -> int:
        with self._lock:
            expired = [k for k, (_, exp) in self._store.items() if self._is_expired(exp)]
            for k in expired:
                del self._store[k]
            return len(expired)

    def size(self) -> int:
        with self._lock:
            return len(self._store)
