"""MCP tools for tree analysis."""

from typing import Any

from analysis.duplicate_detector import find_likely_duplicates
from analysis.name_disambiguation import detect_name_clusters
from analysis.relationship_checker import (
    check_relationship_structure,
    detect_circular_ancestry,
)
from analysis.source_coverage import prioritize_source_research
from analysis.timeline_validator import validate_all_timelines, validate_person_timeline
from db.queries import get_person_by_id


def tool_detect_name_duplicates(
    surname_filter: str | None = None, similarity_threshold: float = 0.60
) -> dict[str, Any]:
    """
    Detect clusters of persons with similar names (potential duplicates or confused persons).

    Args:
        surname_filter: Optional surname to focus on (e.g., "Ibarra")
        similarity_threshold: Minimum similarity score (0-1, default 0.60)
    """
    clusters = detect_name_clusters(surname_filter, similarity_threshold)
    return {
        "surname_filter": surname_filter or "All",
        "threshold": similarity_threshold,
        "cluster_count": len(clusters),
        "clusters": clusters,
    }


def tool_validate_timeline(
    person_id: str | None = None, min_severity: str = "warning"
) -> dict[str, Any]:
    """
    Validate timeline for plausibility (birth before death, reasonable ages, etc.).

    Args:
        person_id: Specific person to validate (if None, validates all cached persons)
        min_severity: Minimum severity to include ('critical', 'warning', 'info')
    """
    if person_id:
        issues = validate_person_timeline(person_id)
        person = get_person_by_id(person_id)
        return {
            "person_id": person_id,
            "person_name": person.get("display_name") if person else "Unknown",
            "issue_count": len(issues),
            "issues": issues,
        }
    else:
        issues = validate_all_timelines(min_severity)
        return {
            "scope": "all_persons",
            "min_severity": min_severity,
            "issue_count": len(issues),
            "issues": issues,
        }


def tool_check_relationships(
    person_id: str, check_types: list[str] | None = None
) -> dict[str, Any]:
    """
    Check relationship structure for issues (circular ancestry, multiple parents, etc.).

    Args:
        person_id: Person to analyze
        check_types: Types of checks ('circular', 'structure', or both if None)
    """
    check_types = check_types or ["circular", "structure"]
    issues = []

    if "circular" in check_types:
        issues.extend(detect_circular_ancestry(person_id))

    if "structure" in check_types:
        issues.extend(check_relationship_structure(person_id))

    person = get_person_by_id(person_id)
    return {
        "person_id": person_id,
        "person_name": person.get("display_name") if person else "Unknown",
        "check_types": check_types,
        "issue_count": len(issues),
        "issues": issues,
    }


def tool_analyze_source_coverage(
    root_person_id: str, min_sources_per_person: int = 1
) -> dict[str, Any]:
    """
    Analyze source coverage for a tree and identify persons/events missing sources.

    Args:
        root_person_id: Root person of tree
        min_sources_per_person: Minimum acceptable sources per person
    """
    priorities = prioritize_source_research(root_person_id, generations=5)

    # Filter to those below minimum
    below_minimum = [p for p in priorities if p["total_sources"] < min_sources_per_person]

    return {
        "root_person_id": root_person_id,
        "min_sources": min_sources_per_person,
        "total_analyzed": len(priorities),
        "below_minimum_count": len(below_minimum),
        "below_minimum": below_minimum[:50],
        "top_priorities": priorities[:20],
    }


def tool_find_duplicates(threshold: float = 0.85) -> dict[str, Any]:
    """
    Find likely duplicate persons (very high similarity).

    Args:
        threshold: Similarity threshold (0-1, default 0.85 for likely duplicates)
    """
    duplicates = find_likely_duplicates(threshold)
    return {
        "threshold": threshold,
        "duplicate_count": len(duplicates),
        "duplicates": duplicates,
    }


def tool_compare_persons(person_id_a: str, person_id_b: str) -> dict[str, Any]:
    """
    Deep comparison of two persons to help determine if they are duplicates.

    Args:
        person_id_a: First person ID
        person_id_b: Second person ID
    """
    from analysis.name_disambiguation import compute_similarity_score
    from db.queries import (
        get_parents,
        get_person_facts,
        get_person_names,
        get_person_sources,
        get_spouses,
    )

    person_a = get_person_by_id(person_id_a)
    person_b = get_person_by_id(person_id_b)

    if not person_a or not person_b:
        return {"error": "One or both persons not found"}

    # Get all data for comparison
    names_a = get_person_names(person_id_a)
    names_b = get_person_names(person_id_b)
    facts_a = get_person_facts(person_id_a)
    facts_b = get_person_facts(person_id_b)
    parents_a = get_parents(person_id_a)
    parents_b = get_parents(person_id_b)
    spouses_a = get_spouses(person_id_a)
    spouses_b = get_spouses(person_id_b)
    sources_a = get_person_sources(person_id_a)
    sources_b = get_person_sources(person_id_b)

    # Compute similarity score
    # Need to create a dict format compatible with compute_similarity_score
    p_a_dict = {
        "person_id": person_id_a,
        "display_name": person_a["display_name"],
        "normalized_given": names_a[0]["normalized_given"] if names_a else "",
        "normalized_surname": names_a[0]["normalized_surname"] if names_a else "",
    }
    p_b_dict = {
        "person_id": person_id_b,
        "display_name": person_b["display_name"],
        "normalized_given": names_b[0]["normalized_given"] if names_b else "",
        "normalized_surname": names_b[0]["normalized_surname"] if names_b else "",
    }

    similarity = compute_similarity_score(p_a_dict, p_b_dict)

    return {
        "person_a": {
            "id": person_id_a,
            "name": person_a["display_name"],
            "names": names_a,
            "facts": facts_a,
            "parents": [p["display_name"] for p in parents_a],
            "spouses": [s["display_name"] for s in spouses_a],
            "source_count": len(sources_a),
        },
        "person_b": {
            "id": person_id_b,
            "name": person_b["display_name"],
            "names": names_b,
            "facts": facts_b,
            "parents": [p["display_name"] for p in parents_b],
            "spouses": [s["display_name"] for s in spouses_b],
            "source_count": len(sources_b),
        },
        "similarity_score": round(similarity, 3),
        "likely_duplicate": similarity >= 0.85,
    }
