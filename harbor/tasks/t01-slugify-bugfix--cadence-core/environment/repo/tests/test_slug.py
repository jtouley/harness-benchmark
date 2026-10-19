from textkit import slugify


def test_simple_phrase():
    assert slugify("Hello World") == "hello-world"
