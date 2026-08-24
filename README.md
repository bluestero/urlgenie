<p align = "center">
<img src = "https://raw.githubusercontent.com/bluestero/urlgenie/main/images/mascot.png" alt = "urlgenie" /><div align = "center" style = "margin-top: 0;">
<h1>🧞 URL Genie 🧞</h1>
</div>
<h3 align="center">
  URL extraction, generalization, validation, and filtration made easy.
</h3>

## 🚀 About URL Genie
A python package based on research involving over 2 million URLs, designed to handle
URLs in a flexible manner for data-driven projects.

Version 2 is a rewrite with an RFC 3986 compliant core and small, explicit functions
in place of one `generalize()` carrying a dozen flags. See
[Migrating from 1.x](#-migrating-from-1x) if you are upgrading.

## ✨ Features
- RFC 3986 compliant parsing, normalization and validation.
- Social profile recognition for Facebook, LinkedIn, Twitter/X, Instagram and YouTube.
- Email, phone and social extraction from free text, with validation.
- Domain-scoped email filtering, to drop contacts unrelated to a site.
- Duplicate reduction: every spelling of a profile collapses to one canonical URL.
- Public suffix validation against the bundled PSL snapshot -- no network access.
- Pure functions: no hidden state, safe to use across threads and processes.

## ⚙️ Installation

```shell
python -m pip install urlgenie
```

Depends only on `tldextract`, used offline against its bundled public suffix list.

## ♨️ Usage

```python
from urlgenie import generalize, generalize_social, extract_social_handle

print(generalize("cnn.com/sports/about?a=b#c"))
>> https://cnn.com/sports/about

print(generalize("facebook.com.br/@Ahmed.Khatib"))
>> https://www.facebook.com/ahmedkhatib

print(generalize_social("x.com/elonmusk"))
>> https://twitter.com/elonmusk

print(extract_social_handle("x.com/elonmusk").handle)
>> elonmusk
```

Everything returns `None` on invalid input rather than a magic string, so use
`generalize(url) or "Bad Url"` if you want a sentinel:

```python
df["clean"] = df["url"].apply(lambda u: generalize(u) or "Bad Url")
```

For a one-off batch, `generalize_many` keeps every entry in place -- an invalid
URL comes back as `None` rather than being silently dropped, so nothing shifts
out of alignment with your input:

```python
from urlgenie import generalize_many

for original, result in generalize_many("facebook.com,facebook/com,dummy.com,instagram.com/ahmed"):
    print(f"{original:22} -> {result}")

>> facebook.com           -> https://facebook.com
>> facebook/com           -> None
>> dummy.com              -> https://dummy.com
>> instagram.com/ahmed    -> https://www.instagram.com/ahmed
```

For a one-off run where you only want the URLs that came out clean and do not
need to know which input produced which, pass `drop_invalid=True`:

```python
generalize_many("facebook.com,facebook/com,dummy.com,instagram.com/ahmed", drop_invalid=True)
>> [('facebook.com', 'https://facebook.com'), ('dummy.com', 'https://dummy.com'), ('instagram.com/ahmed', 'https://www.instagram.com/ahmed')]
```

```python
print(generalize("random.haz/somePath") or "Bad Url")
>> Bad Url
```

### Validating a social URL against an expected platform

A form field asking for a Facebook profile has to check two different things:
is this a Facebook URL at all, and does it actually point at a profile?

```python
from urlgenie import validate_social_platform, validate_social_profile

url = "facebook.com/profile.php"

print(validate_social_platform(url, "facebook"))
>> True

print(validate_social_profile(url, "facebook"))
>> False

print(validate_social_profile("facebook.com/profile.php?id=123123123", "facebook"))
>> True
```

`profile.php` alone belongs to Facebook but isn't a profile -- it's a reserved
path with no id. Adding `?id=...` is what makes it one.

### Extracting contacts from a page

```python
from urlgenie import extract_contacts, validate_contacts

result = extract_contacts(scraped_text)

print(result.emails)
>> {'sales@example.com', 'someone@gmail.com'}

print(result.facebook)
>> {'https://www.facebook.com/example'}

print(result.phones)
>> {'+14155552671'}

#-Keep only emails belonging to the site being scraped-#
validated = validate_contacts(result, url="https://www.example.com/contact")

print(validated.emails)
>> {'sales@example.com'}
```

## 📋 API

| Function | Purpose |
| --- | --- |
| `generalize(url, social=True, ...)` | Canonical URL, collapsing recognized social links to their profile |
| `generalize_url(url, ...)` | Canonical URL only; `keep_path` / `keep_query` / `keep_fragment` / `keep_userinfo` / `force_https` / `lower` |
| `generalize_many(urls, drop_invalid=False, ...)` | Same for a delimited string or iterable; returns `[(original, result), ...]` in order, so an invalid entry is `None` in place rather than dropped. Pass `drop_invalid=True` to omit those pairs entirely when you only want the clean ones |
| `generalize_social(url)` | Canonical social profile URL, or `None` |
| `extract_social_handle(url)` | `SocialHandle(platform, handle, url, original_handle, rule)`, or `None` |
| `detect_platform(url)` / `is_social_url(url)` | Platform lookup and membership test |
| `parse_url(url)` | RFC 3986 parse + normalize into a `ParsedUrl`, or `None` |
| `validate_url(url)` | Syntactic validity, public-suffix check, scheme allowlist |
| `validate_email(email, url=None)` | Syntax, RFC 5321 length limits, optional site-domain match |
| `validate_phone(phone)` / `normalize_phone(phone)` | Pragmatic digit-count validation |
| `validate_social(url)` | Whether a URL is a recognized profile, on any platform |
| `validate_social_platform(url, platform)` | Whether a URL's domain belongs to `platform` (e.g. `"facebook"`), regardless of whether the path resolves to a profile |
| `validate_social_profile(url, platform)` | Whether a URL resolves to an actual profile/handle on `platform`. `facebook.com/profile.php` passes the platform check but not this one |
| `extract_contacts(text, include=, exclude=)` | Emails, phones and socials from free text |
| `validate_contacts(result, url=None)` | Filter an `ExtractResult`; scope emails to a site |

## 🔀 Migrating from 1.x

Version 2 removes the `UrlGenie` class. Import the functions directly.

```python
# 1.x
from urlgenie import UrlGenie
genie = UrlGenie(bad_url = "Bad Url", proper_tlds = True)
print(genie.generalize("fb.com/@ahmedkhatib"))
>> https://www.facebook.com/ahmedkhatib

# 2.x
from urlgenie import generalize
print(generalize("fb.com/@ahmedkhatib") or "Bad Url")
>> https://www.facebook.com/ahmedkhatib
```

| 1.x | 2.x |
| --- | --- |
| `UrlGenie(bad_url=..., bad_social=...)` | functions return `None`; use `or "Bad Url"` |
| `proper_tlds=True` | always on, via the public suffix list |
| `generalize(url)` | `generalize(url)` |
| `generalize(url, get_handle=True)` | `extract_social_handle(url).handle` |
| `generalize(url, get_domain=True)` | `parse_url(url).domain` |
| `generalize(url, get_domain_with_tld=True)` | `parse_url(url).registrable_domain` |
| `generalize(url, comma_separated=True)` | `generalize_many(url)` -- note this returns `(original, result)` pairs, not a flat list |
| `generalize(url, social_rectification=False)` | `generalize(url, social=False)` |
| `generalize(url, keep_periods=False)` | always on for Facebook, which ignores periods |
| `extract_from_text(text)` | `extract_contacts(text)` |
| `validate_result_dict(d, url=...)` | `validate_contacts(result, url=...)` |
| `update_subdomains()` / `get_subdomains()` | removed; `generalize()` keeps no state |

Behaviour changes worth knowing:
- URLs 1.x silently rejected now parse: TLDs longer than four characters, subdomain
  labels longer than ten, ports, IDN hosts, IP literals, and `example.com?a=b`.
  Measured against the Tranco top 1M, 1.x rejected 4.72% of real domains; 2.x rejects 0.
- Twitter handles follow Twitter's actual rules (15 characters, no periods), so some
  strings 1.x accepted are now rejected.
- Facebook handles have periods stripped, since Facebook ignores them when resolving
  profiles. LinkedIn and Instagram periods are significant and preserved.

## 🧩 Adding a social pattern

Every pattern is a separate named `Rule` in `urlgenie/config.py`. Rules are tried in
order and the first yielding a non-reserved handle wins, so supporting a new URL shape
is one line and touches nothing else:

```python
FACEBOOK_RULES = (
    Rule("fb_query_id",  re.compile(r"[?&](?:id|gid|__user)=(?P<id>\d{5,})", _I)),
    Rule("fb_media_set", re.compile(r"[?&]set=a\.(?:\d+\.)*(?P<id>\d{5,})", _I)),
    ...
)
```

A rule exposes an `id` or `handle` named group; an optional `subdir` group or attribute
sets the canonical path prefix. `transform=` handles the rare case needing real logic,
such as LinkedIn's legacy `/pub/` to `/in/` slug conversion.

## 📐 RFC 3986

`urlgenie/uri.py` implements scheme and host case normalization (§3.1, §3.2.2), IDNA
punycoding, default-port removal (§3.2.3), dot-segment resolution (§5.2.4) and
percent-encoding normalization (§2.1, §6.2.2.2). The last is idempotent, unlike
`quote(unquote(url))`, which corrupts `%2520` and literal `%`.

## ⚡ Performance

Roughly 60,000 URLs per second single-threaded (~17s for one million), measured over a
corpus of one million distinct URLs. Every function is pure, so `multiprocessing.Pool`
scales it linearly.

```shell
python tools/benchmark.py 1000000
```

## 🧪 Tests

```shell
python -m pytest tests -q      # 287 tests
```

`sample.csv` at the repo root is the reference sheet and is treated as the spec,
read directly by the test suite: every row is asserted for both the generalized
URL and the extracted handle.

## 📖 Resources
- [Sample Sheet](https://docs.google.com/spreadsheets/d/12QHwZxiDv80ksFngQK10hkOmPQLRpI0s6dPfe6mRuxk/edit?usp=sharing)
- [Social Research Doc](https://docs.google.com/document/d/12Z025x5m9xBlEahkiRI0wLE0zJNhPtSTCllk_GIqReQ/edit?usp=sharing)

## ⭐ Love It? [Star It!](https://github.com/bluestero/urlgenie)
Just a simple click but would help me out ;)
