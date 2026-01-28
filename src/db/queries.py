"""Prebuilt SQL queries for tree analysis."""

from typing import List, Dict, Any
from .connection import get_fs_db


def get_person_by_id(person_id: str) -> Dict[str, Any] | None:
    """Get person by FamilySearch ID."""
    conn = get_fs_db()
    cursor = conn.execute(
        "SELECT * FROM persons WHERE person_id = ?",
        (person_id,)
    )
    row = cursor.fetchone()
    return dict(row) if row else None


def get_person_names(person_id: str) -> List[Dict[str, Any]]:
    """Get all name forms for a person."""
    conn = get_fs_db()
    cursor = conn.execute(
        "SELECT * FROM person_names WHERE person_id = ?",
        (person_id,)
    )
    return [dict(row) for row in cursor.fetchall()]


def get_person_facts(person_id: str) -> List[Dict[str, Any]]:
    """Get all facts/events for a person."""
    conn = get_fs_db()
    cursor = conn.execute(
        "SELECT * FROM facts WHERE person_id = ? ORDER BY date_sort",
        (person_id,)
    )
    return [dict(row) for row in cursor.fetchall()]


def get_parents(person_id: str) -> List[Dict[str, Any]]:
    """Get parents of a person."""
    conn = get_fs_db()
    cursor = conn.execute("""
        SELECT p.*, pcr.parent_role
        FROM persons p
        JOIN parent_child_relationships pcr ON p.person_id = pcr.parent_id
        WHERE pcr.child_id = ?
    """, (person_id,))
    return [dict(row) for row in cursor.fetchall()]


def get_children(person_id: str) -> List[Dict[str, Any]]:
    """Get children of a person."""
    conn = get_fs_db()
    cursor = conn.execute("""
        SELECT p.*, pcr.parent_role
        FROM persons p
        JOIN parent_child_relationships pcr ON p.person_id = pcr.child_id
        WHERE pcr.parent_id = ?
    """, (person_id,))
    return [dict(row) for row in cursor.fetchall()]


def get_spouses(person_id: str) -> List[Dict[str, Any]]:
    """Get spouses of a person."""
    conn = get_fs_db()
    cursor = conn.execute("""
        SELECT p.*, cr.marriage_date, cr.marriage_place
        FROM persons p
        JOIN couple_relationships cr ON (
            (cr.person1_id = ? AND cr.person2_id = p.person_id) OR
            (cr.person2_id = ? AND cr.person1_id = p.person_id)
        )
        WHERE p.person_id != ?
    """, (person_id, person_id, person_id))
    return [dict(row) for row in cursor.fetchall()]


def get_person_sources(person_id: str) -> List[Dict[str, Any]]:
    """Get sources attached to a person."""
    conn = get_fs_db()
    cursor = conn.execute("""
        SELECT s.*, psr.tag
        FROM sources s
        JOIN person_source_refs psr ON s.source_id = psr.source_id
        WHERE psr.person_id = ?
    """, (person_id,))
    return [dict(row) for row in cursor.fetchall()]


def get_all_persons_with_names() -> List[Dict[str, Any]]:
    """Get all persons with their primary names."""
    conn = get_fs_db()
    cursor = conn.execute("""
        SELECT p.person_id, p.display_name, p.gender,
               pn.given_name, pn.surname, pn.normalized_given, pn.normalized_surname,
               pn.soundex_given, pn.soundex_surname
        FROM persons p
        LEFT JOIN person_names pn ON p.person_id = pn.person_id AND pn.name_type = 'BirthName'
    """)
    return [dict(row) for row in cursor.fetchall()]


def get_persons_by_surname(surname: str) -> List[Dict[str, Any]]:
    """Get all persons with a given surname (fuzzy match)."""
    conn = get_fs_db()
    cursor = conn.execute("""
        SELECT DISTINCT p.*
        FROM persons p
        JOIN person_names pn ON p.person_id = pn.person_id
        WHERE pn.surname LIKE ?
    """, (f"%{surname}%",))
    return [dict(row) for row in cursor.fetchall()]


def get_persons_without_sources() -> List[Dict[str, Any]]:
    """Get persons that have no source citations."""
    conn = get_fs_db()
    cursor = conn.execute("""
        SELECT p.*
        FROM persons p
        WHERE NOT EXISTS (
            SELECT 1 FROM person_source_refs psr WHERE psr.person_id = p.person_id
        )
    """)
    return [dict(row) for row in cursor.fetchall()]


def get_facts_without_sources() -> List[Dict[str, Any]]:
    """Get facts that have no supporting sources."""
    conn = get_fs_db()
    cursor = conn.execute("""
        SELECT f.*, p.display_name
        FROM facts f
        JOIN persons p ON f.person_id = p.person_id
        WHERE NOT EXISTS (
            SELECT 1 FROM person_source_refs psr
            WHERE psr.person_id = f.person_id AND psr.tag = f.fact_type
        )
        AND f.fact_type IN ('Birth', 'Death', 'Marriage', 'Burial')
    """)
    return [dict(row) for row in cursor.fetchall()]
