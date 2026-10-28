"""Tests for sliding_window_counter_utils.core."""

import unittest

from sliding_window_counter_utils import SlidingWindowCounter


class FakeClock:
    """Deterministic clock: returns a value that tests advance by hand."""

    def __init__(self, start: float = 0.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now


class TestConstruction(unittest.TestCase):
    def test_default_clock_is_set(self) -> None:
        c = SlidingWindowCounter(window=5.0)
        self.assertEqual(c.count(), 0)

    def test_non_positive_window_rejected(self) -> None:
        for bad in (0.0, -1.0):
            with self.assertRaises(ValueError):
                SlidingWindowCounter(window=bad)


class TestObserveAndCount(unittest.TestCase):
    def test_single_event_within_window(self) -> None:
        clock = FakeClock(10.0)
        c = SlidingWindowCounter(window=5.0, clock=clock)
        self.assertEqual(c.observe(), 1)
        self.assertEqual(c.count(), 1)

    def test_multiple_events_no_eviction(self) -> None:
        clock = FakeClock(0.0)
        c = SlidingWindowCounter(window=10.0, clock=clock)
        self.assertEqual(c.observe(), 1)
        clock.now = 1.0
        self.assertEqual(c.observe(), 2)
        clock.now = 2.0
        self.assertEqual(c.observe(), 3)
        clock.now = 3.0
        self.assertEqual(c.count(), 3)

    def test_event_exactly_at_cutoff_is_evicted(self) -> None:
        clock = FakeClock(0.0)
        c = SlidingWindowCounter(window=5.0, clock=clock)
        c.observe()
        clock.now = 5.0
        # An event at t=0 with window=5 is out of range at t=5 (cutoff=0).
        self.assertEqual(c.count(), 0)

    def test_event_just_inside_cutoff_is_kept(self) -> None:
        clock = FakeClock(0.0)
        c = SlidingWindowCounter(window=5.0, clock=clock)
        c.observe()
        clock.now = 4.999
        self.assertEqual(c.count(), 1)

    def test_old_events_evicted_new_kept(self) -> None:
        clock = FakeClock(0.0)
        c = SlidingWindowCounter(window=5.0, clock=clock)
        c.observe()  # t=0
        clock.now = 1.0
        c.observe()  # t=1
        clock.now = 2.0
        c.observe()  # t=2
        clock.now = 6.0  # t=0 and t=1 evicted; t=2 kept (cutoff=1)
        self.assertEqual(c.count(), 1)
        clock.now = 7.0  # cutoff=2; t=2 evicted
        self.assertEqual(c.count(), 0)

    def test_observe_runs_eviction_before_appending(self) -> None:
        clock = FakeClock(0.0)
        c = SlidingWindowCounter(window=5.0, clock=clock)
        c.observe()
        clock.now = 10.0
        # The old event is expired; the new one is the only entry.
        self.assertEqual(c.observe(), 1)

    def test_count_advances_with_clock_without_observe(self) -> None:
        clock = FakeClock(0.0)
        c = SlidingWindowCounter(window=5.0, clock=clock)
        c.observe()
        c.observe()
        clock.now = 4.0
        self.assertEqual(c.count(), 2)
        clock.now = 6.0
        self.assertEqual(c.count(), 0)

    def test_many_events_burst_then_drain(self) -> None:
        clock = FakeClock(0.0)
        c = SlidingWindowCounter(window=1.0, clock=clock)
        for _ in range(50):
            c.observe()
        self.assertEqual(c.count(), 50)
        clock.now = 2.0
        self.assertEqual(c.count(), 0)

    def test_interleaved_eviction_does_not_over_evict(self) -> None:
        clock = FakeClock(0.0)
        c = SlidingWindowCounter(window=10.0, clock=clock)
        for t in (0.0, 1.0, 2.0, 3.0):
            clock.now = t
            c.observe()
        clock.now = 3.5
        self.assertEqual(c.count(), 4)
        clock.now = 11.0  # t=0 and t=1 evicted; t=2 and t=3 within [2, 11]
        self.assertEqual(c.count(), 2)

    def test_empty_counter_count_is_zero(self) -> None:
        clock = FakeClock(100.0)
        c = SlidingWindowCounter(window=5.0, clock=clock)
        self.assertEqual(c.count(), 0)


if __name__ == "__main__":
    unittest.main()
