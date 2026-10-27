"""In-memory key-value store with TTL and nested atomic transactions.

Design: O(1) undo journaling. Each transaction owns a journal mapping every
touched key to its *effective* pre-transaction state (expired entries are
recorded as absent, so rollback never resurrects a dead key). Nested commit
merges the child journal into the parent without overwriting entries the
parent already recorded.
"""

import time

_MISSING = object()


class TransactionError(Exception):
    """Raised when COMMIT/ROLLBACK is called outside a transaction."""


class KVStore:
    def __init__(self, clock=time.monotonic):
        self._clock = clock
        self._data = {}  # key -> (value, expires_at | None)
        self._tx = []  # journal stack: {key -> previous effective entry | _MISSING}

    def _entry(self, key):
        """Return the live entry for key, lazily reaping expired entries."""
        entry = self._data.get(key, _MISSING)
        if entry is not _MISSING and entry[1] is not None and self._clock() >= entry[1]:
            del self._data[key]
            return _MISSING
        return entry

    def _journal(self, key):
        if self._tx and key not in self._tx[-1]:
            self._tx[-1][key] = self._entry(key)

    def set(self, key, value, ttl=None):
        if ttl is not None and ttl < 0:
            raise ValueError("ttl must be >= 0")
        self._journal(key)
        self._data[key] = (value, None if ttl is None else self._clock() + ttl)

    def get(self, key, default=None):
        entry = self._entry(key)
        return default if entry is _MISSING else entry[0]

    def delete(self, key):
        existed = self._entry(key) is not _MISSING
        self._journal(key)
        self._data.pop(key, None)
        return existed

    def begin(self):
        self._tx.append({})

    def commit(self):
        if not self._tx:
            raise TransactionError("COMMIT without BEGIN")
        journal = self._tx.pop()
        if self._tx:
            parent = self._tx[-1]
            for key, old in journal.items():
                parent.setdefault(key, old)

    def rollback(self):
        if not self._tx:
            raise TransactionError("ROLLBACK without BEGIN")
        for key, old in self._tx.pop().items():
            if old is _MISSING:
                self._data.pop(key, None)
            else:
                self._data[key] = old

    @property
    def tx_depth(self):
        return len(self._tx)

    SET, GET, DELETE = set, get, delete
    BEGIN, COMMIT, ROLLBACK = begin, commit, rollback
