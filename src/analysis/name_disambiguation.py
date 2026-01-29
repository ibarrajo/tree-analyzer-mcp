"""Name disambiguation using fuzzy matching and phonetic codes.

Tailored for Spanish/Latin American naming conventions with repeated family names.
"""

from typing import Any

import jellyfish
from rapidfuzz import fuzz

from db.queries import get_all_persons_with_names, get_parents, get_person_facts, get_spouses


def compute_similarity_score(person1: dict[str, Any], person2: dict[str, Any]) -> float:
    """
    Compute similarity score between two persons (0-1 scale).

    Breakdown:
    - Surname exact match: 0.25
    - Given name fuzzy (Jaro-Winkler + partial ratio): 0.20
    - Birth year proximity: 0.15
    - Birth place match: 0.10
    - Death year proximity: 0.10
    - Parent name match: 0.10
    - Spouse name match: 0.05
    - Source overlap: 0.05
    """
    score = 0.0

    # Surname match (exact normalized)
    if person1.get("normalized_surname") and person2.get("normalized_surname"):
        if person1["normalized_surname"] == person2["normalized_surname"]:
            score += 0.25
        else:
            # Partial credit for similar surnames
            similarity = (
                fuzz.ratio(person1["normalized_surname"], person2["normalized_surname"]) / 100
            )
            score += 0.25 * similarity

    # Given name fuzzy match
    if person1.get("normalized_given") and person2.get("normalized_given"):
        jw = jellyfish.jaro_winkler_similarity(
            person1["normalized_given"], person2["normalized_given"]
        )
        partial = fuzz.partial_ratio(person1["normalized_given"], person2["normalized_given"]) / 100
        given_score = (jw + partial) / 2
        score += 0.20 * given_score

    # Get facts for both persons
    facts1 = {f["fact_type"]: f for f in get_person_facts(person1["person_id"])}
    facts2 = {f["fact_type"]: f for f in get_person_facts(person2["person_id"])}

    # Birth year proximity
    birth1 = facts1.get("Birth")
    birth2 = facts2.get("Birth")
    if birth1 and birth2 and birth1.get("date_sort") and birth2.get("date_sort"):
        year1 = birth1["date_sort"] // 10000
        year2 = birth2["date_sort"] // 10000
        year_diff = abs(year1 - year2)
        if year_diff == 0:
            score += 0.15
        elif year_diff <= 2:
            score += 0.15 * (1 - year_diff / 10)

    # Birth place match
    if birth1 and birth2:
        place1 = (birth1.get("place_normalized") or "").lower()
        place2 = (birth2.get("place_normalized") or "").lower()
        if place1 and place2:
            if place1 == place2:
                score += 0.10
            else:
                # Partial credit for overlapping place components
                place_sim = fuzz.token_set_ratio(place1, place2) / 100
                score += 0.10 * place_sim

    # Death year proximity
    death1 = facts1.get("Death")
    death2 = facts2.get("Death")
    if death1 and death2 and death1.get("date_sort") and death2.get("date_sort"):
        year1 = death1["date_sort"] // 10000
        year2 = death2["date_sort"] // 10000
        year_diff = abs(year1 - year2)
        if year_diff == 0:
            score += 0.10
        elif year_diff <= 2:
            score += 0.10 * (1 - year_diff / 10)

    # Parent name match
    parents1 = get_parents(person1["person_id"])
    parents2 = get_parents(person2["person_id"])
    if parents1 and parents2:
        parent_names1 = {p["display_name"] for p in parents1}
        parent_names2 = {p["display_name"] for p in parents2}
        overlap = len(parent_names1 & parent_names2)
        if overlap > 0:
            score += 0.10 * (overlap / max(len(parent_names1), len(parent_names2)))

    # Spouse name match
    spouses1 = get_spouses(person1["person_id"])
    spouses2 = get_spouses(person2["person_id"])
    if spouses1 and spouses2:
        spouse_names1 = {s["display_name"] for s in spouses1}
        spouse_names2 = {s["display_name"] for s in spouses2}
        overlap = len(spouse_names1 & spouse_names2)
        if overlap > 0:
            score += 0.05 * (overlap / max(len(spouse_names1), len(spouse_names2)))

    # Note: Source overlap would require loading sources, skipping for now
    # Could add 0.05 here in future

    return min(score, 1.0)


