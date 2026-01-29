"""Tests for FamilySearch URL generation."""

import pytest

from reports.links import person_url, record_search_url, search_url


def test_person_url() -> None:
    """Test person URL generation."""
    url = person_url("GK1Y-97Y")
    assert url == "https://www.familysearch.org/tree/person/details/GK1Y-97Y"


def test_person_url_with_different_id() -> None:
    """Test person URL with different ID format."""
    url = person_url("ABCD-123")
    assert url == "https://www.familysearch.org/tree/person/details/ABCD-123"


def test_search_url_with_all_params() -> None:
    """Test search URL with all parameters."""
    url = search_url(
        given_name="Josue", surname="Ibarra", birth_year="1991", birth_place="California"
    )
    assert "https://www.familysearch.org/search/tree/results?" in url
    assert "givenName=Josue" in url
    assert "surname=Ibarra" in url
    assert "birthLikeDate=1991" in url
    assert "birthLikePlace=California" in url


def test_search_url_with_name_only() -> None:
    """Test search URL with only name parameters."""
    url = search_url(given_name="John", surname="Doe")
    assert url == "https://www.familysearch.org/search/tree/results?givenName=John&surname=Doe"


def test_search_url_with_year_only() -> None:
    """Test search URL with only birth year."""
    url = search_url(birth_year="1850")
    assert url == "https://www.familysearch.org/search/tree/results?birthLikeDate=1850"


def test_search_url_with_no_params() -> None:
    """Test search URL with no parameters."""
    url = search_url()
    assert url == "https://www.familysearch.org/search/tree/results"


def test_record_search_url_with_all_params() -> None:
    """Test record search URL with all parameters."""
    url = record_search_url(collection_id="2221801", given_name="Maria", surname="Rodriguez")
    assert "https://www.familysearch.org/search/record/results?" in url
    assert "givenName=Maria" in url
    assert "surname=Rodriguez" in url
    assert "collectionId=2221801" in url


def test_record_search_url_with_collection_only() -> None:
    """Test record search URL with collection ID only."""
    url = record_search_url(collection_id="2221801")
    assert url == "https://www.familysearch.org/search/record/results?collectionId=2221801"


def test_record_search_url_with_no_params() -> None:
    """Test record search URL with no parameters."""
    url = record_search_url()
    assert url == "https://www.familysearch.org/search/record/results"


def test_search_url_parameter_order() -> None:
    """Test that search URL parameters are in expected order."""
    url = search_url(surname="Smith", given_name="John")
    # Parameters should appear in the order they're added in the function
    params_part = url.split("?")[1]
    params = params_part.split("&")
    assert params[0] == "givenName=John"
    assert params[1] == "surname=Smith"
