import pytest

from ratelimit import TokenBucket


class FakeClock:
    def __init__(self, t=100.0):
        self.t = t

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


def test_starts_full_and_drains():
    clock = FakeClock()
    bucket = TokenBucket(3, 1.0, clock=clock)
    assert bucket.available() == 3
    assert [bucket.try_acquire() for _ in range(4)] == [True, True, True, False]


def test_refills_continuously_and_caps():
    clock = FakeClock()
    bucket = TokenBucket(4, 2.0, clock=clock)
    assert bucket.try_acquire(4)
    clock.advance(0.5)
    assert bucket.available() == pytest.approx(1.0)
    clock.advance(0.25)
    assert bucket.available() == pytest.approx(1.5)
    clock.advance(100)
    assert bucket.available() == pytest.approx(4.0)


def test_failed_acquire_takes_nothing():
    clock = FakeClock()
    bucket = TokenBucket(5, 1.0, clock=clock)
    assert bucket.try_acquire(4)
    assert not bucket.try_acquire(2)
    assert bucket.available() == pytest.approx(1.0)
    clock.advance(1.0)
    assert bucket.try_acquire(2)
    assert bucket.available() == pytest.approx(0.0)


def test_zero_refill_rate():
    clock = FakeClock()
    bucket = TokenBucket(2, 0, clock=clock)
    assert bucket.try_acquire(2)
    clock.advance(1000)
    assert not bucket.try_acquire()


@pytest.mark.parametrize("capacity, rate", [(0, 1.0), (-1, 1.0), (2, -0.5)])
def test_invalid_construction(capacity, rate):
    with pytest.raises(ValueError):
        TokenBucket(capacity, rate, clock=FakeClock())


@pytest.mark.parametrize("n", [0, -1, 6])
def test_invalid_acquire_amount(n):
    bucket = TokenBucket(5, 1.0, clock=FakeClock())
    with pytest.raises(ValueError):
        bucket.try_acquire(n)


def test_reads_clock_lazily():
    calls = []

    def clock():
        calls.append(1)
        return 0.0

    bucket = TokenBucket(1, 1.0, clock=clock)
    before = len(calls)
    bucket.available()
    assert len(calls) == before + 1