def detect_name_clusters(
    surname_filter: str | None = None, similarity_threshold: float = 0.60
) -> list[dict[str, Any]]:
    """
    Detect clusters of potentially confused or duplicate persons.

    Uses Soundex/phonetic blocking to avoid O(n^2) comparisons, then scores pairs.
    Returns list of clusters, each containing list of similar persons.

    Args:
        surname_filter: Optional surname to focus on (e.g., "Ibarra")
        similarity_threshold: Minimum similarity score to group (0-1, default 0.60)

    Returns:
        List of clusters, each with: cluster_id, persons (with similarity scores)
    """
    # Get all persons
    all_persons = get_all_persons_with_names()

    if surname_filter:
        all_persons = [
            p
            for p in all_persons
            if p.get("surname") and surname_filter.lower() in p["surname"].lower()
        ]

    if len(all_persons) < 2:
        return []

    # Block by Soundex surname (avoids comparing everyone with everyone)
    soundex_blocks: dict[str, list[dict[str, Any]]] = {}
    for person in all_persons:
        soundex = person.get("soundex_surname", "")
        if soundex:
            soundex_blocks.setdefault(soundex, []).append(person)

    # Find similar pairs within each block
    similar_pairs: list[tuple[str, str, float]] = []

    for block_persons in soundex_blocks.values():
        if len(block_persons) < 2:
            continue

        for i in range(len(block_persons)):
            for j in range(i + 1, len(block_persons)):
                p1 = block_persons[i]
                p2 = block_persons[j]

                # Don't compare person to themselves
                if p1["person_id"] == p2["person_id"]:
                    continue

                score = compute_similarity_score(p1, p2)
                if score >= similarity_threshold:
                    similar_pairs.append((p1["person_id"], p2["person_id"], score))

    # Cluster using Union-Find
    clusters = _cluster_pairs(similar_pairs, all_persons)

    return clusters


def _cluster_pairs(
    pairs: list[tuple[str, str, float]], all_persons: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Group similar pairs into clusters using Union-Find."""
    if not pairs:
        return []

    # Union-Find parent mapping
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        if x not in parent:
            parent[x] = x
        if parent[x] != x:
            parent[x] = find(parent[x])  # Path compression
        return parent[x]

    def union(x: str, y: str):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    # Build clusters
    for p1_id, p2_id, _score in pairs:
        union(p1_id, p2_id)

    # Group by root
    cluster_members: dict[str, list[str]] = {}
    for person_id in parent.keys():
        root = find(person_id)
        cluster_members.setdefault(root, []).append(person_id)

    # Build output
    person_map = {p["person_id"]: p for p in all_persons}
    result = []

    for cluster_id, (root, members) in enumerate(cluster_members.items()):
        if len(members) < 2:
            continue

        cluster_persons = []
        for member_id in members:
            person = person_map.get(member_id)
            if person:
                # Compute score vs representative (root)
                if member_id == root:
                    score = 1.0
                else:
                    score = compute_similarity_score(person_map[root], person)

                cluster_persons.append(
                    {
                        "person_id": member_id,
                        "display_name": person.get("display_name", "Unknown"),
                        "similarity_score": round(score, 3),
                    }
                )

        result.append(
            {
                "cluster_id": cluster_id,
                "size": len(cluster_persons),
                "persons": sorted(
                    cluster_persons, key=lambda x: x["similarity_score"], reverse=True
                ),
            }
        )

    return sorted(result, key=lambda x: x["size"], reverse=True)
