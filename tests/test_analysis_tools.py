"""Tests for analysis tools."""

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from db import connection
from tools.analysis_tools import (
    tool_compare_persons,
    tool_detect_name_duplicates,
    tool_validate_timeline,
)


@pytest.fixture
def simple_db(tmp_path: Path) -> Path:
    """Create a simple test database."""
    db_path = tmp_path / "simple.sqlite"
    conn = sqlite3.connect(str(db_path))

    conn.executescript("""
        CREATE TABLE persons (person_id TEXT PRIMARY KEY, display_name TEXT, gender TEXT);
        CREATE TABLE person_names (person_id TEXT, name_type TEXT, given_name TEXT, surname TEXT,
            normalized_given TEXT, normalized_surname TEXT, soundex_given TEXT, soundex_surname TEXT);
        CREATE TABLE facts (person_id TEXT, fact_type TEXT, date_sort INTEGER, place_normalized TEXT);
        CREATE TABLE parent_child_relationships (parent_id TEXT, child_id TEXT, parent_role TEXT);
        CREATE TABLE couple_relationships (person1_id TEXT, person2_id TEXT, marriage_date TEXT, marriage_place TEXT);
        CREATE TABLE sources (source_id TEXT PRIMARY KEY, title TEXT);
        CREATE TABLE person_source_refs (person_id TEXT, source_id TEXT, tag TEXT);

        INSERT INTO persons VALUES ('P1', 'Alice Smith', 'F');
        INSERT INTO persons VALUES ('P2', 'Alice Smith', 'F');
        INSERT INTO person_names VALUES
            ('P1', 'BirthName', 'Alice', 'Smith', 'alice', 'smith', 'A420', 'S530'),
            ('P2', 'BirthName', 'Alice', 'Smith', 'alice', 'smith', 'A420', 'S530');
        INSERT INTO facts VALUES ('P1', 'Birth', 19600101, 'California');
        INSERT INTO facts VALUES ('P1', 'Death', 20200101, 'California');
        INSERT INTO facts VALUES ('P2', 'Birth', 19600101, 'California');
    """)

    conn.commit()
    conn.close()
    return db_path


@pytest.fixture(autouse=True)
def mock_simple_db(simple_db: Path) -> None:
    """Automatically patch the database for all tests."""
    with patch.object(connection, "FS_CACHE_PATH", simple_db):
        connection._fs_conn = None
        yield
        connection.close_connections()


def test_tool_detect_name_duplicates_no_filter() -> None:
    """Test detecting name duplicates without surname filter."""
    result = tool_detect_name_duplicates(surname_filter=None, similarity_threshold=0.60)

    assert "surname_filter" in result
    assert result["surname_filter"] == "All"
    assert "threshold" in result
    assert result["threshold"] == 0.60
    assert "cluster_count" in result
    assert "clusters" in result
    assert isinstance(result["clusters"], list)


def test_tool_detect_name_duplicates_with_filter() -> None:
    """Test detecting name duplicates with surname filter."""
    result = tool_detect_name_duplicates(surname_filter="Smith", similarity_threshold=0.50)

    assert result["surname_filter"] == "Smith"
    assert result["threshold"] == 0.50
    assert isinstance(result["clusters"], list)


def test_tool_validate_timeline_specific_person() -> None:
    """Test validating timeline for a specific person."""
    result = tool_validate_timeline(person_id="P1", min_severity="warning")

    assert "person_id" in result
    assert result["person_id"] == "P1"
    assert "person_name" in result
    assert "issue_count" in result
    assert "issues" in result
    assert isinstance(result["issues"], list)


def test_tool_validate_timeline_all_persons() -> None:
    """Test validating timeline for all persons."""
    result = tool_validate_timeline(person_id=None, min_severity="warning")

    assert "scope" in result
    assert result["scope"] == "all_persons"
    assert "min_severity" in result
    assert result["min_severity"] == "warning"
    assert "issue_count" in result
    assert "issues" in result


def test_tool_compare_persons() -> None:
    """Test comparing two persons."""
    result = tool_compare_persons(person_id_a="P1", person_id_b="P2")

    assert "person_a" in result
    assert "person_b" in result
    assert "similarity_score" in result
    assert isinstance(result["similarity_score"], (int, float))
    assert 0 <= result["similarity_score"] <= 1
    assert "likely_duplicate" in result
    assert isinstance(result["likely_duplicate"], bool)


def test_tool_check_relationships() -> None:
    """Test checking relationships."""
    from tools.analysis_tools import tool_check_relationships

    result = tool_check_relationships(person_id="P1", check_types=["circular", "structure"])

    assert "person_id" in result
    assert result["person_id"] == "P1"
    assert "issues" in result
    assert isinstance(result["issues"], list)


def test_tool_analyze_source_coverage() -> None:
    """Test analyzing source coverage."""
    from tools.analysis_tools import tool_analyze_source_coverage

    result = tool_analyze_source_coverage(root_person_id="P1", min_sources_per_person=1)

    assert "root_person_id" in result
    assert result["root_person_id"] == "P1"
    assert "top_priorities" in result
    assert isinstance(result["top_priorities"], list)


def test_tool_find_duplicates() -> None:
    """Test finding duplicates."""
    from tools.analysis_tools import tool_find_duplicates

    result = tool_find_duplicates(threshold=0.85)

    assert "threshold" in result
    assert result["threshold"] == 0.85
    assert "duplicates" in result
    assert isinstance(result["duplicates"], list)
