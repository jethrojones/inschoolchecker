import pytest

from app.services.url_safety import UnsafeURLError, canonical_domain, normalize_url


def test_normalize_url_adds_scheme_and_path():
    assert normalize_url("examplek12.org") == "https://examplek12.org/"


def test_canonical_domain_strips_www():
    assert canonical_domain("https://www.examplek12.org/calendar") == "examplek12.org"


def test_normalize_url_rejects_unsupported_scheme():
    with pytest.raises(UnsafeURLError):
        normalize_url("ftp://examplek12.org")

