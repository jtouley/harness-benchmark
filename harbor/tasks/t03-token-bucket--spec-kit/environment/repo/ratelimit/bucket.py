import time


class TokenBucket:
    """Token-bucket rate limiter. See the issue for the required behavior."""

    def __init__(self, capacity, refill_rate, clock=time.monotonic):
        raise NotImplementedError

    def try_acquire(self, n=1):
        raise NotImplementedError

    def available(self):
        raise NotImplementedError
