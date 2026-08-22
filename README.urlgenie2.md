# urlgenie2

URL generalization, contact extraction and validation. A clean-room rewrite of
`urlgenie` with an RFC 3986 compliant core and small, explicit functions in
place of one `generalize()` with a dozen flags.

## Layout

`urlgenie2/` sits next to the v1 `urlgenie/` package in this repo so the two can
be compared directly. Packaging metadata is kept under distinct names
(`pyproject.urlgenie2.toml`, `README.urlgenie2.md`) so it does not collide with
v1's `setup.py`. When v2 replaces v1: delete `urlgenie/`, rename `urlgenie2/` to
`urlgenie/`, rename those two files to `pyproject.toml` / `README.md`, and drop
`setup.py` and `setup.cfg`.

## Install

```shell
python -m pip install tldextract pytest
```

Depends only on `tldextract`, which is used offline against its bundled public
suffix list — no network access at import or call time.

## Usage

```python
from urlgenie2 import generalize, generalize_social, extract_social_handle, extract_contacts

generalize("cnn.com/sports/about?a=b#c")     # 'https://cnn.com/sports/about'
generalize_social("fb.com/@ahmedkhatib")     # 'https://www.facebook.com/ahmedkhatib'
extract_social_handle("x.com/elonmusk").handle   # 'elonmusk'
```

Everything returns `None` on invalid input rather than a magic string, so use
`generalize(url) or "Bad Url"` if you want a sentinel.

## API

| Function | Purpose |
| --- | --- |
| `parse_url(url)` | RFC 3986 parse + normalize into a `ParsedUrl`, or `None` |
| `validate_url(url)` | Syntactic validity, public-suffix check, scheme allowlist |
| `generalize_url(url, ...)` | Canonical URL string; `keep_path` / `keep_query` / `keep_fragment` / `keep_userinfo` / `force_https` / `lower` |
| `generalize(url, social=True)` | As above, collapsing recognized social links to their profile URL |
| `generalize_many(urls, ...)` | Same for a delimited string or iterable; forwards every flag |
| `generalize_social(url)` | Canonical social profile URL, or `None` |
| `extract_social_handle(url)` | `SocialHandle(platform, handle, url, original_handle, rule)`, or `None` |
| `detect_platform(url)` / `is_social_url(url)` | Platform lookup and membership test |
| `validate_email(email, url=None)` | Syntax, RFC 5321 length limits, optional site-domain match |
| `validate_phone(phone)` / `normalize_phone(phone)` | Pragmatic E.164-ish digit-count validation |
| `extract_contacts(text, include=, exclude=)` | Emails, phones and social profiles from free text |
| `validate_contacts(result, url=None)` | Filter an `ExtractResult`; scope emails to a site |

## Adding a social pattern

Every pattern is a separate named `Rule` in `urlgenie2/config.py`. Rules are
tried in order and the first one yielding a non-reserved handle wins, so
supporting a new URL shape is one line and touches nothing else:

```python
FACEBOOK_RULES = (
    Rule("fb_query_id",  re.compile(r"[?&](?:id|gid)=(?P<id>\d{5,})", _I)),
    Rule("fb_media_set", re.compile(r"[?&]set=a\.(?:\d+\.)*(?P<id>\d{5,})", _I)),
    ...
)
```

A rule exposes an `id` or `handle` named group; an optional `subdir` group or
attribute sets the canonical path prefix. `transform=` handles the rare case
that needs real logic (LinkedIn's legacy `/pub/` → `/in/` slug).

## RFC 3986

`urlgenie2/uri.py` implements scheme and host case normalization (§3.1, §3.2.2),
IDNA punycoding, default-port removal (§3.2.3), dot-segment resolution (§5.2.4)
and percent-encoding normalization (§2.1, §6.2.2.2). The last one is
idempotent, unlike `quote(unquote(url))`, which corrupts `%2520` and literal `%`.

## Differences from urlgenie v1

- Valid URLs v1 rejected now parse: 5+ character TLDs (`.photography`), long
  subdomain labels, ports, IDN hosts, IP literals, `example.com?a=b`.
- No hidden state. `generalize()` is pure — v1 mutated `self.subdomains` on
  every call and could leave `bad_url` corrupted after an exception.
- `extract_contacts()` works with default arguments (v1 raised `TypeError`).
- `generalize_many()` forwards every flag (v1 dropped `keep_path`).
- Escaped dots, so `facebookXcom.co` is no longer treated as Facebook.
- LinkedIn handles are lowercased like every other platform, except opaque
  `ACwAA...` member ids, which are case sensitive and must not be folded.
- Extraction and generalization share one set of rules, so they cannot disagree.

## Tests

```shell
python -m pytest tests -q       # 284 tests
python tools/compare_v1_v2.py   # diff v1 and v2 over sample.csv
```

`tests/sample.csv` is a copy of the reference sheet and is treated as the spec:
every row is asserted for both the generalized URL and the extracted handle.
