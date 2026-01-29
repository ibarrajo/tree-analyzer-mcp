"""Tests for name disambiguation module."""

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from analysis.name_disambiguation import compute_similarity_score, detect_name_clusters
from db import connection


@pytest.fixture
def name_test_db(tmp_path: Path) -> Path:
    """Create a test database with persons having similar names."""
    db_path = tmp_path / "name_test.sqlite"
    conn = sqlite3.connect(str(db_path))

    conn.executescript("""
        CREATE TABLE persons (
            person_id TEXT PRIMARY KEY,
            display_name TEXT,
            gender TEXT
        );

        CREATE TABLE person_names (
            person_id TEXT,
            name_type TEXT,
            given_name TEXT,
            surname TEXT,
            normalized_given TEXT,
            normalized_surname TEXT,
            soundex_given TEXT,
            soundex_surname TEXT
        );

        CREATE TABLE facts (
            person_id TEXT,
            fact_type TEXT,
            date_sort INTEGER,
            place_normalized TEXT
        );

        CREATE TABLE parent_child_relationships (
            parent_id TEXT,
            child_id TEXT,
            parent_role TEXT
        );

        CREATE TABLE couple_relationships (
            person1_id TEXT,
            person2_id TEXT,
            marriage_date TEXT,
            marriage_place TEXT
        );

        CREATE TABLE person_source_refs (
            person_id TEXT,
            source_id TEXT
        );

        -- Very similar persons (likely duplicates)
        INSERT INTO persons VALUES ('P1', 'John Smith', 'M');
        INSERT INTO persons VALUES ('P2', 'John Smith', 'M');
        INSERT INTO persons VALUES ('P3', 'Jose Garcia', 'M');
        INSERT INTO persons VALUES ('P4', 'Joseph Garcia', 'M');

        INSERT INTO person_names VALUES
            ('P1', 'BirthName', 'John', 'Smith', 'john', 'smith', 'J500', 'S530'),
            ('P2', 'BirthName', 'John', 'Smith', 'john', 'smith', 'J500', 'S530'),
            ('P3', 'BirthName', 'Jose', 'Garcia', 'jose', 'garcia', 'J200', 'G620'),
            ('P4', 'BirthName', 'Joseph', 'Garcia', 'joseph', 'garcia', 'J210', 'G620');

        INSERT INTO facts VALUES
            ('P1', 'Birth', 19500101, 'California'),
            ('P2', 'Birth', 19500315, 'California'),
            ('P3', 'Birth', 19600101, 'Mexico'),
            ('P4', 'Birth', 19590901, 'Mexico');
    """)

    conn.commit()
    conn.close()
    return db_path


@pytest.fixture(autouse=True)
def mock_name_db(name_test_db: Path) -> None:
    """Automatically patch the database for name tests."""
    with patch.object(connection, "FS_CACHE_PATH", name_test_db):
        connection._fs_conn = None
        yield
        connection.close_connections()


def test_compute_similarity_score_exact_match() -> None:
    """Test similarity score for exact matches."""
    person1 = {"person_id": "P1", "normalized_surname": "smith", "normalized_given": "john"}
    person2 = {"person_id": "P2", "normalized_surname": "smith", "normalized_given": "john"}

    score = compute_similarity_score(person1, person2)
    # Should have high score for exact name match
    assert score >= 0.40  # At least surname + given name


def test_compute_similarity_score_similar_names() -> None:
    """Test similarity score for similar but not identical names."""
    person1 = {"person_id": "P3", "normalized_surname": "garcia", "normalized_given": "jose"}
    person2 = {"person_id": "P4", "normalized_surname": "garcia", "normalized_given": "joseph"}

    score = compute_similarity_score(person1, person2)
    # Should have moderate to high score (same surname, similar given names and dates/places)
    assert 0.40 < score < 0.80


def test_compute_similarity_score_different_names() -> None:
    """Test similarity score for completely different names."""
    person1 = {"person_id": "P1", "normalized_surname": "smith", "normalized_given": "john"}
    person2 = {"person_id": "P3", "normalized_surname": "garcia", "normalized_given": "jose"}

    score = compute_similarity_score(person1, person2)
    # Should have low score for different names
    assert score < 0.25


def test_compute_similarity_score_missing_names() -> None:
    """Test similarity score when names are missing."""
    person1 = {"person_id": "P1"}
    person2 = {"person_id": "P2"}

    score = compute_similarity_score(person1, person2)
    # Score should still be calculated (will be low due to missing data)
    assert 0.0 <= score <= 1.0


def test_detect_name_clusters() -> None:
    """Test detecting name duplicate clusters."""
    clusters = detect_name_clusters(surname_filter=None, similarity_threshold=0.40)

    # Should find at least one cluster
    assert len(clusters) > 0

    # Check cluster structure
    cluster = clusters[0]
    assert "cluster_id" in cluster
    assert "size" in cluster
    assert "persons" in cluster
    assert cluster["size"] >= 2
    assert len(cluster["persons"]) >= 2


def test_detect_name_clusters_with_surname_filter() -> None:
    """Test detecting clusters with surname filter."""
    clusters = detect_name_clusters(surname_filter="Smith", similarity_threshold=0.40)

    # Should find Smith cluster
    assert len(clusters) > 0

    # All persons should have Smith surname in display name
    for cluster in clusters:
        for person in cluster["persons"]:
            assert "Smith" in person["display_name"]


def test_detect_name_clusters_high_threshold() -> None:
    """Test detecting clusters with high threshold."""
    # High threshold should find only very similar matches
    clusters = detect_name_clusters(surname_filter=None, similarity_threshold=0.90)

    # Might find fewer or no clusters
    assert isinstance(clusters, list)
    # If clusters exist, they should have very high similarity
    for cluster in clusters:
        assert cluster["size"] >= 2


def test_detect_name_clusters_low_threshold() -> None:
    """Test detecting clusters with low threshold."""
    # Low threshold should find more matches
    clusters = detect_name_clusters(surname_filter=None, similarity_threshold=0.10)

    # Should find more clusters with low threshold
    assert len(clusters) > 0
