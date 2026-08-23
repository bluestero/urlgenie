"""URL generalization -- the standardizing counterpart to :mod:`urlgenie2.uri`."""

from __future__ import annotations

from typing import List, Optional

from .social import extract_social_handle
from .types import ParsedUrl
from .uri import parse_url

__all__ = ["generalize_url", "generalize", "generalize_many"]


def generalize_url(
    url,
    *,
    keep_path: bool = True,
    keep_query: bool = False,
    keep_fragment: bool = False,
    keep_userinfo: bool = False,
    force_https: bool = True,
    lower: bool = False,
) -> Optional[str]:
    """Normalize a URL to a canonical string, or return ``None`` if invalid.

    This applies RFC 3986 normalization (scheme/host case, percent-encoding,
    dot segments, default ports) and then drops the parts you do not want.
    Trailing slashes are removed so ``a.com/p`` and ``a.com/p/`` agree.
    """
    parsed = url if isinstance(url, ParsedUrl) else parse_url(url)
    if parsed is None:
        return None

    scheme = "https" if force_https and parsed.scheme in ("http", "https") else parsed.scheme

    authority = parsed.host
    if keep_userinfo and parsed.userinfo:
        authority = f"{parsed.userinfo}@{authority}"
    if parsed.port is not None:
        authority = f"{authority}:{parsed.port}"

    result = f"{scheme}://{authority}"
    if keep_path:
        result += parsed.path.rstrip("/")
    if keep_query and parsed.query:
        result += f"?{parsed.query}"
    if keep_fragment and parsed.fragment:
        result += f"#{parsed.fragment}"

    return result.lower() if lower else result


def generalize(url, *, social: bool = True, **kwargs) -> Optional[str]:
    """Generalize any URL, canonicalizing social profiles when recognized.

    Set ``social=False`` to treat social URLs like any other URL.
    Keyword arguments are forwarded to :func:`generalize_url`.
    """
    parsed = url if isinstance(url, ParsedUrl) else parse_url(url)
    if parsed is None:
        return None

    if social:
        found = extract_social_handle(parsed)
        if found is not None:
            return found.url

    return generalize_url(parsed, **kwargs)


def generalize_many(urls, *, separator: str = ",", social: bool = True, **kwargs) -> List[str]:
    """Generalize a delimited string or an iterable of URLs.

    Invalid entries are dropped. Every keyword argument is forwarded to
    :func:`generalize`, so no flag can be silently lost here.
    """
    if isinstance(urls, str):
        urls = urls.split(separator)

    results = []
    for item in urls:
        if not isinstance(item, str) or not item.strip():
            continue
        generalized = generalize(item.strip(), social=social, **kwargs)
        if generalized is not None:
            results.append(generalized)
    return results
