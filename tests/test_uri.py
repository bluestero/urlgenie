"""RFC 3986 conformance."""

import pytest

from urlgenie2 import normalize_component, normalize_host, parse_url, remove_dot_segments


@pytest.mark.parametrize(
    "path,expected",
    [
        #-The two worked examples from RFC 3986 section 5.2.4-#
        ("/a/b/c/./../../g", "/a/g"),
        ("mid/content=5/../6", "mid/6"),
        ("/./a", "/a"),
        ("/../a", "/a"),
        ("/a/..", "/"),
        ("/a/b/..", "/a/"),
        ("", ""),
    ],
)
def test_remove_dot_segments(path, expected):
    assert remove_dot_segments(path) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        #-Section 6.2.2.2: decode octets that stand for unreserved characters-#
        ("%7Egood", "~good"),
        ("%7egood", "~good"),
        ("%41%42", "AB"),
        #-Reserved octets stay encoded but get uppercase hex-#
        ("a%2fb", "a%2Fb"),
        ("a%3Fb", "a%3Fb"),
        #-Non-ASCII is encoded as UTF-8 octets-#
        ("münchen", "m%C3%BCnchen"),
    ],
)
def test_normalize_component(value, expected):
    assert normalize_component(value, "") == expected


def test_percent_normalization_is_idempotent():
    """quote(unquote(x)) is not idempotent; this must be."""
    once = normalize_component("%2520", "")
    assert once == "%2520"
    assert normalize_component(once, "") == once


def test_literal_percent_is_preserved():
    assert normalize_component("100%25", "") == "100%25"


@pytest.mark.parametrize(
    "host,expected",
    [
        ("EXAMPLE.COM", "example.com"),
        ("example.com.", "example.com"),
        ("münchen.de", "xn--mnchen-3ya.de"),
        ("192.168.1.1", "192.168.1.1"),
        ("[::1]", "[::1]"),
        ("999.1.1.1", None),
    ],
)
def test_normalize_host(host, expected):
    assert normalize_host(host) == expected


def test_scheme_and_host_are_lowercased():
    parsed = parse_url("HTTP://WWW.EXAMPLE.COM/Path")
    assert parsed.scheme == "http"
    assert parsed.host == "www.example.com"
    #-Section 6.2.2.1: the path is case sensitive and must not be touched-#
    assert parsed.path == "/Path"


@pytest.mark.parametrize(
    "url,port",
    [
        ("https://example.com:443/x", None),
        ("http://example.com:80/x", None),
        ("https://example.com:8080/x", 8080),
        ("https://example.com/x", None),
    ],
)
def test_default_ports_are_dropped(url, port):
    assert parse_url(url).port == port


def test_userinfo_is_parsed_not_confused_with_host():
    parsed = parse_url("https://evil.com@facebook.com/victim")
    assert parsed.host == "facebook.com"
    assert parsed.userinfo == "evil.com"


@pytest.mark.parametrize(
    "url",
    ["example.com", "//example.com/x", "example.com:8080/p", "example.com?a=b", "https://[::1]/x"],
)
def test_scheme_relative_and_scheme_less_inputs_parse(url):
    assert parse_url(url) is not None


def test_port_is_not_mistaken_for_a_scheme():
    parsed = parse_url("example.com:8080/p")
    assert (parsed.scheme, parsed.host, parsed.port) == ("https", "example.com", 8080)


@pytest.mark.parametrize("url", [None, 123, "", "   ", "not a url", "random.haz/x", "javascript:alert(1)"])
def test_invalid_inputs_return_none(url):
    assert parse_url(url) is None


def test_control_characters_are_stripped():
    assert parse_url("https://exa\nmple.com/x").host == "example.com"
