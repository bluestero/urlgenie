"""Throughput benchmark for urlgenie (and v1 for comparison).

    python tools/benchmark.py [count]

The corpus is built by mutating the social URL shapes from sample.csv so that
handles, ids, subdomains and country TLDs all vary. Repeating one URL a million
times would measure the CPU's string cache, not the library.
"""

import pathlib
import random
import string
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import urlgenie

try:
    from urlgenie import UrlGenie
except Exception:  # pragma: no cover
    UrlGenie = None

#-Shapes taken from sample.csv; {h} is a handle slot, {i} a numeric id slot-#
TEMPLATES = [
    "fb.com/@{h}",
    "facebook.com/{h}..90/about?idk=idk#some_fragment",
    "facebook.com/pg/{i}",
    "facebook.com/watch/{h}",
    "facebook.com/#!/{h}",
    "facebook.com/home.php?#!/{h}",
    "facebook.com/?ref=logo#!/{h}",
    "facebook.com/pages/category/photographer/{h}-{i}",
    "facebook.com/profile.php?tsid=0.1&source=typeahead&id={i}",
    "facebook.com/{h}-{i}",
    "facebook.com/group.php?gid={i}",
    "facebook.com/pages/{h}/{i}",
    "facebook.com/groups/groupid/user/{i}",
    "facebook.com.br/{h}",
    "www.secure.latest.facebook.com.au/#!/pages/{h}/{i}?some=query#frag",
    "facebook.com/media/set/?set=a.1386330472434.107549.{i}",
    "linkedin.com/in/{h}-99/about/anything?keyvalue&something#frag",
    "https://www.linkedin.com/pub/{h}/28/1b8/a?_l=en_US",
    "https://www.linkedin.com/groups/{h}-{i}/",
    "https://www.linkedin.com/company-beta/{i}/",
    "https://www.linkedin.com/organization-guest/company/{h}-?challengeId=AQG1JHkLLbFJ",
    "http://www.linkedin.com/groupInvitation?gID={i}",
    "http://www.linkedin.com/companies/{h}?trk=fc_badge",
    "https://www.linkedin.com/edu/school?id={i}&trk=tyah",
    "https://ie.linkedin.com/edu/{h}-{i}",
    "https://linkedin.com/showcase/{h}/",
    "https://www.linkedin.com/grps/{h}-{i}/",
    "https://www.linkedin.com.br/in/{h}-915b9a12a/",
    "x.com/{h}",
    "twitter.com/{h}/about/anything?keyvalue&something#frag",
    "twitter.com/@{h}",
    "twitter.com/intent/follow?original_referer=&screen_name={h}",
    "instagram.com/{h}/about/anything?keyvalue&something#frag",
    "instagram.com/accounts/login/?next=/{h}/",
    "youtube.com/@{h}",
    "youtube.com/c/{h}",
    "cnn.com/sports/about/{h}?keyvalue&something#frag",
    "{h}.example.com/some/path?a=b#c",
]


def build_corpus(count, seed=1234):
    """Build `count` distinct URLs by filling the templates with varied values."""
    rng = random.Random(seed)
    letters = string.ascii_lowercase
    corpus = []
    for index in range(count):
        template = TEMPLATES[index % len(TEMPLATES)]
        handle = "".join(rng.choice(letters) for _ in range(rng.randint(5, 14)))
        numeric = rng.randint(10_000_000, 999_999_999)
        corpus.append(template.format(h=handle, i=numeric))
    return corpus


def measure(label, function, corpus):
    start = time.perf_counter()
    hits = 0
    for url in corpus:
        if function(url) is not None:
            hits += 1
    elapsed = time.perf_counter() - start
    rate = len(corpus) / elapsed
    micros = elapsed / len(corpus) * 1e6
    print(f"{label:34} {elapsed:7.2f}s   {rate:10,.0f} url/s   {micros:6.2f} us/url   {hits:,} resolved")
    return elapsed


def main(count):
    print(f"Building corpus of {count:,} distinct URLs ...")
    corpus = build_corpus(count)
    print(f"unique: {len(set(corpus)):,}\n")

    print(f"{'':34} {'elapsed':>8}   {'throughput':>10}          {'latency':>7}")
    measure("v2 parse_url (parsing only)", urlgenie.parse_url, corpus)
    measure("v2 extract_social_handle", urlgenie.extract_social_handle, corpus)
    measure("v2 generalize (full path)", urlgenie.generalize, corpus)
    measure("v2 generalize_url (no social)", urlgenie.generalize_url, corpus)

    if UrlGenie is not None:
        genie = UrlGenie()
        measure("v1 generalize", genie.generalize, corpus)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 1_000_000)
