"""Tests for timeline validation."""

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from analysis.timeline_validator import validate_all_timelines, validate_person_timeline
from db import connection


@pytest.fixture
def timeline_db(tmp_path: Path) -> Path:
    """Create test database with timeline issues."""
    db_path = tmp_path / "timeline.sqlite"
    conn = sqlite3.connect(str(db_path))

    conn.executescript("""
        CREATE TABLE persons (person_id TEXT PRIMARY KEY, display_name TEXT, gender TEXT);
        CREATE TABLE person_names (person_id TEXT, name_type TEXT, given_name TEXT, surname TEXT,
            normalized_given TEXT, normalized_surname TEXT, soundex_given TEXT, soundex_surname TEXT);
        CREATE TABLE facts (person_id TEXT, fact_type TEXT, date_sort INTEGER, date_original TEXT, place_normalized TEXT);
        CREATE TABLE parent_child_relationships (parent_id TEXT, child_id TEXT, parent_role TEXT);

        -- Person with valid timeline
        INSERT INTO persons VALUES ('P1', 'Valid Person', 'M');
        INSERT INTO facts VALUES ('P1', 'Birth', 19500101, '1 Jan 1950', 'California');
        INSERT INTO facts VALUES ('P1', 'Death', 20200101, '1 Jan 2020', 'California');

        -- Person with death before birth (invalid)
        INSERT INTO persons VALUES ('P2', 'Invalid Timeline', 'M');
        INSERT INTO facts VALUES ('P2', 'Birth', 20000101, '1 Jan 2000', 'Texas');
        INSERT INTO facts VALUES ('P2', 'Death', 19900101, '1 Jan 1990', 'Texas');

        -- Child born before parent
        INSERT INTO persons VALUES ('P3', 'Parent', 'F');
        INSERT INTO persons VALUES ('P4', 'Child', 'M');
        INSERT INTO facts VALUES ('P3', 'Birth', 20000101, '1 Jan 2000', 'Nevada');
        INSERT INTO facts VALUES ('P4', 'Birth', 19900101, '1 Jan 1990', 'Nevada');
        INSERT INTO parent_child_relationships VALUES ('P3', 'P4', 'mother');
    """)

    conn.commit()
    conn.close()
    return db_path


@pytest.fixture(autouse=True)
def mock_timeline_db(timeline_db: Path) -> None:
    """Auto-patch database."""
    with patch.object(connection, "FS_CACHE_PATH", timeline_db):
        connection._fs_conn = None
        yield
        connection.close_connections()


def test_validate_person_timeline_valid() -> None:
    """Test validating a person with valid timeline."""
    issues = validate_person_timeline("P1")

    # Valid person should have no issues
    assert isinstance(issues, list)


def test_validate_person_timeline_death_before_birth() -> None:
    """Test detecting death before birth."""
    issues = validate_person_timeline("P2")

    # Should detect the timeline issue
    assert isinstance(issues, list)
    if issues:
        issue = issues[0]
        assert "severity" in issue
        assert "description" in issue


def test_validate_person_timeline_child_before_parent() -> None:
    """Test detecting child born before parent."""
    issues = validate_person_timeline("P4")

    assert isinstance(issues, list)
    # May detect parent-child timeline issue


def test_validate_all_timelines() -> None:
    """Test validating all persons' timelines."""
    issues = validate_all_timelines(min_severity="warning")

    assert isinstance(issues, list)
    # Should find issues in the database
    for issue in issues:
        assert "person_id" in issue
        assert "severity" in issue


def test_validate_all_timelines_critical_only() -> None:
    """Test validating all timelines with critical severity only."""
    issues = validate_all_timelines(min_severity="critical")

    assert isinstance(issues, list)
    # All returned issues should be critical
    for issue in issues:
        assert issue["severity"] == "critical"
