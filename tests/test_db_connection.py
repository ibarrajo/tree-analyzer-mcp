"""Tests for database connection module."""

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from db import connection


@pytest.fixture
def mock_fs_db(tmp_path: Path) -> Path:
    """Create a temporary FamilySearch database."""
    db_path = tmp_path / "cache.sqlite"
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE persons (
            person_id TEXT PRIMARY KEY,
            display_name TEXT
        )
    """)
    conn.execute("INSERT INTO persons VALUES ('TEST-123', 'Test Person')")
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def mock_sources_db(tmp_path: Path) -> Path:
    """Create a temporary sources database."""
    db_path = tmp_path / "sources-cache.sqlite"
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE external_matches (
            id INTEGER PRIMARY KEY,
            source_name TEXT
        )
    """)
    conn.execute("INSERT INTO external_matches VALUES (1, 'wikitree')")
    conn.commit()
    conn.close()
    return db_path


def test_get_fs_db(mock_fs_db: Path) -> None:
    """Test getting FamilySearch database connection."""
    with patch.object(connection, "FS_CACHE_PATH", mock_fs_db):
        # Reset the global connection
        connection._fs_conn = None

        conn = connection.get_fs_db()
        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)

        # Test row factory is set
        cursor = conn.execute("SELECT * FROM persons")
        row = cursor.fetchone()
        assert row["person_id"] == "TEST-123"
        assert row["display_name"] == "Test Person"


def test_get_sources_db(mock_sources_db: Path) -> None:
    """Test getting sources database connection."""
    with patch.object(connection, "SOURCES_CACHE_PATH", mock_sources_db):
        # Reset the global connection
        connection._sources_conn = None

        conn = connection.get_sources_db()
        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)

        # Test row factory is set
        cursor = conn.execute("SELECT * FROM external_matches")
        row = cursor.fetchone()
        assert row["source_name"] == "wikitree"


def test_get_fs_db_reuses_connection(mock_fs_db: Path) -> None:
    """Test that get_fs_db reuses existing connection."""
    with patch.object(connection, "FS_CACHE_PATH", mock_fs_db):
        connection._fs_conn = None

        conn1 = connection.get_fs_db()
        conn2 = connection.get_fs_db()

        assert conn1 is conn2


def test_get_sources_db_reuses_connection(mock_sources_db: Path) -> None:
    """Test that get_sources_db reuses existing connection."""
    with patch.object(connection, "SOURCES_CACHE_PATH", mock_sources_db):
        connection._sources_conn = None

        conn1 = connection.get_sources_db()
        conn2 = connection.get_sources_db()

        assert conn1 is conn2


def test_close_connections(mock_fs_db: Path, mock_sources_db: Path) -> None:
    """Test closing all database connections."""
    with (
        patch.object(connection, "FS_CACHE_PATH", mock_fs_db),
        patch.object(connection, "SOURCES_CACHE_PATH", mock_sources_db),
    ):
        connection._fs_conn = None
        connection._sources_conn = None

        # Open connections
        connection.get_fs_db()
        connection.get_sources_db()

        # Close them
        connection.close_connections()

        # Verify they're closed by checking the global variables
        assert connection._fs_conn is None
        assert connection._sources_conn is None
