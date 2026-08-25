# Who's urlgenie for?

Five shapes of the same underlying problem: a URL, email, phone number or
social link arrives as an untrusted string, and something downstream needs to
know what it actually is before it can be used. Every example below is
real output, run against the package itself.

## Scrapers and crawlers

A scraped column is half junk, and every request spent on a fake domain is a
request wasted. Validate before you fetch, extract once the page is in hand.

```python
import urlgenie

candidates = ["https://acme.com/team", "not-a-real-link", "https://acme.zzz/page"]
to_fetch = [c for c in candidates if urlgenie.validate_url(c)]
>> ['https://acme.com/team']

page_text = "Contact us: hello@acme.com or +1 (415) 555-2671. Follow: facebook.com/acme"
contacts = urlgenie.extract_contacts(page_text)
>> emails={'hello@acme.com'}  phones={'+14155552671'}  facebook={'https://www.facebook.com/acme'}
```

## Extractor plugins

Same job as a crawler, running one page at a time and usually client-side --
a browser extension pulling contact details out of whatever page is open,
without shipping a second copy of the extraction regexes to keep in sync.

```python
from urlgenie import extract_contacts

contacts = extract_contacts(document_text)
# same function, same rules, whether it runs on one page or ten million
```

## Form validation

The difference between "is this a URL" and "is this the specific thing the
field is asking for" matters here. A Facebook-profile field shouldn't just
accept any facebook.com link.

```python
from urlgenie import validate_email, validate_social_profile

validate_email(form["email"])                                    # True
validate_social_profile(form["facebook_url"], "facebook")        # True only if it's a real profile
```

`facebook.com/profile.php` alone would pass a plain URL check and fail this
one -- see [`validate_social_platform` vs. `validate_social_profile`](README.md#validating-a-social-url-against-an-expected-platform)
for the split.

## Data cleaning and processing

The same page, email, or profile shows up spelled four different ways across
a dataset. `generalize` collapses the differences that don't matter --
case, query strings, trailing slashes, `fb.com` vs `facebook.com` -- so
different spellings resolve to the same key.

```python
from urlgenie import generalize_many

urls = "http://Acme.com/Team/?utm_source=newsletter,https://acme.com/Team,ACME.COM/Team/"
for original, cleaned in generalize_many(urls):
    print(original, "->", cleaned)
>> http://Acme.com/Team/?utm_source=newsletter -> https://acme.com/Team
>> https://acme.com/Team                       -> https://acme.com/Team
>> ACME.COM/Team/                              -> https://acme.com/Team
```

Worth knowing: this only forces a canonical subdomain for recognized social
platforms. `www.acme.com` and `acme.com` stay distinct for an ordinary site,
since urlgenie has no way to know those resolve to the same page -- only that
they might not.

```python
urls = "fb.com/@acme,facebook.com/acme,FACEBOOK.COM/acme?ref=nav"
for original, cleaned in generalize_many(urls):
    print(original, "->", cleaned)
>> fb.com/@acme              -> https://www.facebook.com/acme
>> facebook.com/acme         -> https://www.facebook.com/acme
>> FACEBOOK.COM/acme?ref=nav -> https://www.facebook.com/acme
```

## ETL pipelines

Extraction and validation compose as pipeline steps: pull contacts out of a
raw text field, then filter to the ones that actually belong to the record
you're loading, before anything reaches the warehouse.

```python
from urlgenie import extract_contacts, validate_contacts

text = "Reach us at sales@acme.com or the founder personally at alex@gmail.com."
contacts = extract_contacts(text)
>> emails={'sales@acme.com', 'alex@gmail.com'}

validated = validate_contacts(contacts, url="https://www.acme.com")
>> emails={'sales@acme.com'}   # alex@gmail.com dropped -- not acme.com's domain
```

## Full API

None of this needs a new import beyond `urlgenie` itself. See the
[README](README.md#-api) for the complete function list, or
[`explain.py`](urlgenie/explain.py) if you want the *why* behind a verdict,
not just the true/false.
