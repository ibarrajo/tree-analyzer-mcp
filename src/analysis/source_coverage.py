"""Analyze source coverage and identify persons/events missing sources."""

from typing import Any

from db.queries import (
    get_parents,
    get_person_by_id,
    get_person_facts,
    get_person_sources,
)


def analyze_person_source_coverage(person_id: str) -> dict[str, Any]:
    """
    Analyze source coverage for a single person.

    Returns:
        Dict with total_sources, facts_with_sources, facts_without_sources, priority_score
    """
    person = get_person_by_id(person_id)
    if not person:
        return {}

    sources = get_person_sources(person_id)
    facts = get_person_facts(person_id)

    # Map sources to fact types
    source_tags = {s["tag"] for s in sources if s.get("tag")}

    # Categorize facts by importance
    vital_facts = ["Birth", "Death", "Christening", "Burial"]
    important_facts = ["Marriage", "Residence", "Census"]

    vital_events = [f for f in facts if f["fact_type"] in vital_facts]
    important_events = [f for f in facts if f["fact_type"] in important_facts]

    vital_with_sources = [f for f in vital_events if f["fact_type"] in source_tags]
    vital_without_sources = [f for f in vital_events if f["fact_type"] not in source_tags]

    important_with_sources = [f for f in important_events if f["fact_type"] in source_tags]
    important_without_sources = [f for f in important_events if f["fact_type"] not in source_tags]

    return {
        "person_id": person_id,
        "person_name": person["display_name"],
        "total_sources": len(sources),
        "total_facts": len(facts),
        "vital_facts_with_sources": len(vital_with_sources),
        "vital_facts_without_sources": len(vital_without_sources),
        "important_facts_with_sources": len(important_with_sources),
        "important_facts_without_sources": len(important_without_sources),
        "missing_vital_events": vital_without_sources,
        "missing_important_events": important_without_sources,
    }


def prioritize_source_research(root_person_id: str, generations: int = 4) -> list[dict[str, Any]]:
    """
    Generate prioritized list of persons needing source research.

    Priority factors:
    - Proximity to root person (closer = higher priority)
    - Number of vital facts without sources
    - Total number of facts without sources

    Returns:
        Sorted list of persons with priority scores
    """
    # BFS to collect persons by generation
    to_visit = [(root_person_id, 0)]
    visited = set()
    person_priorities = []

    while to_visit:
        current_id, gen = to_visit.pop(0)
        if current_id in visited or gen > generations:
            continue
        visited.add(current_id)

        # Analyze coverage
        coverage = analyze_person_source_coverage(current_id)
        if not coverage:
            continue

        # Calculate priority score
        # Closer generation = higher base score
        generation_score = (generations - gen + 1) * 10

        # More missing vital facts = higher score
        vital_missing_score = coverage["vital_facts_without_sources"] * 5

        # More missing important facts = moderate score
        important_missing_score = coverage["important_facts_without_sources"] * 2

        # No sources at all = bonus
        no_sources_bonus = 10 if coverage["total_sources"] == 0 else 0

        priority_score = (
            generation_score + vital_missing_score + important_missing_score + no_sources_bonus
        )

        if priority_score > 0:
            person_priorities.append(
                {
                    "person_id": current_id,
                    "person_name": coverage["person_name"],
                    "generation": gen,
                    "priority_score": priority_score,
                    "total_sources": coverage["total_sources"],
                    "vital_missing": coverage["vital_facts_without_sources"],
                    "important_missing": coverage["important_facts_without_sources"],
                    "missing_events": [f["fact_type"] for f in coverage["missing_vital_events"]]
                    + [f["fact_type"] for f in coverage["missing_important_events"]],
                }
            )

        # Add parents to visit
        parents = get_parents(current_id)
        for parent in parents:
            if parent["person_id"] not in visited:
                to_visit.append((parent["person_id"], gen + 1))

    return sorted(person_priorities, key=lambda x: x["priority_score"], reverse=True)
