Use the cadence skill to ship this change end to end through R7.

Issue (ticket gh-1):
Implement `ratelimit.TokenBucket`; the class is currently a stub.

`TokenBucket(capacity, refill_rate, clock=time.monotonic)`

- `capacity`: maximum tokens, an int > 0. `refill_rate`: tokens added per second, a number >= 0.
  Anything else raises `ValueError`.
- `clock` is a zero-argument callable returning seconds as a float. It is read once in
  `__init__` and again on every call to `try_acquire` / `available`. Tests inject a fake clock.
- The bucket starts full.
- Tokens refill continuously: after `dt` seconds, `refill_rate * dt` tokens are added, never
  exceeding `capacity`. Partial tokens accumulate.
- `try_acquire(n=1) -> bool`: if at least `n` tokens are available, remove `n` and return `True`;
  otherwise remove nothing and return `False`. `n` must be an int with `1 <= n <= capacity`,
  otherwise raise `ValueError`.
- `available() -> float`: the current number of tokens after refilling.

Standard library only.
