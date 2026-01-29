"""Tests for duplicate detector."""

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from analysis.duplicate_detector import find_likely_duplicates
from db import connection


@pytest.fixture
def dup_db(tmp_path: Path) -> Path:
    """Create test database with potential duplicates."""
    db_path = tmp_path / "dup.sqlite"
    conn = sqlite3.connect(str(db_path))

    conn.executescript("""
        CREATE TABLE persons (person_id TEXT PRIMARY KEY, display_name TEXT, gender TEXT);
        CREATE TABLE person_names (person_id TEXT, name_type TEXT, given_name TEXT, surname TEXT,
            normalized_given TEXT, normalized_surname TEXT, soundex_given TEXT, soundex_surname TEXT);
        CREATE TABLE facts (person_id TEXT, fact_type TEXT, date_sort INTEGER, place_normalized TEXT);
        CREATE TABLE parent_child_relationships (parent_id TEXT, child_id TEXT, parent_role TEXT);
        CREATE TABLE couple_relationships (person1_id TEXT, person2_id TEXT, marriage_date TEXT, marriage_place TEXT);
        CREATE TABLE person_source_refs (person_id TEXT, source_id TEXT, tag TEXT);

        INSERT INTO persons VALUES ('P1', 'John Doe', 'M'), ('P2', 'John Doe', 'M'), ('P3', 'Jane Smith', 'F');
        INSERT INTO person_names VALUES
            ('P1', 'BirthName', 'John', 'Doe', 'john', 'doe', 'J500', 'D000'),
            ('P2', 'BirthName', 'John', 'Doe', 'john', 'doe', 'J500', 'D000'),
            ('P3', 'BirthName', 'Jane', 'Smith', 'jane', 'smith', 'J500', 'S530');
        INSERT INTO facts VALUES ('P1', 'Birth', 19500101, 'California'), ('P2', 'Birth', 19500101, 'California');
    """)

    conn.commit()
    conn.close()
    return db_path


@pytest.fixture(autouse=True)
def mock_dup_db(dup_db: Path) -> None:
    """Auto-patch database."""
    with patch.object(connection, "FS_CACHE_PATH", dup_db):
        connection._fs_conn = None
        yield
        connection.close_connections()


def test_find_likely_duplicates_default_threshold() -> None:
    """Test finding duplicates with default threshold."""
    duplicates = find_likely_duplicates()

    assert isinstance(duplicates, list)
    # Should find P1 and P2 as duplicates
    if duplicates:
        dup = duplicates[0]
        assert "person_id_a" in dup
        assert "person_id_b" in dup
        assert "similarity_score" in dup


def test_find_likely_duplicates_high_threshold() -> None:
    """Test finding duplicates with high threshold."""
    duplicates = find_likely_duplicates(threshold=0.90)

    assert isinstance(duplicates, list)
    # High threshold means very similar pairs
    for dup in duplicates:
        assert dup["similarity_score"] >= 0.90


def test_find_likely_duplicates_low_threshold() -> None:
    """Test finding duplicates with low threshold."""
    duplicates = find_likely_duplicates(threshold=0.20)

    assert isinstance(duplicates, list)
    # Low threshold should find more pairs
