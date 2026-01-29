"""Tests for database queries module."""

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from db import connection, queries


@pytest.fixture
def test_db(tmp_path: Path) -> Path:
    """Create a test database with schema and sample data."""
    db_path = tmp_path / "test_cache.sqlite"
    conn = sqlite3.connect(str(db_path))

    # Create schema
    conn.executescript("""
        CREATE TABLE persons (
            person_id TEXT PRIMARY KEY,
            display_name TEXT,
            gender TEXT,
            raw_json TEXT
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

        CREATE TABLE sources (
            source_id TEXT PRIMARY KEY,
            title TEXT
        );

        CREATE TABLE person_source_refs (
            person_id TEXT,
            source_id TEXT,
            tag TEXT
        );
    """)

    # Insert test data
    conn.executescript("""
        -- Test persons
        INSERT INTO persons VALUES ('P1', 'John Doe', 'M', '{}');
        INSERT INTO persons VALUES ('P2', 'Jane Smith', 'F', '{}');
        INSERT INTO persons VALUES ('P3', 'Bob Johnson', 'M', '{}');
        INSERT INTO persons VALUES ('P4', 'Alice Doe', 'F', '{}');

        -- Names
        INSERT INTO person_names VALUES
            ('P1', 'BirthName', 'John', 'Doe', 'john', 'doe', 'J500', 'D000'),
            ('P2', 'BirthName', 'Jane', 'Smith', 'jane', 'smith', 'J500', 'S530'),
            ('P3', 'BirthName', 'Bob', 'Johnson', 'bob', 'johnson', 'B100', 'J525'),
            ('P4', 'BirthName', 'Alice', 'Doe', 'alice', 'doe', 'A420', 'D000');

        -- Facts
        INSERT INTO facts VALUES ('P1', 'Birth', 19500101, 'New York');
        INSERT INTO facts VALUES ('P1', 'Death', 20200101, 'California');
        INSERT INTO facts VALUES ('P2', 'Birth', 19520315, 'Boston');

        -- Relationships
        INSERT INTO parent_child_relationships VALUES ('P1', 'P4', 'father');
        INSERT INTO parent_child_relationships VALUES ('P2', 'P4', 'mother');
        INSERT INTO couple_relationships VALUES ('P1', 'P2', '1975-06-01', 'Nevada');

        -- Sources
        INSERT INTO sources VALUES ('S1', 'Birth Certificate');
        INSERT INTO sources VALUES ('S2', 'Death Certificate');
        INSERT INTO person_source_refs VALUES ('P1', 'S1', 'Birth');
        INSERT INTO person_source_refs VALUES ('P1', 'S2', 'Death');
    """)

    conn.commit()
    conn.close()
    return db_path


@pytest.fixture(autouse=True)
def mock_db_path(test_db: Path) -> None:
    """Automatically patch the FS_CACHE_PATH for all tests."""
    with patch.object(connection, "FS_CACHE_PATH", test_db):
        connection._fs_conn = None  # Reset connection
        yield
        connection.close_connections()


def test_get_person_by_id() -> None:
    """Test getting a person by ID."""
    person = queries.get_person_by_id("P1")
    assert person is not None
    assert person["person_id"] == "P1"
    assert person["display_name"] == "John Doe"
    assert person["gender"] == "M"


def test_get_person_by_id_not_found() -> None:
    """Test getting a non-existent person."""
    person = queries.get_person_by_id("NONEXISTENT")
    assert person is None


def test_get_person_names() -> None:
    """Test getting person names."""
    names = queries.get_person_names("P1")
    assert len(names) == 1
    assert names[0]["given_name"] == "John"
    assert names[0]["surname"] == "Doe"
    assert names[0]["normalized_given"] == "john"
    assert names[0]["soundex_given"] == "J500"


def test_get_person_names_empty() -> None:
    """Test getting names for person with no names."""
    names = queries.get_person_names("NONEXISTENT")
    assert names == []


def test_get_person_facts() -> None:
    """Test getting person facts."""
    facts = queries.get_person_facts("P1")
    assert len(facts) == 2
    # Facts should be ordered by date_sort
    assert facts[0]["fact_type"] == "Birth"
    assert facts[0]["date_sort"] == 19500101
    assert facts[1]["fact_type"] == "Death"


