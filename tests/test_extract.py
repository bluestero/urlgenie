"""Contact extraction from free text."""

import pytest

from urlgenie import ExtractResult, extract_contacts, validate_contacts

TEXT = """
This is a good email: sample@gmail.com and this is a bad email: sample@image.png.
Another would be an email with a custom domain: sample@example.com.
Sample facebook facebook.com/sample1, lets try with fb domain: fb.com/sample2.
Lets add a bad facebook: fb.com/profile.php?
Lets add 2 twitter formats: x.com/sample and twitter.com/sample with same handles.
How about a linkedin pub? linkedin.com/pub/aravind-p-r/24/324/185?_l=en_US.
Let's also add its in url: linkedin.com/in/aravind-p-r-18532424/
Call us on +1 (415) 555-2671.
"""


def test_extract_works_with_default_arguments():
    """v1 raised TypeError here because exclude_cols defaulted to None."""
    result = extract_contacts(TEXT)
    assert isinstance(result, ExtractResult)
    assert not result.is_empty()


def test_extracted_emails():
    result = extract_contacts(TEXT)
    assert result.emails == {"sample@gmail.com", "sample@example.com"}


def test_extracted_socials_are_already_canonical():
    result = extract_contacts(TEXT)
    assert result.facebook == {"https://www.facebook.com/sample1", "https://www.facebook.com/sample2"}
    #-x.com and twitter.com collapse to one entry-#
    assert result.twitter == {"https://twitter.com/sample"}
    #-pub and in forms collapse to one entry-#
    assert result.linkedin == {"https://www.linkedin.com/in/aravind-p-r-18532424"}
    assert result.instagram == set()


def test_extracted_phones():
    assert "+14155552671" in extract_contacts(TEXT).phones


def test_include_and_exclude():
    only_email = extract_contacts(TEXT, include=["emails"])
    assert only_email.emails
    assert not only_email.facebook

    without_social = extract_contacts(TEXT, exclude=["facebook", "twitter", "linkedin"])
    assert without_social.emails
    assert not without_social.facebook
    assert not without_social.twitter


def test_exclude_none_is_not_iterated():
    assert extract_contacts(TEXT, include=None, exclude=None).emails


def test_validate_contacts_filters_emails_by_site():
    result = extract_contacts(TEXT)
    validated = validate_contacts(result, url="https://www.example.com/ContactUs")
    assert validated.emails == {"sample@example.com"}
    #-Socials are untouched by the email filter-#
    assert validated.facebook == result.facebook


def test_validate_contacts_does_not_mutate_input():
    result = extract_contacts(TEXT)
    before = set(result.emails)
    validate_contacts(result, url="https://www.example.com")
    assert result.emails == before


@pytest.mark.parametrize("text", [None, "", 123])
def test_extract_handles_bad_input(text):
    assert extract_contacts(text).is_empty()


def test_as_dict_round_trip():
    result = extract_contacts(TEXT)
    assert set(result.as_dict()) == set(ExtractResult.FIELDS)
