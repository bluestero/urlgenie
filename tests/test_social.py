"""Social rules beyond the reference sheet."""

import pytest

from urlgenie import detect_platform, extract_social_handle, generalize_social, is_social_url


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://www.facebook.com/zuck", "https://www.facebook.com/zuck"),
        ("m.facebook.com/zuck", "https://www.facebook.com/zuck"),
        ("mbasic.facebook.com/zuck?ref=bookmarks", "https://www.facebook.com/zuck"),
        ("https://fr-fr.facebook.com/zuck", "https://www.facebook.com/zuck"),
        ("FACEBOOK.COM/Zuck", "https://www.facebook.com/zuck"),
        ("facebook.com/groups/12345678", "https://www.facebook.com/12345678"),
        ("facebook.com/groups/pythondevs", "https://www.facebook.com/groups/pythondevs"),
    ],
)
def test_facebook(url, expected):
    assert generalize_social(url) == expected


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://x.com/elonmusk", "https://twitter.com/elonmusk"),
        ("mobile.twitter.com/elonmusk", "https://twitter.com/elonmusk"),
        ("twitter.com/elonmusk/status/123456789", "https://twitter.com/elonmusk"),
        ("https://twitter.com/#!/elonmusk", "https://twitter.com/elonmusk"),
    ],
)
def test_twitter(url, expected):
    assert generalize_social(url) == expected


@pytest.mark.parametrize(
    "url,expected",
    [
        ("linkedin.com/company/anthropic/about/", "https://www.linkedin.com/company/anthropic"),
        ("uk.linkedin.com/in/Some-Person-1a2b3c", "https://www.linkedin.com/in/some-person-1a2b3c"),
        ("linkedin.com/school/mit/", "https://www.linkedin.com/company/mit"),
    ],
)
def test_linkedin(url, expected):
    assert generalize_social(url) == expected


def test_linkedin_vanity_slugs_are_lowercased():
    found = extract_social_handle("https://www.linkedin.com.br/in/inahul-jOsHi-915b9a12a/")
    assert found.handle == "inahul-joshi-915b9a12a"


def test_linkedin_opaque_member_ids_keep_their_case():
    """ACwAA... ids are case sensitive -- lowercasing them breaks the link."""
    opaque = "ACwAAAxF1hwBy6_9YpmhkW1pUuOxHiYnko3qYjg"
    found = extract_social_handle(f"https://www.LinkedIn.com/in/{opaque}/")
    assert found.handle == opaque
    assert found.url == f"https://www.linkedin.com/in/{opaque}"


@pytest.mark.parametrize(
    "url,expected",
    [
        ("facebook.com/AhmedKhatib", "ahmedkhatib"),
        ("instagram.com/AhmedKhatib", "ahmedkhatib"),
        ("twitter.com/AhmedKhatib", "ahmedkhatib"),
        ("linkedin.com/company/Anthropic", "anthropic"),
    ],
)
def test_handles_are_lowercased(url, expected):
    assert extract_social_handle(url).handle == expected


@pytest.mark.parametrize(
    "url,expected",
    [
        ("youtube.com/@somechannel", "https://www.youtube.com/@somechannel"),
        ("youtube.com/c/somechannel", "https://www.youtube.com/somechannel"),
        ("youtube.com/channel/UCabcdefghijklmnop", "https://www.youtube.com/ucabcdefghijklmnop"),
        ("m.youtube.com/user/somechannel", "https://www.youtube.com/somechannel"),
    ],
)
def test_youtube(url, expected):
    assert generalize_social(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "twitter.com/intent",
        "twitter.com/home",
        "facebook.com/login",
        "facebook.com/profile.php",
        "facebook.com/",
        "instagram.com/p/",
        "instagram.com/explore",
        "youtube.com/watch?v=abc123",
        "linkedin.com/feed/",
    ],
)
def test_non_profile_social_urls_are_rejected(url):
    assert generalize_social(url) is None
    assert is_social_url(url) is False


def test_lookalike_domains_are_not_social():
    """Unescaped dots in v1 meant facebookXcom matched the facebook pattern."""
    assert detect_platform("http://facebookXcom.co/zuck") is None
    assert generalize_social("http://facebookXcom.co/zuck") is None
    assert generalize_social("http://notfacebook.com/zuck") is None


def test_non_social_urls_return_none():
    assert generalize_social("https://cnn.com/sports") is None
    assert extract_social_handle("https://cnn.com/sports") is None


