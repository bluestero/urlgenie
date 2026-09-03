"""RFC 3986 compliant URI parsing and normalization.

Section references in this module point at RFC 3986:
https://datatracker.ietf.org/doc/html/rfc3986
"""

from __future__ import annotations

import re
import string
from typing import Optional, Tuple

from .psl import SuffixParts, suffix_parts
from .types import ParsedUrl

__all__ = ["parse_url", "remove_dot_segments", "normalize_component", "normalize_host"]

#-RFC 3986 Appendix B: the reference URI parsing regex-#
_URI_RE = re.compile(
    r"^(?:(?P<scheme>[^:/?#]+):)?"
    r"(?://(?P<authority>[^/?#]*))?"
    r"(?P<path>[^?#]*)"
    r"(?:\?(?P<query>[^#]*))?"
    r"(?:#(?P<fragment>.*))?$"
)

#-RFC 3986 section 3.1: scheme = ALPHA *( ALPHA / DIGIT / "+" / "-" / "." )-#
_SCHEME_RE = re.compile(r"^[a-z][a-z0-9+.\-]*://", re.IGNORECASE)

#-RFC 3986 section 2.3: unreserved characters are never percent-encoded-#
_UNRESERVED = frozenset(string.ascii_letters + string.digits + "-._~")

#-RFC 3986 section 2.2: sub-delims, safe to leave literal inside a component-#
_SUB_DELIMS = "!$&'()*+,;="
_PATH_SAFE = _SUB_DELIMS + ":@/"
_QUERY_SAFE = _PATH_SAFE + "/?"

_PCT_RE = re.compile(r"%([0-9A-Fa-f]{2})")
_HEX = frozenset(string.hexdigits)

#-Characters RFC 3986 section 2.4 requires stripped before parsing-#
_JUNK_RE = re.compile(r"[\x00-\x20\x7f]")

_DEFAULT_PORTS = {"http": 80, "https": 443, "ftp": 21, "ws": 80, "wss": 443}

