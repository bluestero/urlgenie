"""Validators for URLs, emails, phone numbers and social profiles."""

from __future__ import annotations

import re
from typing import Iterable, Optional

from .config import EMAIL_BAD_TLDS, EMAIL_PATTERN, PLATFORM_BY_DOMAIN, PLATFORMS
from .social import detect_platform, extract_social_handle, is_social_url
from .types import ParsedUrl
from .uri import parse_url

__all__ = [
    "validate_url",
    "validate_email",
    "validate_phone",
    "validate_social",
    "validate_social_platform",
    "validate_social_profile",
    "normalize_phone",
    "email_domain_matches",
]

#-RFC 5321 section 4.5.3.1 size limits-#
_MAX_LOCAL_PART = 64
_MAX_EMAIL = 254

#-E.164 allows at most 15 digits; 7 is the shortest plausible national number-#
_MIN_PHONE_DIGITS = 7
_MAX_PHONE_DIGITS = 15

_NON_DIGIT_RE = re.compile(r"\D")

#-Digits plus the punctuation real phone numbers are formatted with. \D alone
# strips letters too, which let "asdasd1312312321" normalize as a real number
# just because it happened to contain 10 digits -- this rejects it outright
# before any digit-counting logic runs.-#
_PHONE_ALLOWED_CHARS_RE = re.compile(r"^[\d\s+().\-]+$")


def validate_url(
    url,
    *,
    allowed_schemes: Iterable[str] = ("http", "https"),
    require_suffix: bool = True,
) -> bool:
    """True if ``url`` is a syntactically valid, resolvable-looking URL.

    ``require_suffix`` rejects hosts whose TLD is not in the public suffix
    list, which is what filters out typos like ``random.haz``.
    """
    parsed = url if isinstance(url, ParsedUrl) else parse_url(url)
    if parsed is None:
        return False
    if allowed_schemes and parsed.scheme not in allowed_schemes:
        return False
    if require_suffix and not parsed.suffix:
        return False
    return True


def validate_email(email, *, url=None) -> bool:
    """True if ``email`` is syntactically valid.

    When ``url`` is given, the email must also sit on that site's registrable
    domain -- the usual way to drop ``someone@gmail.com`` from a scrape of a
    company website.
    """
    if not isinstance(email, str):
        return False

    email = email.strip()
    if not email or len(email) > _MAX_EMAIL or email.count("@") != 1:
        return False

    local, _, domain = email.partition("@")
    if not local or len(local) > _MAX_LOCAL_PART:
        return False
    if local.startswith(".") or local.endswith(".") or ".." in local:
        return False

    if domain.rsplit(".", 1)[-1].lower() in EMAIL_BAD_TLDS:
        return False

    #-Reuse the extraction pattern so extract and validate can never disagree-#
    match = EMAIL_PATTERN.fullmatch(email)
    if not match:
        return False

    if url is not None and not email_domain_matches(email, url):
        return False

    return True


def email_domain_matches(email: str, url) -> bool:
    """True if the email's domain is the registrable domain of ``url``.

    Subdomains count as a match, so ``info@mail.example.com`` belongs to
    ``https://www.example.com``.
    """
    parsed = url if isinstance(url, ParsedUrl) else parse_url(url)
    if parsed is None or not isinstance(email, str) or "@" not in email:
        return False

    site = parsed.registrable_domain.lower()
    if not site:
        return False

    email_host = parse_url(f"https://{email.rsplit('@', 1)[-1].strip().lower()}/")
    if email_host is None:
        return False

    return email_host.registrable_domain.lower() == site


def normalize_phone(phone) -> Optional[str]:
    """Return a compact ``+<digits>`` / ``<digits>`` form, or ``None`` if implausible.

    This is deliberately pragmatic rather than a full E.164 implementation:
    it enforces the digit-count limits and rejects the obvious false positives
    that turn up in scraped text (dates, ids, repeated digits).
    """
    if not isinstance(phone, str):
        return None

    phone = phone.strip()
    if not phone or not _PHONE_ALLOWED_CHARS_RE.match(phone):
        return None

    international = phone.lstrip().startswith("+")
    digits = _NON_DIGIT_RE.sub("", phone)

    if not (_MIN_PHONE_DIGITS <= len(digits) <= _MAX_PHONE_DIGITS):
        return None
    #-"1111111111" and friends are ids or placeholders, not phone numbers-#
    if len(set(digits)) <= 1:
        return None
    #-A run of separator-free digits that looks like a timestamp or id-#
    if not international and digits == phone and len(digits) > 11:
        return None

    return f"+{digits}" if international else digits


def validate_phone(phone) -> bool:
    """True if ``phone`` looks like a real phone number."""
    return normalize_phone(phone) is not None


def validate_social(url) -> bool:
    """True if ``url`` is a recognized social profile, on any platform."""
    return is_social_url(url)


def _resolve_platform(platform: str) -> str:
    """Resolve a platform name or alias (``"fb"``, ``"x"``) to its canonical name.

    Raises ``ValueError`` if ``platform`` isn't one urlgenie recognizes. This is
    a caller bug, not bad user input -- the URL being validated is untrusted,
    but the platform name is a literal the caller wrote themselves, so a typo
    should fail immediately rather than silently validating against nothing.
    """
    entry = PLATFORM_BY_DOMAIN.get(platform.lower()) if isinstance(platform, str) else None
    if entry is None:
        valid = sorted({p.name for p in PLATFORMS})
        raise ValueError(f"Unknown platform {platform!r}; expected one of {valid} (or an alias like 'fb', 'x')")
    return entry.name


def validate_social_platform(url, platform: str) -> bool:
    """True if ``url``'s domain belongs to ``platform``.

    This does not check whether the path resolves to an actual profile --
    ``facebook.com/profile.php`` belongs to Facebook but is not itself a
    profile URL. See :func:`validate_social_profile` for that check.

        validate_social_platform("facebook.com/profile.php", "facebook")  # True
        validate_social_platform("twitter.com/elonmusk", "facebook")      # False
    """
    canonical = _resolve_platform(platform)
    detected = detect_platform(url)
    return detected is not None and detected.name == canonical


def validate_social_profile(url, platform: str) -> bool:
    """True if ``url`` resolves to an actual profile/handle on ``platform``.

        validate_social_profile("facebook.com/profile.php", "facebook")             # False -- reserved, no id
        validate_social_profile("facebook.com/profile.php?id=123123123", "facebook") # True
    """
    canonical = _resolve_platform(platform)
    handle = extract_social_handle(url)
    return handle is not None and handle.platform == canonical
