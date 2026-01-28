"""Database connection module for accessing both FamilySearch and research sources caches."""

import sqlite3
from pathlib import Path
from typing import Optional

# Database paths
FS_CACHE_PATH = Path(__file__).parent.parent.parent.parent / "familysearch-mcp" / "data" / "cache.sqlite"
SOURCES_CACHE_PATH = Path(__file__).parent.parent.parent.parent / "research-sources-mcp" / "data" / "sources-cache.sqlite"

_fs_conn: Optional[sqlite3.Connection] = None
_sources_conn: Optional[sqlite3.Connection] = None


def get_fs_db() -> sqlite3.Connection:
    """Get connection to FamilySearch cache database."""
    global _fs_conn
    if _fs_conn is None:
        _fs_conn = sqlite3.connect(str(FS_CACHE_PATH))
        _fs_conn.row_factory = sqlite3.Row
    return _fs_conn


def get_sources_db() -> sqlite3.Connection:
    """Get connection to research sources cache database."""
    global _sources_conn
    if _sources_conn is None:
        _sources_conn = sqlite3.connect(str(SOURCES_CACHE_PATH))
        _sources_conn.row_factory = sqlite3.Row
    return _sources_conn


def close_connections():
    """Close all database connections."""
    global _fs_conn, _sources_conn
    if _fs_conn:
        _fs_conn.close()
        _fs_conn = None
    if _sources_conn:
        _sources_conn.close()
        _sources_conn = None
