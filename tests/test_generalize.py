"""Generalization behaviour and the v1 bugs it has to avoid."""

import pytest

from urlgenie2 import generalize, generalize_many, generalize_url


@pytest.mark.parametrize(
    "url,expected",
    [
        ("cnn.com/sports?a=b#c", "https://cnn.com/sports"),
        ("http://cnn.com/sports/", "https://cnn.com/sports"),
        ("cnn.com", "https://cnn.com"),
        ("cnn.com/", "https://cnn.com"),
        ("cnn.com/a/b/../c", "https://cnn.com/a/c"),
    ],
)
def test_generalize_url_basics(url, expected):
    assert generalize_url(url) == expected


def test_flags_are_independent():
    url = "cnn.com/sports?a=b#c"
    assert generalize_url(url, keep_query=True) == "https://cnn.com/sports?a=b"
    assert generalize_url(url, keep_fragment=True) == "https://cnn.com/sports#c"
    assert generalize_url(url, keep_path=False) == "https://cnn.com"
    assert generalize_url(url, keep_query=True, keep_fragment=True) == "https://cnn.com/sports?a=b#c"


def test_generalize_many_forwards_every_flag():
    """v1 silently dropped keep_path and get_domain_with_tld in the comma path."""
    assert generalize_many("a.com/p, b.com/q", keep_path=False) == ["https://a.com", "https://b.com"]
    assert generalize_many("a.com/p?x=1", keep_query=True) == ["https://a.com/p?x=1"]


def test_generalize_many_accepts_iterables_and_drops_blanks():
    assert generalize_many(["a.com/p", "  ", None, "bad..."]) == ["https://a.com/p"]
    assert generalize_many("a.com/p,, , b.com/q") == ["https://a.com/p", "https://b.com/q"]


@pytest.mark.parametrize(
    "url",
    [
        #-v1 rejected every one of these-#
        "https://example.photography/x",
        "https://sub.example.museum/x",
        "https://verylongsubdomain.example.com/x",
        "http://example.com:8080/p",
        "example.com?a=b",
        "http://münchen.de/x",
        "http://192.168.1.1/admin",
    ],
)
def test_valid_urls_v1_wrongly_rejected(url):
    assert generalize(url) is not None


def test_invalid_input_returns_none_not_the_input():
    for bad in (None, 12345, "", "nonsense", "random.haz/x"):
        assert generalize(bad) is None


def test_social_off_falls_back_to_plain_generalization():
    assert generalize("fb.com/@ahmed", social=False) == "https://fb.com/@ahmed"
    assert generalize("fb.com/@ahmed") == "https://www.facebook.com/ahmed"


def test_userinfo_is_dropped_by_default():
    """https://evil.com@facebook.com/x must not look like it belongs to evil.com."""
    assert generalize_url("https://evil.com@facebook.com/x") == "https://facebook.com/x"
    assert generalize_url("https://u@example.com/x", keep_userinfo=True) == "https://u@example.com/x"


def test_generalization_is_idempotent():
    for url in ["cnn.com/sports?a=b#c", "fb.com/@ahmed", "x.com/elonmusk", "linkedin.com/in/ahmed-99"]:
        once = generalize(url)
        assert generalize(once) == once


def test_no_hidden_state_between_calls():
    """v1 mutated self.subdomains on every call and leaked bad_url on exceptions."""
    first = generalize("https://blog.facebook.com/somepage")
    for _ in range(5):
        generalize("https://news.facebook.com/other")
    assert generalize("https://blog.facebook.com/somepage") == first