_IPV4_RE = re.compile(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$")
_REG_NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9._~%!$&'()*+,;=\-]*[a-z0-9])?$", re.IGNORECASE)


def remove_dot_segments(path: str) -> str:
    """RFC 3986 section 5.2.4 -- resolve ``.`` and ``..`` segments."""
    output: list = []
    while path:
        if path.startswith("../"):
            path = path[3:]
        elif path.startswith("./"):
            path = path[2:]
        elif path.startswith("/./"):
            path = "/" + path[3:]
        elif path == "/.":
            path = "/"
        elif path.startswith("/../"):
            path = "/" + path[4:]
            if output:
                output.pop()
        elif path == "/..":
            path = "/"
            if output:
                output.pop()
        elif path in (".", ".."):
            path = ""
        else:
            #-Move the next segment (leading slash plus everything up to the next one)-#
            end = path.find("/", 1)
            end = len(path) if end == -1 else end
            output.append(path[:end])
            path = path[end:]
    return "".join(output)


def normalize_component(value: str, safe: str) -> str:
    """Normalize percent-encoding per RFC 3986 sections 2.1 and 6.2.2.2.

    Decodes octets that represent unreserved characters, uppercases the hex
    digits of every octet that must stay encoded, and percent-encodes any
    character that is not allowed to appear literally in the component.

    Unlike ``quote(unquote(value))`` this is idempotent: it never decodes an
    already-decoded ``%25`` into a bare ``%``.
    """
    out: list = []
    i, length = 0, len(value)
    while i < length:
        char = value[i]
        if char == "%" and i + 2 < length + 1 and value[i + 1 : i + 3] and all(c in _HEX for c in value[i + 1 : i + 3]):
            octet = int(value[i + 1 : i + 3], 16)
            decoded = chr(octet)
            #-Only ASCII unreserved octets may be decoded; everything else stays encoded-#
            out.append(decoded if decoded in _UNRESERVED else f"%{octet:02X}")
            i += 3
            continue
        if char in _UNRESERVED or char in safe:
            out.append(char)
        else:
            out.extend(f"%{byte:02X}" for byte in char.encode("utf-8"))
        i += 1
    return "".join(out)


def normalize_host(host: str) -> Optional[str]:
    """RFC 3986 section 3.2.2 -- lowercase the host and punycode non-ASCII labels."""
    if not host:
        return None

    #-IPv6 / IPvFuture literals keep their brackets and are only lowercased-#
    if host.startswith("[") and host.endswith("]"):
        return host.lower()

    host = host.rstrip(".").lower()
    if not host:
        return None

    match = _IPV4_RE.match(host)
    if match:
        return host if all(int(part) < 256 for part in match.groups()) else None

    if host.isascii():
        return host if _REG_NAME_RE.match(host) else None

    #-Internationalized host: encode each label with IDNA, per RFC 3986 section 3.2.2-#
    labels = []
    for label in host.split("."):
        try:
            labels.append(label.encode("idna").decode("ascii"))
        except UnicodeError:
            return None
    return ".".join(labels)


def _split_authority(authority: str) -> Tuple[str, str, Optional[str]]:
    """RFC 3986 section 3.2 -- authority = [ userinfo "@" ] host [ ":" port ]."""
    userinfo = ""
    if "@" in authority:
        userinfo, _, authority = authority.rpartition("@")

    port = None
    if authority.startswith("["):
        #-IPv6 literal: the port colon can only follow the closing bracket-#
        end = authority.find("]")
        if end != -1 and authority[end + 1 :].startswith(":"):
            authority, port = authority[: end + 1], authority[end + 2 :]
    elif ":" in authority:
        authority, _, port = authority.partition(":")

    return userinfo, authority, port


def parse_url(url: str, *, default_scheme: str = "https") -> Optional[ParsedUrl]:
    """Parse and normalize ``url``, returning ``None`` if it is not a usable URL.

    A scheme-relative or scheme-less input such as ``facebook.com/x`` is given
    ``default_scheme``. Only hierarchical (``scheme://``) URLs are accepted;
    ``mailto:`` and friends are rejected because they have no authority.
    """
    if not isinstance(url, str):
        return None

    url = _JUNK_RE.sub("", url).strip()
    if not url:
        return None

    if url.startswith("//"):
        url = f"{default_scheme}:{url}"
    elif not _SCHEME_RE.match(url):
        #-Bare host such as "example.com:8080/p": the colon is a port, not a scheme-#
        url = f"{default_scheme}://{url}"

    match = _URI_RE.match(url)
    if not match:
        return None

    scheme = (match.group("scheme") or default_scheme).lower()
    authority = match.group("authority")
    if authority is None:
        return None

    userinfo, raw_host, raw_port = _split_authority(authority)
    host = normalize_host(raw_host)
    if not host:
        return None

    port: Optional[int] = None
    if raw_port not in (None, ""):
        if not raw_port.isdigit():
            return None
        port = int(raw_port)
        #-RFC 3986 section 3.2.3: an empty or default port is equivalent to none-#
        if _DEFAULT_PORTS.get(scheme) == port:
            port = None

    path = match.group("path") or ""
    if path and not path.startswith("/"):
        path = f"/{path}"
    path = remove_dot_segments(path)
    path = normalize_component(path, _PATH_SAFE)

    query = normalize_component(match.group("query") or "", _QUERY_SAFE)
    fragment = normalize_component(match.group("fragment") or "", _QUERY_SAFE)

    is_ip_or_literal = _IPV4_RE.match(host) or host.startswith("[")
    if is_ip_or_literal:
        #-An IP/IPvFuture literal has no labels to split -- the whole thing is the "domain"-#
        parts = SuffixParts(subdomain="", domain=host, suffix="")
    else:
        parts = suffix_parts(host)
        #-Reject hosts with no public suffix (typos like "random.haz") and hosts that
        # *are* a public suffix with nothing registered under it (e.g. bare "ck",
        # itself a PSL entry) -- neither is a registrable domain-#
        if not parts.suffix or not parts.domain:
            return None

    return ParsedUrl(
        scheme=scheme,
        userinfo=normalize_component(userinfo, _SUB_DELIMS + ":"),
        host=host,
        port=port,
        path=path,
        query=query,
        fragment=fragment,
        subdomain=parts.subdomain,
        domain=parts.domain,
        suffix=parts.suffix,
    )