def test_get_person_facts_empty() -> None:
    """Test getting facts for person with no facts."""
    facts = queries.get_person_facts("P4")
    assert facts == []


def test_get_parents() -> None:
    """Test getting parents of a person."""
    parents = queries.get_parents("P4")
    assert len(parents) == 2
    parent_ids = {p["person_id"] for p in parents}
    assert "P1" in parent_ids
    assert "P2" in parent_ids
    assert any(p["parent_role"] == "father" for p in parents)
    assert any(p["parent_role"] == "mother" for p in parents)


def test_get_parents_empty() -> None:
    """Test getting parents for person with no parents."""
    parents = queries.get_parents("P1")
    assert parents == []


def test_get_children() -> None:
    """Test getting children of a person."""
    children = queries.get_children("P1")
    assert len(children) == 1
    assert children[0]["person_id"] == "P4"
    assert children[0]["parent_role"] == "father"


def test_get_children_empty() -> None:
    """Test getting children for person with no children."""
    children = queries.get_children("P3")
    assert children == []


def test_get_spouses() -> None:
    """Test getting spouses of a person."""
    spouses = queries.get_spouses("P1")
    assert len(spouses) == 1
    assert spouses[0]["person_id"] == "P2"
    assert spouses[0]["marriage_date"] == "1975-06-01"
    assert spouses[0]["marriage_place"] == "Nevada"


def test_get_spouses_reverse() -> None:
    """Test getting spouses works in reverse direction."""
    spouses = queries.get_spouses("P2")
    assert len(spouses) == 1
    assert spouses[0]["person_id"] == "P1"


def test_get_spouses_empty() -> None:
    """Test getting spouses for person with no spouses."""
    spouses = queries.get_spouses("P3")
    assert spouses == []


def test_get_person_sources() -> None:
    """Test getting sources for a person."""
    sources = queries.get_person_sources("P1")
    assert len(sources) == 2
    source_ids = {s["source_id"] for s in sources}
    assert "S1" in source_ids
    assert "S2" in source_ids
    tags = {s["tag"] for s in sources}
    assert "Birth" in tags
    assert "Death" in tags


def test_get_person_sources_empty() -> None:
    """Test getting sources for person with no sources."""
    sources = queries.get_person_sources("P3")
    assert sources == []


def test_get_all_persons_with_names() -> None:
    """Test getting all persons with names."""
    persons = queries.get_all_persons_with_names()
    assert len(persons) == 4
    # Check one person has correct structure
    john = next(p for p in persons if p["person_id"] == "P1")
    assert john["display_name"] == "John Doe"
    assert john["given_name"] == "John"
    assert john["surname"] == "Doe"
    assert john["normalized_given"] == "john"
    assert john["soundex_surname"] == "D000"


def test_get_persons_by_surname() -> None:
    """Test getting persons by surname."""
    doe_persons = queries.get_persons_by_surname("Doe")
    assert len(doe_persons) == 2
    person_ids = {p["person_id"] for p in doe_persons}
    assert "P1" in person_ids
    assert "P4" in person_ids


def test_get_persons_by_surname_partial() -> None:
    """Test getting persons by partial surname match."""
    persons = queries.get_persons_by_surname("mit")
    assert len(persons) == 1
    assert persons[0]["person_id"] == "P2"


def test_get_persons_by_surname_not_found() -> None:
    """Test getting persons by non-existent surname."""
    persons = queries.get_persons_by_surname("NotExists")
    assert persons == []


def test_get_persons_without_sources() -> None:
    """Test getting persons without sources."""
    persons = queries.get_persons_without_sources()
    assert len(persons) >= 2  # P2, P3, P4 have no sources
    person_ids = {p["person_id"] for p in persons}
    assert "P2" in person_ids
    assert "P3" in person_ids
    assert "P1" not in person_ids  # P1 has sources


def test_get_facts_without_sources() -> None:
    """Test getting facts without sources."""
    facts = queries.get_facts_without_sources()
    # P2's Birth fact has no source
    assert len(facts) >= 1
    birth_fact = next((f for f in facts if f["person_id"] == "P2"), None)
    assert birth_fact is not None
    assert birth_fact["fact_type"] == "Birth"
    assert birth_fact["display_name"] == "Jane Smith"
