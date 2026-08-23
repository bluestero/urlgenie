"""Social profile detection, generalization and handle extraction."""

from __future__ import annotations

from typing import Optional, Tuple
from urllib.parse import unquote

from .config import PLATFORM_BY_DOMAIN
from .types import ParsedUrl, Platform, SocialHandle
from .uri import parse_url

__all__ = [
    "detect_platform",
    "generalize_social",
    "extract_social_handle",
    "is_social_url",
]


def detect_platform(url) -> Optional[Platform]:
    """Return the :class:`Platform` a URL belongs to, or ``None``."""
    parsed = url if isinstance(url, ParsedUrl) else parse_url(url)
    if parsed is None:
        return None
    return PLATFORM_BY_DOMAIN.get(parsed.domain.lower())


def _keeps_case(platform: Platform, handle: str) -> bool:
    """True if this particular handle must not be lowercased."""
    pattern = platform.preserve_case_pattern
    return pattern is not None and pattern.fullmatch(handle) is not None


def _is_reserved(platform: Platform, handle: str) -> bool:
    lowered = handle.lower()
    #-Compare with and without periods so "profile.php" and "profilephp" both hit-#
    return lowered in platform.reserved or lowered.replace(".", "") in platform.reserved


def _apply_rules(platform: Platform, probe: str) -> Optional[Tuple[str, str, str, str]]:
    """Run the rules in order, returning ``(subdir, handle, original_handle, rule_name)``.

    A rule that matches but produces a reserved or over-long handle is skipped
    rather than accepted, so a later, more specific rule still gets its turn.
    """
    for rule in platform.rules:
        match = rule.pattern.search(probe)
        if not match:
            continue

        if rule.transform is not None:
            transformed = rule.transform(match)
            if transformed is None:
                continue
            subdir, handle = transformed
        else:
            groups = match.groupdict()
            handle = groups.get("id") or groups.get("handle")
            if not handle:
                continue
            subdir = rule.subdir or groups.get("subdir") or ""

        handle = unquote(handle).strip("/")
        #-"...", "--" and similar scrape artifacts are not handles-#
        if not handle or not any(char.isalnum() for char in handle):
            continue

        #-Keep the handle as it appeared before any normalization-#
        original_handle = handle

        if platform.lowercase_handle and not _keeps_case(platform, handle):
            handle = handle.lower()
        if platform.strip_periods:
            handle = handle.replace(".", "")
        if not handle:
            continue
        if len(handle) > platform.max_handle_length:
            continue
        if _is_reserved(platform, handle):
            continue

        if subdir:
            subdir = subdir.lower()
            subdir = platform.subdir_aliases.get(subdir, subdir)

        return subdir, handle, original_handle, rule.name

    return None


def extract_social_handle(url) -> Optional[SocialHandle]:
    """Identify the social profile a URL points at.

    Returns ``None`` for non-social URLs and for social URLs that do not
    address a profile (``twitter.com/intent``, ``facebook.com/login``, ...).
    """
    parsed = url if isinstance(url, ParsedUrl) else parse_url(url)
    if parsed is None:
        return None

    platform = PLATFORM_BY_DOMAIN.get(parsed.domain.lower())
    if platform is None:
        return None

    resolved = _apply_rules(platform, parsed.probe())
    if resolved is None:
        return None

    subdir, handle, original_handle, rule_name = resolved
    return SocialHandle(
        platform=platform.name,
        handle=handle,
        url=platform.build_url(subdir, handle),
        original_handle=original_handle,
        rule=rule_name,
    )


def generalize_social(url) -> Optional[str]:
    """Canonical profile URL for a social link, or ``None`` if there is none.

    Country hosts, locale subdomains, tracking queries and legacy path shapes
    all collapse to one form: ``facebook.com.br/@x`` -> ``https://www.facebook.com/x``.
    """
    found = extract_social_handle(url)
    return found.url if found else None


def is_social_url(url) -> bool:
    """True if the URL is a recognized profile on a known platform."""
    return extract_social_handle(url) is not None
