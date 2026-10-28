# sliding_window_counter_utils

Counts events within a rolling time window using a deque of timestamped entries, evicting expired entries on each observation.

## Usage

```python
from sliding_window_counter_utils import SlidingWindowCounter

# Use the default clock (time.monotonic) in production.
counter = SlidingWindowCounter(window=5.0)
counter.observe()  # -> 1
counter.observe()  # -> 2
counter.count()    # -> 2 (still within the window)
```

For deterministic tests, inject a clock callable:

```python
class FakeClock:
    def __init__(self, start=0.0):
        self.now = start
    def __call__(self):
        return self.now

clk = FakeClock(0.0)
c = SlidingWindowCounter(window=5.0, clock=clk)
c.observe()         # t=0
clk.now = 4.999
c.count()           # -> 1 (just inside)
clk.now = 5.0
c.count()           # -> 0 (exactly at cutoff, evicted)
```

## Exported names

- `SlidingWindowCounter(window: float, clock: Callable[[], float] | None = None)`
  - `observe() -> int` — record an event at the clock's current time, evict expired entries, return the new count.
  - `count() -> int` — evict expired entries and return how many remain in the window.

## Why this exists

Rate limiting and "events in the last N seconds" dashboards need a window that actually rolls. A fixed counter resets on a boundary and hides bursts that straddle it; a rolling counter gives an honest picture at the cost of storing one timestamp per event. This library picks the deque approach because eviction from the left is cheap, the code is small enough to audit in one read, and the storage cost is acceptable when the number of events per window is bounded by the workload itself.

## Edge you will hit

The eviction boundary is **exclusive at the cutoff**: an event whose timestamp equals `now - window` is treated as expired. With `window=5.0`, an event observed at `t=0` is gone at `t=5.0`, not `t=5.0001`. If you need inclusive behavior at the boundary, widen the window by an epsilon in your own code — the library will not guess which side of the fence you want.