def test_handle_reports_platform_and_rule():
    found = extract_social_handle("facebook.com/profile.php?id=123123123")
    assert (found.platform, found.handle, found.rule) == ("facebook", "123123123", "fb_query_id")


# --------------------------------------------------------------------------- #
# Parity with the v1 social_gens.py patterns
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "url,expected",
    [
        #-v1 facebook_gen id alternatives-#
        ("facebook.com/ajax/timeline?__user=123123123", "https://www.facebook.com/123123123"),
        ("facebook.com/#1/ahmedkhatib", "https://www.facebook.com/ahmedkhatib"),
        ("facebook.com/.../ahmedkhatib", "https://www.facebook.com/ahmedkhatib"),
        #-v1 youtube_gen fragment form-#
        ("youtube.com/#/somechannel", "https://www.youtube.com/somechannel"),
        ("youtube.de/c/somechannel", "https://www.youtube.com/somechannel"),
        #-v1 linkedin_gen profile/view?id=-#
        ("linkedin.com/profile/view?id=12345678", "https://www.linkedin.com/in/12345678"),
    ],
)
def test_v1_pattern_parity(url, expected):
    assert generalize_social(url) == expected


@pytest.mark.parametrize("url", ["facebook.com/...", "facebook.com/.../", "facebook.com/--"])
def test_punctuation_only_handles_are_rejected(url):
    """A handle with no alphanumeric character is a scrape artifact."""
    assert generalize_social(url) is None


@pytest.mark.parametrize(
    "url",
    [
        #-v1 allowed 20 chars and periods; Twitter's real limit is 15, no periods-#
        "twitter.com/abcdefghijklmnopqr",
        "twitter.com/some.handle.x",
    ],
)
def test_twitter_handle_rules_are_stricter_than_v1(url):
    assert generalize_social(url) is None


# --------------------------------------------------------------------------- #
# Facebook ignores periods in profile URLs
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "url",
    [
        "https://www.facebook.com/AhmedKhatib/",
        "https://www.facebook.com/ahmedkhatib",
        "https://www.facebook.com/ahmed.khatib",
        "https://www.facebook.com/..A..h.med..Kh...at....i.b.../",
        "facebook.com/@Ahmed.Khatib",
    ],
)
def test_facebook_periods_are_ignored(url):
    """All of these address the same Facebook profile, so all must canonicalize alike."""
    assert generalize_social(url) == "https://www.facebook.com/ahmedkhatib"


def test_facebook_period_stripping_does_not_leak_to_other_platforms():
    """Instagram periods are significant and must survive."""
    assert generalize_social("instagram.com/ahmed.khatib") == "https://www.instagram.com/ahmed.khatib"
    assert generalize_social("linkedin.com/in/ahmed.khatib") == "https://www.linkedin.com/in/ahmed.khatib"


@pytest.mark.parametrize("url", ["facebook.com/profile.php", "facebook.com/home.php", "facebook.com/l.php?u=x"])
def test_reserved_words_still_caught_after_period_stripping(url):
    """profile.php becomes profilephp once periods go; the reserved set must know both."""
    assert generalize_social(url) is None


# --------------------------------------------------------------------------- #
# SocialHandle.original_handle
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "url,handle,original",
    [
        #-Facebook: lowercased and period-stripped-#
        ("facebook.com/Ahmed.Khatib.90", "ahmedkhatib90", "Ahmed.Khatib.90"),
        #-Twitter and LinkedIn: lowercased only-#
        ("twitter.com/@ElonMusk", "elonmusk", "ElonMusk"),
        ("linkedin.com/in/inahul-jOsHi-915b9a12a", "inahul-joshi-915b9a12a", "inahul-jOsHi-915b9a12a"),
        #-Untouched when no normalization applies-#
        ("instagram.com/ahmed.khatib", "ahmed.khatib", "ahmed.khatib"),
        ("facebook.com/pages/Ahmed-Khatib/123123123", "123123123", "123123123"),
    ],
)
def test_original_handle_is_preserved(url, handle, original):
    found = extract_social_handle(url)
    assert (found.handle, found.original_handle) == (handle, original)


def test_original_handle_is_percent_decoded():
    """Decoding happens before the snapshot; case folding and stripping do not."""
    opaque = "ACwAAAxF1hwBy6_9YpmhkW1pUuOxHiYnko3qYjg"
    assert extract_social_handle(f"linkedin.com/in/{opaque}/").original_handle == opaque
    found = extract_social_handle("https://www.linkedin.com/in/marie-%D9%85%D8%A7-85600546/")
    assert "%" not in found.original_handle
