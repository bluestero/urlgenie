"""All patterns and lookup tables live here, one entry at a time.

Every social pattern is a separate, named :class:`~urlgenie2.types.Rule`.
Rules are tried in order and the first one that yields a non-reserved handle
wins, so adding support for a new URL shape means appending one line -- no
existing pattern has to be touched or re-tested.
"""

from __future__ import annotations

import re
from typing import Dict, Optional, Tuple

from .types import Platform, Rule

__all__ = ["PLATFORMS", "PLATFORM_BY_DOMAIN", "EMAIL_PATTERN", "PHONE_PATTERN", "SOCIAL_CANDIDATE_PATTERN"]

_I = re.IGNORECASE


def _reserved(words: str) -> frozenset:
    """Build a reserved-word set that also holds each word without its periods.

    Handles may be period-stripped before the reserved check runs, so
    "profile.php" has to be recognized as "profilephp" too.
    """
    entries = set(words.split())
    return frozenset(entries | {entry.replace(".", "") for entry in entries})


# --------------------------------------------------------------------------- #
# Facebook
# --------------------------------------------------------------------------- #

FACEBOOK_RULES: Tuple[Rule, ...] = (
    #-profile.php?id=, group.php?gid=, pages/edit/?id=, ?ref=name&id=, ?__user=-#
    Rule("fb_query_id", re.compile(r"[?&](?:id|gid|__user)=(?P<id>\d{5,})", _I)),
    #-media/set/?set=a.<album>.<size>.<owner id>-#
    Rule("fb_media_set", re.compile(r"[?&]set=a\.(?:\d+\.)*(?P<id>\d{5,})", _I)),
    #-groups/<name>/user/<id>-#
    Rule("fb_user_id", re.compile(r"/user/(?P<id>\d{5,})", _I)),
    #-pages/<slug>/<id>-#
    Rule("fb_pages_id", re.compile(r"/pages/(?:[^/?#]+/)+?(?P<id>\d{5,})(?:[/?#]|$)", _I)),
    #-Ahmed-Khatib-123123123 and pages/category/photographer/<slug>-<id>-#
    Rule("fb_slug_id", re.compile(r"-(?P<id>\d{5,})(?:[/?#]|$)", _I)),
    #-pg/<id>, events/<id>, bare /<id>-#
    Rule("fb_numeric_path", re.compile(r"/(?P<id>\d{5,})(?:[/?#]|$)", _I)),
    #-Legacy AJAX fragments: #!/handle and home.php#/handle-#
    Rule("fb_fragment_handle", re.compile(r"#[!1]?/@?(?P<handle>[a-z0-9%.\-]{1,50})(?:[/?#]|$)", _I)),
    #-pg/, watch/, people/, .../ (scrape truncation), pages/category/<job>/-#
    Rule(
        "fb_prefixed_handle",
        re.compile(
            r"/(?:pg|watch|people|\.\.\.|pages/category/[a-z]+)/@?(?P<handle>[a-z0-9%.\-]{1,50})(?:[/?#]|$)", _I
        ),
    ),
    Rule("fb_group_handle", re.compile(r"/groups/(?P<handle>[a-z0-9%.\-]{1,50})(?:[/?#]|$)", _I), subdir="groups"),
    Rule("fb_handle", re.compile(r"^/+@?(?P<handle>[a-z0-9%.\-]{1,50})(?:[/?#]|$)", _I)),
)

FACEBOOK_RESERVED = _reserved(
    """
    profile.php home.php story.php permalink.php sharer.php l.php pages groups people pg watch events media
    dialog help search sharer login public notes video photo photos plugins ajax hashtag marketplace gaming
    settings privacy terms policies about careers directory bookmarks messages notifications recover
    """
)


# --------------------------------------------------------------------------- #
# LinkedIn
# --------------------------------------------------------------------------- #

def _pub_to_in(match: "re.Match") -> Optional[Tuple[str, str]]:
    """Convert the legacy ``/pub/<name>/<a>/<b>/<c>`` form into ``/in/<slug>``.

    LinkedIn built the modern slug by reversing the three id fragments and
    zero-padding the last two to three characters:
    ``pub/mark-adams/28/1b8/a`` -> ``in/mark-adams-00a1b828``.
    """
    name, a, b, c = match.group("name"), match.group("a"), match.group("b"), match.group("c")
    return "in", f"{name}-{c.rjust(3, '0')}{b.rjust(3, '0')}{a}"


