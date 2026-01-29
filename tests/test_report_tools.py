"""Tests for report generation tools."""

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from db import connection
from tools.report_tools import tool_generate_person_profile


@pytest.fixture
def report_db(tmp_path: Path) -> Path:
    """Create test database for reports."""
    db_path = tmp_path / "report.sqlite"
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

        INSERT INTO persons VALUES ('P1', 'Test Person', 'M');
        INSERT INTO person_names VALUES
            ('P1', 'BirthName', 'Test', 'Person', 'test', 'person', 'T230', 'P625');
        INSERT INTO facts VALUES ('P1', 'Birth', 19500101, 'California');
        INSERT INTO sources VALUES ('S1', 'Birth Certificate');
        INSERT INTO person_source_refs VALUES ('P1', 'S1', 'Birth');
    """)

    conn.commit()
    conn.close()
    return db_path


@pytest.fixture(autouse=True)
def mock_report_db(report_db: Path) -> None:
    """Auto-patch database."""
    with patch.object(connection, "FS_CACHE_PATH", report_db):
        connection._fs_conn = None
        yield
        connection.close_connections()


def test_tool_generate_person_profile() -> None:
    """Test generating a person profile."""
    result = tool_generate_person_profile(person_id="P1")

    assert "person_id" in result
    assert result["person_id"] == "P1"
    assert "output_file" in result
    assert isinstance(result["output_file"], str)
    assert result["output_file"].endswith(".md")
    assert "message" in result
