"""urlgenie -- URL generalization, contact extraction and validation.

Small, explicit functions instead of one function with a dozen flags::

    from urlgenie import generalize, generalize_social, extract_social_handle

    print(generalize("cnn.com/sports/about?a=b#c"))
    >> https://cnn.com/sports/about

    print(generalize_social("fb.com/@ahmedkhatib"))
    >> https://www.facebook.com/ahmedkhatib

    print(extract_social_handle("x.com/elonmusk").handle)
    >> elonmusk
"""

from .extract import extract_contacts, validate_contacts
from .generalize import generalize, generalize_many, generalize_url
from .social import detect_platform, extract_social_handle, generalize_social, is_social_url
from .types import ExtractResult, ParsedUrl, Platform, Rule, SocialHandle
from .uri import normalize_component, normalize_host, parse_url, remove_dot_segments
from .validate import (
    email_domain_matches,
    normalize_phone,
    validate_email,
    validate_phone,
    validate_social,
    validate_social_platform,
    validate_social_profile,
    validate_url,
)

__version__ = "2.1.0"

__all__ = [
    "ExtractResult",
    "ParsedUrl",
    "Platform",
    "Rule",
    "SocialHandle",
    "detect_platform",
    "email_domain_matches",
    "extract_contacts",
    "extract_social_handle",
    "generalize",
    "generalize_many",
    "generalize_social",
    "generalize_url",
    "is_social_url",
    "normalize_component",
    "normalize_host",
    "normalize_phone",
    "parse_url",
    "remove_dot_segments",
    "validate_contacts",
    "validate_email",
    "validate_phone",
    "validate_social",
    "validate_social_platform",
    "validate_social_profile",
    "validate_url",
]