LINKEDIN_RULES: Tuple[Rule, ...] = (
    #-groupInvitation?gID=, ?gid=, ?groupId=-#
    Rule("li_group_query", re.compile(r"[?&]g(?:id|roupid)=(?P<id>\d{2,})", _I), subdir="groups"),
    #-edu/school?id=<id>-#
    Rule("li_edu_query", re.compile(r"/(?:edu/)?school\?id=(?P<id>\d{2,})", _I), subdir="edu"),
    #-Numeric ids embedded in a slug: groups/Wholesaler-magazine-4806067-#
    Rule(
        "li_numeric_slug",
        re.compile(
            r"/(?P<subdir>grps|groups|edu|company-beta|organization|showcase|companies|company|school)"
            r"/(?:[^/?#]*?-)?(?P<id>\d{2,})(?:[/?#]|$)",
            _I,
        ),
    ),
    #-Legacy public profile form-#
    Rule(
        "li_pub",
        re.compile(
            r"/pub/(?P<name>[^/?#]{2,150})/(?P<a>[a-z0-9]{1,3})/(?P<b>[a-z0-9]{1,3})/(?P<c>[a-z0-9]{1,3})(?:[/?#]|$)",
            _I,
        ),
        transform=_pub_to_in,
    ),
    #-in/, company/, showcase/, school/, organization-guest/company/, profile/view?id=-#
    Rule(
        "li_handle",
        re.compile(
            r"/(?:organization-guest/)?(?P<subdir>in|companies|company|showcase|school|organization|profile|edu)"
            r"/(?:view\?id=)?(?P<handle>[^/?#]{2,200})(?:[/?#]|$)",
            _I,
        ),
    ),
)

LINKEDIN_SUBDIR_ALIASES: Dict[str, str] = {
    "grps": "groups",
    "companies": "company",
    "company-beta": "company",
    "organization": "company",
    "showcase": "company",
    "school": "company",
    "profile": "in",
}

#-Opaque LinkedIn member ids (ACwAA..., ACoAA..., ...) are case sensitive:
# lowercasing them breaks the link, unlike ordinary vanity slugs.-#
LINKEDIN_OPAQUE_ID_PATTERN = re.compile(r"A[A-Za-z]{2}AA[A-Za-z0-9_-]{28,40}")

LINKEDIN_RESERVED = _reserved(
    """
    company-beta organization-guest www.linkedin.com feed shareArticle sharing uas login signup help legal
    """
)


# --------------------------------------------------------------------------- #
# Twitter / X
# --------------------------------------------------------------------------- #

TWITTER_RULES: Tuple[Rule, ...] = (
    #-intent/follow?screen_name=<handle> and widget urls-#
    Rule("tw_screen_name", re.compile(r"[?&]screen_name=@?(?P<handle>[a-z0-9_]{1,15})", _I)),
    #-Legacy hashbang form Twitter used around 2010: twitter.com/#!/handle-#
    Rule("tw_fragment_handle", re.compile(r"#!?/@?(?P<handle>[a-z0-9_]{1,15})(?:[/?#]|$)", _I)),
    Rule("tw_handle", re.compile(r"^/+@?(?P<handle>[a-z0-9_]{1,15})(?:[/?#]|$)", _I)),
)

TWITTER_RESERVED = _reserved(
    """
    i home share intent search explore hashtag notifications messages settings login signup privacy tos
    about download compose status statuses account help oauth widgets
    """
)


# --------------------------------------------------------------------------- #
# Instagram
# --------------------------------------------------------------------------- #

INSTAGRAM_RULES: Tuple[Rule, ...] = (
    #-accounts/login/?next=/<handle>/-#
    Rule("ig_login_next", re.compile(r"[?&]next=/(?P<handle>[a-z0-9_.]{1,30})", _I)),
    Rule("ig_handle", re.compile(r"^/+(?P<handle>[a-z0-9_.]{1,30})(?:[/?#]|$)", _I)),
)

INSTAGRAM_RESERVED = _reserved(
    """
    p reel reels tv stories explore accounts direct about developer legal privacy emails web challenge
    """
)


# --------------------------------------------------------------------------- #
# YouTube
# --------------------------------------------------------------------------- #

