"""Thread-safe O(1) LRU cache with per-key TTL support.

Uses OrderedDict (hash map + doubly linked list) for O(1) get/put/evict,
and a single RLock for mutual exclusion across all mutating operations.
Expired entries are purged lazily on access and eagerly via evict_expired().
"""

import threading
import time
from collections import OrderedDict
from typing import Any, Optional


class LRUCache:
    def __init__(self, capacity: int, default_ttl_seconds: Optional[float] = None):
        if capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        self.capacity = capacity
        self.default_ttl_seconds = default_ttl_seconds
        # key -> (value, expires_at_monotonic_or_None); rightmost = most recently used
        self._data: OrderedDict[str, tuple] = OrderedDict()
        self._lock = threading.RLock()

    def _deadline(self, ttl_seconds: Optional[float]) -> Optional[float]:
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        return time.monotonic() + ttl if ttl is not None else None

    @staticmethod
    def _is_expired(expires_at: Optional[float], now: float) -> bool:
        return expires_at is not None and now >= expires_at

    def get(self, key: str) -> Any:
        """Return value for key, or None if missing/expired. Marks key as MRU. O(1)."""
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if self._is_expired(expires_at, time.monotonic()):
                del self._data[key]
                return None
            self._data.move_to_end(key)
            return value

    def put(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
        """Insert/update key. Evicts least recently used entries beyond capacity. O(1)."""
        with self._lock:
            self._data[key] = (value, self._deadline(ttl_seconds))
            self._data.move_to_end(key)
            while len(self._data) > self.capacity:
                self._data.popitem(last=False)

    def evict_expired(self) -> int:
        """Remove all expired entries. Returns count removed. O(N) — explicit maintenance call."""
        with self._lock:
            now = time.monotonic()
            expired = [k for k, (_, exp) in self._data.items() if self._is_expired(exp, now)]
            for k in expired:
                del self._data[k]
            return len(expired)

    def size(self) -> int:
        """Number of stored entries (may include not-yet-purged expired entries). O(1)."""
        with self._lock:
            return len(self._data)

    def __len__(self) -> int:
        return self.size()

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None
