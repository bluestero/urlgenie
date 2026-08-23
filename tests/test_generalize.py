"""Generalization behaviour and the v1 bugs it has to avoid."""

import pytest

from urlgenie import generalize, generalize_many, generalize_url


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
    assert generalize_many("a.com/p, b.com/q", keep_path=False) == [
        ("a.com/p", "https://a.com"),
        ("b.com/q", "https://b.com"),
    ]
    assert generalize_many("a.com/p?x=1", keep_query=True) == [("a.com/p?x=1", "https://a.com/p?x=1")]


def test_generalize_many_accepts_iterables_and_skips_blanks():
    """Blank entries are dropped before generalizing; they were never real input rows."""
    assert generalize_many(["a.com/p", "  ", None, "bad..."]) == [
        ("a.com/p", "https://a.com/p"),
        ("bad...", None),
    ]
    assert generalize_many("a.com/p,, , b.com/q") == [
        ("a.com/p", "https://a.com/p"),
        ("b.com/q", "https://b.com/q"),
    ]


def test_generalize_many_keeps_invalid_entries_aligned_with_their_input():
    """A bad URL must not shift every later result out of position -- report it, don't drop it."""
    result = generalize_many("facebook.com,facebook/com,dummy.com,instagram.com/ahmed")
    assert result == [
        ("facebook.com", "https://facebook.com"),
        ("facebook/com", None),
        ("dummy.com", "https://dummy.com"),
        ("instagram.com/ahmed", "https://www.instagram.com/ahmed"),
    ]


def test_generalize_many_drop_invalid_omits_bad_entries_but_keeps_pair_shape():
    """drop_invalid changes what's included, never the shape of what's returned."""
    result = generalize_many("facebook.com,facebook/com,dummy.com,instagram.com/ahmed", drop_invalid=True)
    assert result == [
        ("facebook.com", "https://facebook.com"),
        ("dummy.com", "https://dummy.com"),
        ("instagram.com/ahmed", "https://www.instagram.com/ahmed"),
    ]
    assert all(generalized is not None for _, generalized in result)


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