YOUTUBE_RULES: Tuple[Rule, ...] = (
    Rule("yt_channel", re.compile(r"^/+(?:c|channel|user)/(?P<handle>[a-z0-9_.\-]{1,64})(?:[/?#]|$)", _I)),
    #-Legacy fragment form: youtube.com/#/channel-#
    Rule("yt_fragment_handle", re.compile(r"#/(?:c/|channel/|user/)?@?(?P<handle>[a-z0-9_.\-]{3,30})(?:[/?#]|$)", _I)),
    Rule("yt_at_handle", re.compile(r"^/+(?P<handle>@[a-z0-9_.\-]{2,30})(?:[/?#]|$)", _I)),
    Rule("yt_plain", re.compile(r"^/+(?P<handle>[a-z0-9_.\-]{3,30})(?:[/?#]|$)", _I)),
)

YOUTUBE_RESERVED = _reserved(
    """
    watch playlist feed results embed shorts about account premium gaming music movies live t redirect
    """
)


# --------------------------------------------------------------------------- #
# Platform registry
# --------------------------------------------------------------------------- #

PLATFORMS: Tuple[Platform, ...] = (
    Platform(
        name="facebook",
        domains=frozenset({"facebook", "fb"}),
        canonical_host="facebook.com",
        canonical_subdomain="www",
        rules=FACEBOOK_RULES,
        reserved=FACEBOOK_RESERVED,
        strip_periods=True,
        max_handle_length=50,
    ),
    Platform(
        name="linkedin",
        domains=frozenset({"linkedin"}),
        canonical_host="linkedin.com",
        canonical_subdomain="www",
        rules=LINKEDIN_RULES,
        reserved=LINKEDIN_RESERVED,
        subdir_aliases=LINKEDIN_SUBDIR_ALIASES,
        preserve_case_pattern=LINKEDIN_OPAQUE_ID_PATTERN,
        max_handle_length=100,
    ),
    Platform(
        name="twitter",
        domains=frozenset({"twitter", "x"}),
        canonical_host="twitter.com",
        canonical_subdomain="",
        rules=TWITTER_RULES,
        reserved=TWITTER_RESERVED,
        max_handle_length=15,
    ),
    Platform(
        name="instagram",
        domains=frozenset({"instagram"}),
        canonical_host="instagram.com",
        canonical_subdomain="www",
        rules=INSTAGRAM_RULES,
        reserved=INSTAGRAM_RESERVED,
        max_handle_length=30,
    ),
    Platform(
        name="youtube",
        domains=frozenset({"youtube"}),
        canonical_host="youtube.com",
        canonical_subdomain="www",
        rules=YOUTUBE_RULES,
        reserved=YOUTUBE_RESERVED,
        max_handle_length=64,
    ),
)

PLATFORM_BY_DOMAIN: Dict[str, Platform] = {
    domain: platform for platform in PLATFORMS for domain in platform.domains
}


# --------------------------------------------------------------------------- #
# Contact extraction patterns
# --------------------------------------------------------------------------- #

#-Local part per RFC 5322 atext, kept practical; image extensions excluded-#
EMAIL_PATTERN = re.compile(
    r"(?<![a-z0-9._%+\-])"
    r"[a-z0-9!#$%&'*+/=?^_`{|}~\-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~\-]+)*"
    r"@"
    r"(?:[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?\.)+"
    r"(?!png|jpg|jpeg|gif|bmp|webp|svg|ico|tiff|css|js|html?)[a-z]{2,63}"
    r"(?![a-z0-9\-])",
    _I,
)

#-Deliberately permissive; validate_phone() does the real filtering-#
PHONE_PATTERN = re.compile(
    r"(?<![\d\-./])"
    r"(?:\+\d{1,3}[\s.\-]?)?"
    r"(?:\(\d{1,4}\)[\s.\-]?)?"
    r"\d{2,4}(?:[\s.\-]?\d{2,5}){1,4}"
    r"(?![\d\-/])"
)

#-Finds social-looking URLs in free text; each hit is then run through
# generalize_social(), so extraction never duplicates the handle patterns.-#
SOCIAL_CANDIDATE_PATTERN = re.compile(
    r"(?<![a-z0-9.\-@])"
    r"(?:https?://)?"
    r"(?:[a-z0-9\-]+\.)*"
    r"(?:facebook|fb|instagram|linkedin|twitter|x|youtube)"
    r"\.[a-z]{2,}(?:\.[a-z]{2,})?"
    r"/[^\s\"'<>()\[\],]*",
    _I,
)

#-Extensions that show up in scraped markup and are never real TLDs-#
EMAIL_BAD_TLDS = frozenset({"png", "jpg", "jpeg", "gif", "bmp", "webp", "svg", "ico", "tiff", "css", "js", "html", "htm"})
