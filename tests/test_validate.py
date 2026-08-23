"""URL, email, phone and social validators."""

import pytest

from urlgenie2 import (
    email_domain_matches,
    normalize_phone,
    validate_email,
    validate_phone,
    validate_social,
    validate_url,
)


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com",
        "example.com/path",
        "http://example.com:8080/p",
        "https://example.photography",
        "https://münchen.de/x",
        "https://a.b.c.d.example.co.uk/x",
    ],
)
def test_valid_urls(url):
    assert validate_url(url) is True


@pytest.mark.parametrize(
    "url",
    [None, 123, "", "nonsense", "random.haz", "http://", "ftp://example.com/x"],
)
def test_invalid_urls(url):
    assert validate_url(url) is False


def test_scheme_allowlist_is_configurable():
    assert validate_url("ftp://example.com/x", allowed_schemes=("ftp",)) is True


@pytest.mark.parametrize(
    "email",
    ["a@b.com", "first.last@example.co.uk", "user+tag@example.com", "x_y@sub.example.com"],
)
def test_valid_emails(email):
    assert validate_email(email) is True


@pytest.mark.parametrize(
    "email",
    [
        None,
        "",
        "not-an-email",
        "a@b",
        "a@@b.com",
        ".leading@example.com",
        "trailing.@example.com",
        "double..dot@example.com",
        #-The classic scrape false positive-#
        "sample@image.png",
        "logo@sprite.jpg",
        "a" * 65 + "@example.com",
    ],
)
def test_invalid_emails(email):
    assert validate_email(email) is False


def test_email_domain_matching():
    assert email_domain_matches("info@example.com", "https://www.example.com/contact") is True
    #-Subdomains still belong to the same organization-#
    assert email_domain_matches("info@mail.example.com", "https://example.com") is True
    assert email_domain_matches("someone@gmail.com", "https://www.example.com") is False


def test_validate_email_with_url():
    assert validate_email("info@example.com", url="https://example.com") is True
    assert validate_email("someone@gmail.com", url="https://example.com") is False


@pytest.mark.parametrize(
    "phone,expected",
    [
        ("+1 (415) 555-2671", "+14155552671"),
        ("+91 98765 43210", "+919876543210"),
        ("020 7946 0958", "02079460958"),
        ("555-2671", "5552671"),
    ],
)
def test_normalize_phone(phone, expected):
    assert normalize_phone(phone) == expected


@pytest.mark.parametrize(
    "phone",
    [
        None,
        "",
        "123",
        "1234567890123456789",
        "0000000000",
        "1111111111",
        #-Timestamps and ids that a loose pattern would otherwise accept-#
        "170123456789012",
    ],
)
def test_invalid_phones(phone):
    assert validate_phone(phone) is False


def test_validate_social():
    assert validate_social("fb.com/@ahmed") is True
    assert validate_social("twitter.com/intent") is False
    assert validate_social("https://cnn.com") is False
