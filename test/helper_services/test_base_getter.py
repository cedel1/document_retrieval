"""Tests for the abstract base getter class."""

import pickle
import ssl
from unittest.mock import patch

import pytest
import urllib3

from src.helper_services.base_getter import (
    BaseGetterMethod,
    CertificateValidationError,
    MetadataSearch,
    PageSearch,
    is_certificate_verification_error,
)
from src.helper_services.simple_dom_getter import SimpleDomGetterMethod


@pytest.fixture
def dummy_getter():
    """Fixture providing a concrete implementation of BaseGetterMethod for testing."""

    class DummyGetter(BaseGetterMethod):
        def get_document_source(self, document_url: str):
            return None

        def get_pages(self, document_url: str, search_parameter: PageSearch) -> list[str]:
            return [document_url, search_parameter["name"]]

        def get_title(self, document_url: str, search_parameter: MetadataSearch) -> str:
            return ""

        def get_subtitle(self, document_url: str, search_parameter: MetadataSearch) -> str:
            return ""

        def get_part_title(self, document_url: str, search_parameter: MetadataSearch) -> str:
            return ""

        def get_part_subtitle(self, document_url: str, search_parameter: MetadataSearch) -> str:
            return ""

    return DummyGetter({})


def test_init_should_raise_type_error_for_abstract_base_class():
    """Test that the base getter class remains abstract and cannot be instantiated."""
    with pytest.raises(TypeError):
        BaseGetterMethod("identifier_pattern")


def test_get_pages_should_work_for_concrete_subclass(dummy_getter):
    """Test that a concrete subclass can implement get_pages without overriding the base contract."""
    assert dummy_getter.get_pages("https://example.com", {"name": "pages"}) == [
        "https://example.com",
        "pages",
    ]


def test_get_pages_should_raise_not_implemented_on_base_class():
    """Test that the abstract get_pages method raises NotImplementedError when invoked directly."""
    with pytest.raises(NotImplementedError, match="This method should be implemented in subclasses"):
        BaseGetterMethod.get_pages(None, "https://example.com", "pages")


def test_get_title_should_raise_not_implemented_on_base_class():
    """Test that the abstract get_title method raises NotImplementedError when invoked directly."""
    with pytest.raises(NotImplementedError, match="This method should be implemented in subclasses"):
        BaseGetterMethod.get_title(None, "https://example.com", "//h1")


def test_get_subtitle_should_raise_not_implemented_on_base_class():
    """Test that the abstract get_subtitle method raises NotImplementedError when invoked directly."""
    with pytest.raises(NotImplementedError, match="This method should be implemented in subclasses"):
        BaseGetterMethod.get_subtitle(None, "https://example.com", "//h2")


@pytest.mark.parametrize(
    "instance_params, expected_calls",
    [
        ({}, []),
        ({"allow_insecure": False}, []),
        ({"allow_insecure": True}, [(urllib3.exceptions.InsecureRequestWarning,)]),
    ],
)
def test_init_should_suppress_urllib3_warning_only_when_allow_insecure(instance_params, expected_calls):
    with patch("urllib3.disable_warnings") as disable_warnings:
        SimpleDomGetterMethod(instance_params)

    assert [call.args for call in disable_warnings.call_args_list] == expected_calls


def test_is_certificate_verification_error_should_find_nested_verification_error():
    cause = ssl.SSLCertVerificationError("invalid certificate")
    error = urllib3.exceptions.MaxRetryError(None, "/", urllib3.exceptions.SSLError(cause))

    assert is_certificate_verification_error(error)


def test_is_certificate_verification_error_should_not_treat_other_ssl_errors_as_certificate_failure():
    assert not is_certificate_verification_error(ssl.SSLError("handshake failed"))


def test_certificate_validation_error_should_survive_pickling():
    error = CertificateValidationError("certificate failed")

    result = pickle.loads(pickle.dumps(error))

    assert isinstance(result, CertificateValidationError)
    assert str(result) == str(error)
