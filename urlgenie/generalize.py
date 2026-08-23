"""URL generalization -- the standardizing counterpart to :mod:`urlgenie.uri`."""

from __future__ import annotations

from typing import List, Optional, Tuple

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


def generalize_many(
    urls, *, separator: str = ",", social: bool = True, drop_invalid: bool = False, **kwargs
) -> List[Tuple[str, Optional[str]]]:
    """Generalize a delimited string or an iterable of URLs.

    Returns one ``(original, generalized)`` pair per non-blank input, in the
    same order given -- ``generalized`` is ``None`` for an invalid entry
    rather than the row being dropped, so a bad URL never shifts every result
    after it out of alignment with its input.

    Set ``drop_invalid=True`` to omit invalid entries from the result instead
    of keeping them as ``None`` -- useful for a one-off run where you only
    want the URLs that came out clean and do not care which input produced
    which output. The return shape does not change: you still get
    ``(original, generalized)`` pairs, just fewer of them.

    Every keyword argument is forwarded to :func:`generalize`, so no flag can
    be silently lost here.
    """
    if isinstance(urls, str):
        urls = urls.split(separator)

    results = []
    for item in urls:
        if not isinstance(item, str) or not item.strip():
            continue
        original = item.strip()
        generalized = generalize(original, social=social, **kwargs)
        if drop_invalid and generalized is None:
            continue
        results.append((original, generalized))
    return results
