"""Thread-safe sliding window rate limiter with bounded memory.

Uses per-client deques of timestamps; expired entries are purged lazily
on each access, so memory per client is bounded by max_requests.
"""

import threading
import time
from collections import deque


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: float):
        if max_requests <= 0:
            raise ValueError("max_requests must be positive")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._hits: dict[str, deque] = {}
        self._now = time.monotonic

    def _purge(self, dq: deque, now: float) -> None:
        cutoff = now - self.window_seconds
        while dq and dq[0] <= cutoff:
            dq.popleft()

    def allow_request(self, client_id: str) -> bool:
        now = self._now()
        with self._lock:
            dq = self._hits.setdefault(client_id, deque())
            self._purge(dq, now)
            if len(dq) >= self.max_requests:
                return False
            dq.append(now)
            return True

    def get_remaining_allowance(self, client_id: str) -> int:
        now = self._now()
        with self._lock:
            dq = self._hits.get(client_id)
            if dq is None:
                return self.max_requests
            self._purge(dq, now)
            return self.max_requests - len(dq)

    def reset(self, client_id: str) -> None:
        with self._lock:
            self._hits.pop(client_id, None)

    def tracked_clients(self) -> int:
        with self._lock:
            return len(self._hits)
