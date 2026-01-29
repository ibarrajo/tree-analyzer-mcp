"""Detect potential duplicate persons using multiple criteria."""

from typing import Any

from db.queries import get_all_persons_with_names

from .name_disambiguation import compute_similarity_score


def find_likely_duplicates(threshold: float = 0.85) -> list[dict[str, Any]]:
    """
    Find persons that are very likely duplicates (high similarity threshold).

    Args:
        threshold: Similarity threshold (0-1, default 0.85 for likely duplicates)

    Returns:
        List of duplicate pairs with similarity scores
    """
    all_persons = get_all_persons_with_names()

    if len(all_persons) < 2:
        return []

    # Group by exact normalized name for fast duplicate detection
    name_groups: dict[str, list[dict[str, Any]]] = {}
    for person in all_persons:
        key = (person.get("normalized_surname", ""), person.get("normalized_given", ""))
        if key[0] or key[1]:
            name_groups.setdefault(key, []).append(person)

    duplicates = []

    # Check each group
    for group_persons in name_groups.values():
        if len(group_persons) < 2:
            continue

        # Compare all pairs in this name group
        for i in range(len(group_persons)):
            for j in range(i + 1, len(group_persons)):
                p1 = group_persons[i]
                p2 = group_persons[j]

                score = compute_similarity_score(p1, p2)
                if score >= threshold:
                    duplicates.append(
                        {
                            "person1_id": p1["person_id"],
                            "person1_name": p1.get("display_name", "Unknown"),
                            "person2_id": p2["person_id"],
                            "person2_name": p2.get("display_name", "Unknown"),
                            "similarity_score": round(score, 3),
                        }
                    )

    return sorted(duplicates, key=lambda x: x["similarity_score"], reverse=True)
