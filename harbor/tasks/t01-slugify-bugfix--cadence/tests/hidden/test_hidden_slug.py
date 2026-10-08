import pytest

from textkit import slugify


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Hello World", "hello-world"),
        ("Hello,  World!!", "hello-world"),
        ("  --Leading and trailing--  ", "leading-and-trailing"),
        ("Crème brûlée", "creme-brulee"),
        ("a b", "a-b"),
        ("!!!", ""),
        ("Version 2.0 Release", "version-2-0-release"),
    ],
)
def test_words_joined_by_single_hyphen(text, expected):
    assert slugify(text) == expected


@pytest.mark.parametrize(
    "text, max_length, expected",
    [
        ("alpha beta gamma", 12, "alpha-beta"),
        ("alpha beta gamma", 10, "alpha-beta"),
        ("alpha beta gamma", 16, "alpha-beta-gamma"),
        ("supercalifragilistic", 5, "super"),
        ("one two", 3, "one"),
    ],
)
def test_truncates_at_word_boundary(text, max_length, expected):
    assert slugify(text, max_length=max_length) == expected


def test_never_ends_with_hyphen():
    for n in range(1, 30):
        out = slugify("the quick brown fox jumps over", max_length=n)
        assert not out.endswith("-") and len(out) <= n
