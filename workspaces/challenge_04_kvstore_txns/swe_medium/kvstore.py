"""In-memory key-value store with TTL and nested atomic transactions.

Design (Occam's razor): a stack of delta layers. The bottom layer is the
committed store; each BEGIN pushes a fresh delta dict. Writes go to the top
layer; reads scan the stack top-down. COMMIT merges the top delta into the
layer below; ROLLBACK pops it. No full-store snapshots — O(delta) memory.
"""

import time

_DELETED = object()  # tombstone marker for deletes inside a transaction


class KVStoreError(Exception):
    pass


class KVStore:
    def __init__(self, now=time.monotonic):
        self._now = now
        self._stack = [{}]  # key -> (value, expiry|None) or _DELETED

    # --- core operations -------------------------------------------------

    def set(self, key, value, ttl_seconds=None):
        expiry = self._now() + ttl_seconds if ttl_seconds is not None else None
        self._stack[-1][key] = (value, expiry)

    def get(self, key):
        for layer in reversed(self._stack):
            entry = layer.get(key)
            if entry is None:
                continue
            if entry is _DELETED:
                return None
            value, expiry = entry
            if expiry is not None and self._now() >= expiry:
                return None  # lazily expired
            return value
        return None

    def delete(self, key):
        existed = self.get(key) is not None
        self._stack[-1][key] = _DELETED
        return existed

    # --- transactions ----------------------------------------------------

    def begin(self):
        self._stack.append({})

    def commit(self):
        if len(self._stack) < 2:
            raise KVStoreError("COMMIT without BEGIN")
        delta = self._stack.pop()
        self._stack[-1].update(delta)

    def rollback(self):
        if len(self._stack) < 2:
            raise KVStoreError("ROLLBACK without BEGIN")
        self._stack.pop()

    @property
    def transaction_depth(self):
        return len(self._stack) - 1
