"""Immutable result types shared across urlgenie."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, ClassVar, Dict, FrozenSet, Optional, Pattern, Set, Tuple

__all__ = [
    "ParsedUrl",
    "SocialHandle",
    "ExtractResult",
    "Rule",
    "Platform",
]


@dataclass(frozen=True)
class ParsedUrl:
    """An RFC 3986 URI split into normalized components.

    Components are stored in normalized form: lowercased scheme and host,
    percent-encoding normalized per RFC 3986 section 6.2.2.2, dot segments
    removed per section 5.2.4, and default ports dropped.
    """

    scheme: str
    userinfo: str
    host: str
    port: Optional[int]
    path: str
    query: str
    fragment: str
    subdomain: str
    domain: str
    suffix: str

    @property
    def registrable_domain(self) -> str:
        """The domain plus its public suffix, e.g. ``facebook.com``."""
        return f"{self.domain}.{self.suffix}" if self.suffix else self.domain

    @property
    def authority(self) -> str:
        authority = self.host
        if self.userinfo:
            authority = f"{self.userinfo}@{authority}"
        if self.port is not None:
            authority = f"{authority}:{self.port}"
        return authority

    def geturl(self, keep_path: bool = True, keep_query: bool = True, keep_fragment: bool = True) -> str:
        """Reassemble the URI per RFC 3986 section 5.3."""
        url = f"{self.scheme}://{self.authority}"
        if keep_path:
            url += self.path
        if keep_query and self.query:
            url += f"?{self.query}"
        if keep_fragment and self.fragment:
            url += f"#{self.fragment}"
        return url

    def probe(self) -> str:
        """Path + query + fragment, the string social rules are matched against."""
        probe = self.path or "/"
        if self.query:
            probe += f"?{self.query}"
        if self.fragment:
            probe += f"#{self.fragment}"
        return probe


@dataclass(frozen=True)
class SocialHandle:
    """A social profile identified on a known platform.

    ``handle`` is the canonical form -- percent-decoded, and case-folded and
    period-stripped according to the platform's rules. ``original_handle`` is
    the same value as it appeared in the URL, decoded but otherwise untouched,
    which is what you want for display or for debugging a rule::

        extract_social_handle("facebook.com/Ahmed.Khatib.90")
        # handle='ahmedkhatib90', original_handle='Ahmed.Khatib.90'
    """

    platform: str
    handle: str
    url: str
    original_handle: str = ""
    rule: str = ""


@dataclass
class ExtractResult:
    """Contacts and social profiles found in a block of text."""

    emails: Set[str] = field(default_factory=set)
    phones: Set[str] = field(default_factory=set)
    facebook: Set[str] = field(default_factory=set)
    twitter: Set[str] = field(default_factory=set)
    instagram: Set[str] = field(default_factory=set)
    linkedin: Set[str] = field(default_factory=set)
    youtube: Set[str] = field(default_factory=set)

    FIELDS: ClassVar[Tuple[str, ...]] = (
        "emails", "phones", "facebook", "twitter", "instagram", "linkedin", "youtube",
    )

    def as_dict(self) -> Dict[str, Set[str]]:
        return {name: getattr(self, name) for name in self.FIELDS}

    def is_empty(self) -> bool:
        return not any(getattr(self, name) for name in self.FIELDS)


@dataclass(frozen=True)
class Rule:
    """One named, independently testable social URL pattern.

    Each rule is deliberately small. Add or remove a rule without touching
    any other pattern -- that is the whole point of splitting them up.

    The pattern should expose either an ``id`` or a ``handle`` named group.
    An optional ``subdir`` group (or the ``subdir`` attribute) selects the
    canonical path prefix, e.g. ``in`` or ``company`` for LinkedIn.
    """

    name: str
    pattern: Pattern[str]
    subdir: str = ""
    transform: Optional[Callable[[re.Match], Optional[Tuple[str, str]]]] = None


@dataclass(frozen=True)
class Platform:
    """Canonical form and match rules for one social network."""

    name: str
    domains: FrozenSet[str]
    canonical_host: str
    canonical_subdomain: str
    rules: Tuple[Rule, ...]
    reserved: FrozenSet[str] = frozenset()
    subdir_aliases: Dict[str, str] = field(default_factory=dict)
    lowercase_handle: bool = True
    #-Facebook ignores periods in profile URLs: ahmed.khatib.90, ahmedkhatib90 and
    # ..a..h.med..90 all resolve to the same profile, so they must canonicalize alike.-#
    strip_periods: bool = False
    #-Handles matching this stay case sensitive even when lowercase_handle is set,
    # e.g. LinkedIn's opaque ACwAA... member ids.-#
    preserve_case_pattern: Optional[Pattern[str]] = None
    max_handle_length: int = 100

    def build_url(self, subdir: str, handle: str) -> str:
        host = self.canonical_host
        if self.canonical_subdomain:
            host = f"{self.canonical_subdomain}.{host}"
        path = f"{subdir}/{handle}" if subdir else handle
        return f"https://{host}/{path}"
