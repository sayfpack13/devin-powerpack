"""Thread-safe sliding window rate limiter with bounded memory.

Design (Occam's razor):
- One ``collections.deque`` per client holding ``time.monotonic()`` timestamps.
- Expired timestamps are purged lazily from the left of the deque on every
  call, so per-client storage never exceeds ``max_requests`` entries.
- Clients whose windows have fully expired are evicted from the registry,
  bounding total memory to O(active_clients * max_requests).
- A single ``threading.Lock`` serializes all registry/deque mutations.
"""

import threading
import time
from collections import deque


class RateLimiter:
    """Allow at most ``max_requests`` per ``client_id`` per sliding window."""

    __slots__ = ("_max_requests", "_window_seconds", "_lock", "_clients")

    def __init__(self, max_requests: int, window_seconds: float):
        if max_requests <= 0:
            raise ValueError("max_requests must be positive")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._lock = threading.Lock()
        self._clients: dict[str, deque] = {}

    def _purge_expired(self, timestamps: deque, now: float) -> None:
        cutoff = now - self._window_seconds
        while timestamps and timestamps[0] <= cutoff:
            timestamps.popleft()

    def allow_request(self, client_id: str) -> bool:
        """Record a request; return True iff within the window's allowance."""
        now = time.monotonic()
        with self._lock:
            timestamps = self._clients.get(client_id)
            if timestamps is None:
                timestamps = self._clients[client_id] = deque()
            self._purge_expired(timestamps, now)
            if len(timestamps) >= self._max_requests:
                return False
            timestamps.append(now)
            return True

    def get_remaining_allowance(self, client_id: str) -> int:
        """Requests still available to ``client_id`` in the current window."""
        now = time.monotonic()
        with self._lock:
            timestamps = self._clients.get(client_id)
            if timestamps is None:
                return self._max_requests
            self._purge_expired(timestamps, now)
            if not timestamps:
                del self._clients[client_id]
                return self._max_requests
            return self._max_requests - len(timestamps)

    def reset(self, client_id: str) -> None:
        """Clear all recorded requests for ``client_id``."""
        with self._lock:
            self._clients.pop(client_id, None)
