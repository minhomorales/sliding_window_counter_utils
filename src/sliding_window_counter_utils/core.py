"""Core implementation of the sliding window counter."""

from __future__ import annotations

import time
from collections import deque
from typing import Callable, Deque, Optional


class SlidingWindowCounter:
    """Counts events within a rolling time window.

    Each call to ``observe`` appends a timestamped entry to a deque and evicts
    every entry whose timestamp falls outside ``window`` seconds of the clock's
    current value. The clock is injected so that tests can be deterministic;
    production code should pass ``time.monotonic`` (or ``time.time``) which both
    return ``float`` and are the default here.

    Eviction is O(expired) rather than O(total) on the happy path: we pop from the
    left while the oldest entry is out of range, and stop as soon as one survives.
    """

    def __init__(
        self,
        window: float,
        clock: Optional[Callable[[], float]] = None,
    ) -> None:
        if window <= 0:
            raise ValueError(f"window must be > 0, got {window!r}")
        if clock is None:
            clock = time.monotonic
        self._window = float(window)
        self._clock = clock
        self._entries: Deque[float] = deque()

    def observe(self) -> int:
        """Record an event at the clock's current time and return the new count.

        Eviction runs first, so an event observed at time ``t`` is counted in the
        same window it produces; this matches the intuition that "the counter
        shows how many events are in the window right now".
        """
        now = self._clock()
        self._evict(now)
        self._entries.append(now)
        return len(self._entries)

    def count(self) -> int:
        """Return the number of events currently within the window.

        Eviction runs before returning so the answer is always fresh with respect
        to the clock's current value.
        """
        now = self._clock()
        self._evict(now)
        return len(self._entries)

    def _evict(self, now: float) -> None:
        cutoff = now - self._window
        entries = self._entries
        while entries and entries[0] <= cutoff:
            entries.popleft()
