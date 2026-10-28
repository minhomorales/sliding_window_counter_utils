"""sliding_window_counter_utils: counts events within a rolling time window.

A deque of timestamped entries is evicted from the left on every observation,
so the window always reflects events whose timestamp is still within `window`
seconds of the clock's current value.
"""

from .core import SlidingWindowCounter

__all__ = ["SlidingWindowCounter"]
