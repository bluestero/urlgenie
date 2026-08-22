"""Extraction of emails, phone numbers and social profiles from free text."""

from __future__ import annotations

from typing import Iterable, Optional

from .config import EMAIL_PATTERN, PHONE_PATTERN, SOCIAL_CANDIDATE_PATTERN
from .social import extract_social_handle
from .types import ExtractResult
from .validate import email_domain_matches, normalize_phone, validate_email

__all__ = ["extract_contacts", "validate_contacts"]


def _selected(include: Optional[Iterable[str]], exclude: Optional[Iterable[str]]) -> frozenset:
    """Resolve the include/exclude arguments into a concrete field set.

    ``None`` means "everything" for ``include`` and "nothing" for ``exclude``;
    neither is ever iterated while still ``None``.
    """
    fields = set(ExtractResult.FIELDS)
    chosen = set(include) if include is not None else set(fields)
    chosen -= set(exclude) if exclude is not None else set()
    return frozenset(chosen & fields)


def extract_contacts(
    text: str,
    *,
    include: Optional[Iterable[str]] = None,
    exclude: Optional[Iterable[str]] = None,
) -> ExtractResult:
    """Pull emails, phone numbers and social profiles out of ``text``.

    Social links are found with one permissive candidate pattern and then run
    through the platform rules, so extraction and generalization always agree
    on what counts as a valid profile.
    """
    result = ExtractResult()
    if not isinstance(text, str) or not text:
        return result

    wanted = _selected(include, exclude)

    if "emails" in wanted:
        result.emails = {match.group(0) for match in EMAIL_PATTERN.finditer(text) if validate_email(match.group(0))}

    if "phones" in wanted:
        for match in PHONE_PATTERN.finditer(text):
            normalized = normalize_phone(match.group(0))
            if normalized is not None:
                result.phones.add(normalized)

    social_fields = wanted & {"facebook", "twitter", "instagram", "linkedin", "youtube"}
    if social_fields:
        for match in SOCIAL_CANDIDATE_PATTERN.finditer(text):
            found = extract_social_handle(match.group(0).rstrip(".,;:!?"))
            if found is not None and found.platform in social_fields:
                getattr(result, found.platform).add(found.url)

    return result


def validate_contacts(result: ExtractResult, *, url=None) -> ExtractResult:
    """Return a copy of ``result`` with entries that fail validation removed.

    Passing ``url`` additionally restricts emails to that site's registrable
    domain. Social URLs produced by :func:`extract_contacts` are already
    canonical, so this mainly re-checks emails and phones.
    """
    validated = ExtractResult(
        emails={email for email in result.emails if validate_email(email)},
        phones={phone for phone in result.phones if normalize_phone(phone) is not None},
        facebook=set(result.facebook),
        twitter=set(result.twitter),
        instagram=set(result.instagram),
        linkedin=set(result.linkedin),
        youtube=set(result.youtube),
    )

    if url is not None:
        validated.emails = {email for email in validated.emails if email_domain_matches(email, url)}

    return validated
