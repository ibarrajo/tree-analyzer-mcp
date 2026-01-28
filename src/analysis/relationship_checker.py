"""Relationship structure validation: detect circular ancestry and structural issues."""

from typing import List, Dict, Any, Set
from ..db.queries import get_parents, get_children, get_spouses
from ..db.connection import get_fs_db


def detect_circular_ancestry(person_id: str, max_depth: int = 20) -> List[Dict[str, Any]]:
    """
    Detect circular ancestry (person is their own ancestor).

    Uses DFS with cycle detection.
    """
    issues = []
    visited = set()
    path = []

    def dfs(current_id: str, depth: int) -> bool:
        if depth > max_depth:
            return False

        if current_id in path:
            # Found a cycle
            cycle_start = path.index(current_id)
            cycle = path[cycle_start:] + [current_id]
            issues.append({
                'type': 'circular_ancestry',
                'severity': 'critical',
                'person_id': person_id,
                'description': f"Circular ancestry detected: {' -> '.join(cycle)}",
                'cycle': cycle,
            })
            return True

        if current_id in visited:
            return False

        visited.add(current_id)
        path.append(current_id)

        # Check parents
        parents = get_parents(current_id)
        for parent in parents:
            if dfs(parent['person_id'], depth + 1):
                return True

        path.pop()
        return False

    dfs(person_id, 0)
    return issues


def check_relationship_structure(person_id: str) -> List[Dict[str, Any]]:
    """
    Check for structural issues in relationships.

    Checks:
    - Person has more than 2 biological parents
    - Spouse relationships without gender distinction
    - Multiple marriages with overlapping dates
    """
    issues = []

    # Check parent count
    parents = get_parents(person_id)
    if len(parents) > 2:
        issues.append({
            'type': 'too_many_parents',
            'severity': 'warning',
            'person_id': person_id,
            'description': f"Person has {len(parents)} parents (expected 0-2)",
        })

    # Check for gender consistency in parent relationships
    mothers = [p for p in parents if p.get('gender') == 'Female']
    fathers = [p for p in parents if p.get('gender') == 'Male']
    if len(mothers) > 1:
        issues.append({
            'type': 'multiple_mothers',
            'severity': 'warning',
            'person_id': person_id,
            'description': f"Person has {len(mothers)} mothers listed",
        })
    if len(fathers) > 1:
        issues.append({
            'type': 'multiple_fathers',
            'severity': 'warning',
            'person_id': person_id,
            'description': f"Person has {len(fathers)} fathers listed",
        })

    # Check spouse relationships
    spouses = get_spouses(person_id)
    if len(spouses) > 1:
        # Check for overlapping marriage dates
        marriages = []
        for spouse in spouses:
            if spouse.get('marriage_date'):
                marriages.append(spouse)

        # Simple overlap check (would need date range parsing for complete check)
        # For now just flag if there are multiple concurrent spouses
        if len(marriages) > 1:
            issues.append({
                'type': 'multiple_concurrent_marriages',
                'severity': 'info',
                'person_id': person_id,
                'description': f"Person has {len(spouses)} spouses (may need timeline verification)",
            })

    return issues


def validate_relationships_for_tree(root_person_id: str, max_persons: int = 1000) -> List[Dict[str, Any]]:
    """
    Validate relationships for a tree rooted at a person.

    Checks circular ancestry and structural issues for all persons in the tree.
    """
    # Collect all person IDs in tree (BFS from root)
    to_visit = [root_person_id]
    visited = set()
    all_issues = []

    while to_visit and len(visited) < max_persons:
        current = to_visit.pop(0)
        if current in visited:
            continue
        visited.add(current)

        # Check for issues
        all_issues.extend(detect_circular_ancestry(current))
        all_issues.extend(check_relationship_structure(current))

        # Add relatives to visit
        for parent in get_parents(current):
            if parent['person_id'] not in visited:
                to_visit.append(parent['person_id'])
        for child in get_children(current):
            if child['person_id'] not in visited:
                to_visit.append(child['person_id'])
        for spouse in get_spouses(current):
            if spouse['person_id'] not in visited:
                to_visit.append(spouse['person_id'])

    return all_issues
