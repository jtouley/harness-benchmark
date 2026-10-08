def test_importable():
    from ratelimit import TokenBucket

    assert callable(TokenBucket)
