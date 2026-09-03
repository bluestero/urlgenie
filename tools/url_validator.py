"""Minimal, dependency-free URL validator. Python 3.7+, stdlib only.

Reuses urlgenie's bundled public-suffix data (urlgenie/psl.py and
urlgenie/public_suffix_list.dat) rather than a pip package.

    from url_validator import is_valid_url

    is_valid_url("example.com")                              # True
    is_valid_url("not a url")                                # False
    is_valid_url("example.zzzzz", require_valid_tld=True)     # False -- not a real TLD
    is_valid_url("example.zzzzz")                             # True  -- TLD check is off by default
    is_valid_url("blogspot.com")                              # True  -- ordinary .com registration
    is_valid_url("b.ck")                                      # False -- ".ck" can't be registered under bare
"""

import re
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from urlgenie.psl import suffix_parts

#-A compact, hand-picked set of real TLDs -- common gTLDs, ccTLDs, and the
# popular newer ones. Not the full ~1500-entry IANA list; enough to catch
# obvious typos (.zzzzz, .haz) without a dependency or a network call.-#
_KNOWN_TLDS = {
    "com", "org", "net", "edu", "gov", "mil", "int", "io", "co", "ai", "app",
    "dev", "info", "biz", "name", "pro", "shop", "store", "tech", "online",
    "site", "xyz", "club", "blog", "me", "tv", "cc", "us", "uk", "ca", "au",
    "de", "fr", "es", "it", "nl", "ru", "cn", "jp", "kr", "in", "br", "mx",
    "za", "ng", "eg", "sa", "ae", "il", "ch", "se", "no", "dk", "fi", "pl",
    "pt", "gr", "tr", "id", "sg", "my", "ph", "vn", "th", "nz", "ie", "be",
    "at", "cz", "hu", "ro", "ua", "hk", "tw",
}

_HOST_LABEL_RE = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$", re.IGNORECASE)


def is_valid_url(url, require_valid_tld=False):
    """True if ``url`` looks like a real, well-formed http(s) URL.

    Adds a scheme automatically if missing, so ``"example.com"`` counts.
    Checks the host is structurally sane -- valid-looking labels, a TLD made
    of at least two letters -- without touching the network. Does not accept
    IP literals (there's no TLD to check on one).

    Set ``require_valid_tld=True`` to also check the TLD against a small
    built-in list of real TLDs, which catches obvious typos like
    ``"example.zzzzz"`` at the cost of rejecting brand-new or obscure TLDs
    that aren't in that list.
    """
    if not isinstance(url, str) or not url.strip():
        return False

    url = url.strip()
    if "://" not in url:
        url = "https://" + url

    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    if parsed.scheme not in ("http", "https"):
        return False

    try:
        host = parsed.hostname
    except ValueError:
        return False
    if not host:
        return False

    labels = host.split(".")
    if len(labels) < 2 or any(not label for label in labels):
        return False
    if not all(_HOST_LABEL_RE.match(label) for label in labels):
        return False

    tld = labels[-1].lower()
    if not tld.isalpha() or not (2 <= len(tld) <= 24):
        return False

    if require_valid_tld and tld not in _KNOWN_TLDS:
        return False

    #-Reject a host that IS a public suffix with nothing registered under it,
    # e.g. bare "ck" -- not a registrable domain-#
    if not suffix_parts(host).domain:
        return False

    return True


if __name__ == "__main__":
    examples = [
        "example.com",
        "https://example.com/path?x=1",
        "www.example.co.uk",
        "not a url",
        "",
        None,
        "example.zzzzz",
        "example.photography",
        "http://192.168.1.1",
        "http://-bad-.com",
        "ftp://example.com",
    ]
    print(f"{'url':32} {'loose':>7} {'strict':>7}")
    for u in examples:
        print(f"{str(u):32} {str(is_valid_url(u)):>7} {str(is_valid_url(u, require_valid_tld=True)):>7}")
