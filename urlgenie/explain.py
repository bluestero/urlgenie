"""Human-readable explanations for every URL Genie verdict.

A thin wrapper around the public API. It never changes a verdict -- it calls
the real validator for the answer, then works out *why* that answer came back
and returns it alongside a plain-English sentence.

    from explain import explain_url

    r = explain_url("https://acme.zzz")
    r.ok        -> False
    r.code      -> "url.no_suffix"
    r.message   -> '".zzz" is not a real public suffix, so nothing on the open internet can live here.'
    r.detail    -> "host: acme.zzz"
    bool(r)     -> False        # drop-in for the plain validators

Messages live in MESSAGES, keyed by a stable code, so you can translate them
or swap the wording without touching any logic.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Optional

import urlgenie as ug
from urlgenie.social import detect_platform, extract_social_handle
from urlgenie.uri import normalize_host, parse_url
from urlgenie.validate import normalize_phone

__all__ = [
    "Explained",
    "MESSAGES",
    "explain_url",
    "explain_email",
    "explain_phone",
    "explain_social",
    "explain_social_platform",
    "explain_social_profile",
    "explain_generalize",
]


@dataclass(frozen=True)
class Explained:
    """A verdict plus the reason for it."""

    ok: bool
    code: str
    message: str
    detail: str = ""

    def __bool__(self) -> bool:
        return self.ok

    def as_dict(self) -> dict:
        return asdict(self)


MESSAGES = {
    #-validate_url-#
    "url.unparseable": "That is not a URL -- no host could be read out of it.",
    "url.bad_scheme": "Only http and https are accepted here; {scheme} is something else.",
    "url.no_suffix": '".{tld}" is not a real public suffix. The parser rejects the host outright, so the require_suffix flag never gets a say.',
    "url.no_dot": 'Host "{host}" has no domain part at all -- it only resolves on your own machine, and the parser rejects it before require_suffix is consulted.',
    "url.ip_no_suffix": "A bare IP address has no public suffix, so require_suffix=True rejects it. Switch that off and it passes -- IPs are the only suffix-less host the parser keeps.",
    "url.ip_ok": "A bare IP address. No public suffix, but you turned that requirement off, so it stands.",
    "url.valid": 'Well-formed, and ".{suffix}" is a real public suffix.',
    #-validate_email-#
    "email.malformed": "Not an email address -- it needs exactly one @ and a valid domain after it.",
    "email.bad_tld": "The part after @ is a filename extension, not a mail domain.",
    "email.off_domain": "Valid address, but it does not belong to {site} -- most likely someone else's email on the page.",
    "email.on_domain": "Valid, and it belongs to {site} -- safe to treat as that business's address.",
    "email.valid": "Syntax is good and the domain looks like a real mail domain.",
    #-validate_phone-#
    "phone.not_numeric": "There are letters in here. Real phone numbers only carry digits and the punctuation they are formatted with.",
    "phone.too_short": "Only {digits} digits -- too short to be a phone number anywhere.",
    "phone.too_long": "{digits} digits exceeds the longest possible number (E.164 caps at 15) -- this is an id, not a phone.",
    "phone.repeated": "Every digit is the same. That is a placeholder, not a number.",
    "phone.looks_like_id": "An unbroken run of {digits} digits with no formatting -- a timestamp or an order id wearing a phone number's clothes.",
    "phone.valid": "Plausible length and no id pattern -- worth dialling.",
    #-validate_social-#
    "social.unparseable": "Not even a URL, let alone a social profile.",
    "social.unknown_platform": "Perfectly good URL, but {host} is not a network URL Genie knows.",
    "social.not_a_profile": "Recognised as {platform}, but the path is not a handle -- system routes, share dialogs and search pages all land here.",
    "social.valid": "A real {platform} profile: @{handle}.",
    #-validate_social_platform-#
    "platform.yes": "This URL is on {platform}. Note that this says nothing about whether it is a profile.",
    "platform.no": "{host} is not {platform}.",
    "platform.unparseable": "Nothing parseable here.",
    #-validate_social_profile-#
    "profile.yes": "On {platform} and it resolves to an actual profile: @{handle}.",
    "profile.wrong_platform": "Not on {platform} at all, so it cannot be a {platform} profile.",
    "profile.not_a_profile": "Recognised as {platform}, but not a profile -- no handle in that path.",
    #-generalize-#
    "generalize.invalid": "Nothing to generalize -- that string has no usable host.",
    "generalize.social": "Recognised as a {platform} profile, so it canonicalizes to the profile URL rather than the plain one.",
    "generalize.ok": "Canonical form.",
}


def _say(code: str, **fields) -> str:
    return MESSAGES[code].format(**fields)


def _mk(ok: bool, code: str, detail: str = "", **fields) -> Explained:
    return Explained(ok=ok, code=code, message=_say(code, **fields), detail=detail)


_SCHEME_SPLIT = re.compile(r"^[a-z][a-z0-9+.\-]*://", re.IGNORECASE)


def _host_of(url) -> Optional[str]:
    """The normalized host, ignoring the public-suffix requirement.

    parse_url() returns None both for "no host at all" and for "host whose TLD
    is not in the public suffix list". Telling those apart is the whole job of
    a good error message, so this repeats just enough of the authority split to
    recover the host either way.
    """
    if not isinstance(url, str):
        return None
    text = url.strip()
    if not text:
        return None

    if text.startswith("//"):
        text = text[2:]
    elif _SCHEME_SPLIT.match(text):
        text = text.split("://", 1)[1]

    authority = re.split(r"[/?#]", text, 1)[0]
    if "@" in authority:
        authority = authority.rpartition("@")[2]
    if authority.startswith("["):
        end = authority.find("]")
        authority = authority[: end + 1] if end != -1 else authority
    elif ":" in authority:
        authority = authority.partition(":")[0]

    return normalize_host(authority)


def explain_url(url, *, require_suffix: bool = True) -> Explained:
    """Why validate_url() said what it said.

    Worth knowing: require_suffix only ever changes the answer for IP-address
    hosts. Any other host without a public suffix is rejected by parse_url
    before validate_url can consult the flag.
    """
    parsed = parse_url(url)

    if parsed is None:
        host = _host_of(url)
        if host is None:
            return _mk(False, "url.unparseable")
        if "." not in host:
            return _mk(False, "url.no_dot", detail=f"host: {host}", host=host)
        return _mk(False, "url.no_suffix", detail=f"host: {host}", tld=host.rsplit(".", 1)[-1])

    if parsed.scheme not in ("http", "https"):
        return _mk(False, "url.bad_scheme", detail=f"scheme: {parsed.scheme}", scheme=parsed.scheme)

    ok = ug.validate_url(url, require_suffix=require_suffix)
    where = f"{parsed.scheme} · {parsed.host} · {parsed.path or '/'}"

    if not parsed.suffix:
        return _mk(ok, "url.ip_ok" if ok else "url.ip_no_suffix", detail=where)
    return _mk(ok, "url.valid", detail=where, suffix=parsed.suffix)


def explain_email(email, *, url=None) -> Explained:
    """Why validate_email() said what it said."""
    if not ug.validate_email(email):
        domain = email.rsplit("@", 1)[-1] if isinstance(email, str) and "@" in email else ""
        tld = domain.rsplit(".", 1)[-1].lower() if "." in domain else ""
        if tld and not ug.validate_email(f"probe@{domain}"):
            return _mk(False, "email.bad_tld", detail=f"domain: {domain}")
        return _mk(False, "email.malformed")

    if url:
        site = parse_url(url)
        site_domain = site.registrable_domain if site else url
        if ug.email_domain_matches(email, url):
            return _mk(True, "email.on_domain", detail=f"{email.rsplit('@', 1)[-1]} = {site_domain}", site=site_domain)
        return _mk(False, "email.off_domain", detail=f"{email.rsplit('@', 1)[-1]} ≠ {site_domain}", site=site_domain)

    return _mk(True, "email.valid", detail=f"domain: {email.rsplit('@', 1)[-1]}")


def explain_phone(phone) -> Explained:
    """Why validate_phone() said what it said.

    Note the ordering: the letters check runs first, because a string like
    "asdasd1312312321" contains a plausible digit count and would otherwise
    look valid to anything that only counts digits.
    """
    raw = phone if isinstance(phone, str) else ""
    normalized = normalize_phone(phone)
    digits = "".join(ch for ch in raw if ch.isdigit())

    if normalized is not None:
        return _mk(True, "phone.valid", detail=f"normalized: {normalized}")

    if any(ch.isalpha() for ch in raw):
        return _mk(False, "phone.not_numeric", detail=f"digits found: {len(digits)}")
    if len(digits) < 7:
        return _mk(False, "phone.too_short", digits=len(digits))
    if len(digits) > 15:
        return _mk(False, "phone.too_long", digits=len(digits))
    if len(set(digits)) <= 1:
        return _mk(False, "phone.repeated")
    return _mk(False, "phone.looks_like_id", digits=len(digits))


def explain_social(url) -> Explained:
    """Why validate_social() said what it said."""
    parsed = parse_url(url)
    if parsed is None:
        return _mk(False, "social.unparseable")

    platform = detect_platform(url)
    if platform is None:
        return _mk(False, "social.unknown_platform", detail=f"host: {parsed.host}", host=parsed.host)

    handle = extract_social_handle(url)
    if handle is None:
        return _mk(False, "social.not_a_profile", detail=f"{platform.name} · reserved or empty path", platform=platform.name)
    return _mk(True, "social.valid", detail=f"{platform.name} · {handle.url}", platform=platform.name, handle=handle.handle)


def explain_social_platform(url, platform: str) -> Explained:
    """Why validate_social_platform() said what it said."""
    parsed = parse_url(url)
    if parsed is None:
        return _mk(False, "platform.unparseable")

    ok = ug.validate_social_platform(url, platform)
    detected = detect_platform(url)
    name = detected.name if detected else parsed.host
    if ok:
        return _mk(True, "platform.yes", detail=f"host: {parsed.host}", platform=name)
    return _mk(False, "platform.no", detail=f"detected: {name}", host=parsed.host, platform=platform)


def explain_social_profile(url, platform: str) -> Explained:
    """Why validate_social_profile() said what it said."""
    if not ug.validate_social_platform(url, platform):
        return _mk(False, "profile.wrong_platform", detail=explain_social_platform(url, platform).detail, platform=platform)

    handle = extract_social_handle(url)
    if handle is None:
        return _mk(False, "profile.not_a_profile", detail=f"{platform} · no handle in path", platform=platform)
    return _mk(True, "profile.yes", detail=handle.url, platform=handle.platform, handle=handle.handle)


def explain_generalize(url) -> Explained:
    """Why generalize() produced what it produced."""
    result = ug.generalize(url)
    if result is None:
        return _mk(False, "generalize.invalid")

    handle = extract_social_handle(url)
    if handle is not None:
        return _mk(True, "generalize.social", detail=result, platform=handle.platform)
    return _mk(True, "generalize.ok", detail=result)
