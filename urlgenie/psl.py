"""Public Suffix List lookup: splits a host into subdomain/domain/suffix.

A small, self-contained reimplementation of the public-suffix matching
algorithm (see https://publicsuffix.org/list/), built once at import time
from the bundled ``public_suffix_list.dat`` snapshot. No third-party
dependency, which keeps this easy to port line-for-line to other languages.

The rules are held in a trie keyed by label, walked from the TLD inward
(i.e. labels in reverse order), so the longest matching rule -- the most
specific one -- is always the last terminal node seen along a successful
walk. A rule prefixed with ``!`` is an exception: it un-matches one label
of whatever wildcard rule would otherwise have covered it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, NamedTuple, Optional

__all__ = ["suffix_parts", "SuffixParts"]

_DATA_FILE = Path(__file__).with_name("public_suffix_list.dat")

_WILDCARD_LABEL = "*"


class SuffixParts(NamedTuple):
    subdomain: str
    domain: str
    suffix: str


class _Node:
    __slots__ = ("children", "terminal")

    def __init__(self) -> None:
        self.children: Dict[str, "_Node"] = {}
        self.terminal: Optional[str] = None  # None, "suffix", or "exception"


def _build_trie() -> _Node:
    root = _Node()
    with _DATA_FILE.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("//") or line.startswith("#"):
                continue

            terminal = "exception" if line.startswith("!") else "suffix"
            rule = line[1:] if terminal == "exception" else line

            node = root
            #-Insert TLD-first (reversed) so matching walks outside-in-#
            for label in reversed(rule.split(".")):
                node = node.children.setdefault(label, _Node())
            node.terminal = terminal
    return root


_ROOT = _build_trie()


def _matched_suffix_lengths(labels):
    """Every trailing-label count that terminates a matching PSL rule, shortest first.

    E.g. for ``["foo", "blogspot", "com"]`` this is ``[1, 2]``: both ``"com"``
    and ``"blogspot.com"`` are suffix rules on their own. Exception rules
    short-circuit the walk (see :func:`suffix_parts`) since nothing can be
    a suffix deeper than one.
    """
    node = _ROOT
    depth = 0
    depths = []
    for label in reversed(labels):
        child = node.children.get(label) or node.children.get(_WILDCARD_LABEL)
        if child is None:
            break
        depth += 1
        node = child
        if node.terminal == "exception":
            #-The exception itself doesn't count; the rule it carves out of
            # is one label shorter-#
            return [depth - 1]
        if node.terminal == "suffix":
            depths.append(depth)
    return depths


def suffix_parts(host: str) -> SuffixParts:
    """Split ``host`` into ``(subdomain, domain, suffix)`` per the full PSL.

    Both ICANN suffixes (real TLDs, e.g. ``"co.uk"``) and PRIVATE suffixes
    (donated ones, e.g. ``"blogspot.com"``, ``"github.io"``) count as a
    suffix -- ``"foo.blogspot.com"`` gets ``domain="foo"``,
    ``suffix="blogspot.com"``, since each blog is effectively its own site.

    An unrecognized TLD yields an empty ``suffix`` (the last label becomes
    ``domain`` instead). A host that *is* itself the longest matching suffix
    (e.g. ``"blogspot.com"``, ``"kalisz.pl"``) falls back to the next-shorter
    matching rule so it still gets a domain -- ``"blogspot.com"`` is, after
    all, an ordinary ``.com`` registration from Google's side; the multi-label
    rule only matters for what other people register underneath it. If no
    shorter rule matches either (a suffix-only zone like Cook Islands' bare
    ``.ck``, where nothing can be registered directly under it), ``domain``
    stays empty.
    """
    labels = host.lower().split(".")
    depths = _matched_suffix_lengths(labels)

    if not depths:
        domain = labels[-1]
        subdomain = ".".join(labels[:-1])
        return SuffixParts(subdomain=subdomain, domain=domain, suffix="")

    #-Prefer the longest match, but if it swallows the whole host, fall back
    # to the next-shorter one so there's still a domain label left over-#
    suffix_len = depths[-1]
    if suffix_len == len(labels):
        shorter = [d for d in depths if d < len(labels)]
        if not shorter:
            return SuffixParts(subdomain="", domain="", suffix=".".join(labels))
        suffix_len = shorter[-1]

    suffix = ".".join(labels[len(labels) - suffix_len :])
    domain = labels[len(labels) - suffix_len - 1]
    subdomain = ".".join(labels[: len(labels) - suffix_len - 1])
    return SuffixParts(subdomain=subdomain, domain=domain, suffix=suffix)
