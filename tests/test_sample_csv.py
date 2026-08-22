"""The reference sheet is the spec: every row must round-trip exactly."""

import pytest

from conftest import load_sample_rows
from urlgenie2 import extract_social_handle, generalize, generalize_many

ROWS = load_sample_rows()


def _ids(rows):
    return [f"{section}:{url[:60]}" for section, url, _, _ in rows]


@pytest.mark.parametrize("section,url,expected,handles", ROWS, ids=_ids(ROWS))
def test_generalized_matches_sample(section, url, expected, handles):
    if "," in url and ", " in expected:
        assert ", ".join(generalize_many(url)) == expected
    else:
        assert generalize(url) == expected


@pytest.mark.parametrize(
    "section,url,expected,handles",
    [row for row in ROWS if row[0] != "WEBSITES"],
    ids=_ids([row for row in ROWS if row[0] != "WEBSITES"]),
)
def test_handles_match_sample(section, url, expected, handles):
    if "," in url and ", " in expected:
        found = [extract_social_handle(part) for part in url.split(",")]
        assert ", ".join(item.handle for item in found if item) == handles
    else:
        found = extract_social_handle(url)
        assert found is not None
        assert found.handle == handles


def test_websites_have_no_social_handle():
    for section, url, _, _ in ROWS:
        if section == "WEBSITES":
            assert extract_social_handle(url) is None
