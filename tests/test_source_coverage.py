"""Tests for source coverage analysis."""

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from analysis.source_coverage import analyze_person_source_coverage, prioritize_source_research
from db import connection


@pytest.fixture
def source_db(tmp_path: Path) -> Path:
    """Create test database with source information."""
    db_path = tmp_path / "source.sqlite"
    conn = sqlite3.connect(str(db_path))

    conn.executescript("""
        CREATE TABLE persons (person_id TEXT PRIMARY KEY, display_name TEXT, gender TEXT);
        CREATE TABLE person_names (person_id TEXT, name_type TEXT, given_name TEXT, surname TEXT,
            normalized_given TEXT, normalized_surname TEXT, soundex_given TEXT, soundex_surname TEXT);
        CREATE TABLE facts (person_id TEXT, fact_type TEXT, date_sort INTEGER, place_normalized TEXT);
        CREATE TABLE parent_child_relationships (parent_id TEXT, child_id TEXT, parent_role TEXT);
        CREATE TABLE sources (source_id TEXT PRIMARY KEY, title TEXT);
        CREATE TABLE person_source_refs (person_id TEXT, source_id TEXT, tag TEXT);

        INSERT INTO persons VALUES ('P1', 'With Sources', 'M'), ('P2', 'No Sources', 'F');
        INSERT INTO person_names VALUES
            ('P1', 'BirthName', 'John', 'Doe', 'john', 'doe', 'J500', 'D000'),
            ('P2', 'BirthName', 'Jane', 'Smith', 'jane', 'smith', 'J500', 'S530');
        INSERT INTO facts VALUES
            ('P1', 'Birth', 19500101, 'California'),
            ('P1', 'Death', 20200101, 'California'),
            ('P2', 'Birth', 19520101, 'Texas');
        INSERT INTO sources VALUES ('S1', 'Birth Certificate');
        INSERT INTO person_source_refs VALUES ('P1', 'S1', 'Birth');
        INSERT INTO parent_child_relationships VALUES ('P1', 'P2', 'father');
    """)

    conn.commit()
    conn.close()
    return db_path


@pytest.fixture(autouse=True)
def mock_source_db(source_db: Path) -> None:
    """Auto-patch database."""
    with patch.object(connection, "FS_CACHE_PATH", source_db):
        connection._fs_conn = None
        yield
        connection.close_connections()


def test_analyze_person_source_coverage() -> None:
    """Test analyzing source coverage for a person."""
    coverage = analyze_person_source_coverage("P1")

    assert "person_id" in coverage
    assert coverage["person_id"] == "P1"
    assert "total_sources" in coverage
    assert "total_facts" in coverage
    assert "vital_facts_with_sources" in coverage


def test_analyze_person_source_coverage_no_sources() -> None:
    """Test analyzing person with no sources."""
    coverage = analyze_person_source_coverage("P2")

    assert coverage["person_id"] == "P2"
    assert coverage["total_sources"] == 0


def test_prioritize_source_research() -> None:
    """Test prioritizing source research."""
    priorities = prioritize_source_research(root_person_id="P1", generations=2)

    assert isinstance(priorities, list)
    # Should identify persons needing sources
    if priorities:
        priority = priorities[0]
        assert "person_id" in priority
        assert "priority_score" in priority
        assert isinstance(priority["priority_score"], (int, float))
