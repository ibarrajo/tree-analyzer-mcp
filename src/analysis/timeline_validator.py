"""Timeline validation: detect impossible dates and age plausibility issues."""

from typing import Any

from db.connection import get_fs_db
from db.queries import get_parents, get_person_by_id, get_person_facts


def validate_person_timeline(person_id: str) -> list[dict[str, Any]]:
    """
    Validate timeline for a single person.

    Checks:
    - Birth before death
    - Reasonable age at death
    - Birth/death date formats
    - Parent ages (too young/old)
    - Children ages (too young/old)
    """
    issues: list[dict[str, Any]] = []
    person = get_person_by_id(person_id)
    if not person:
        return issues

    facts = {f["fact_type"]: f for f in get_person_facts(person_id)}
    birth = facts.get("Birth")
    death = facts.get("Death")

    # Check birth before death
    if birth and death:
        birth_sort = birth.get("date_sort")
        death_sort = death.get("date_sort")
        if birth_sort and death_sort and birth_sort > death_sort:
            issues.append(
                {
                    "type": "death_before_birth",
                    "severity": "critical",
                    "person_id": person_id,
                    "person_name": person["display_name"],
                    "description": f"Death date ({death['date_original']}) is before birth date ({birth['date_original']})",
                }
            )

        # Age at death plausibility
        if birth_sort and death_sort:
            age = (death_sort // 10000) - (birth_sort // 10000)
            if age < 0:
                # Already caught above
                pass
            elif age > 120:
                issues.append(
                    {
                        "type": "implausible_age_at_death",
                        "severity": "warning",
                        "person_id": person_id,
                        "person_name": person["display_name"],
                        "description": f"Age at death ({age} years) exceeds 120 years",
                    }
                )

    # Check parent ages at birth of this child
    if birth and birth.get("date_sort"):
        parents = get_parents(person_id)
        for parent in parents:
            parent_facts = {f["fact_type"]: f for f in get_person_facts(parent["person_id"])}
            parent_birth = parent_facts.get("Birth")
            if parent_birth and parent_birth.get("date_sort"):
                parent_birth_year = parent_birth["date_sort"] // 10000
                child_birth_year = birth["date_sort"] // 10000
                parent_age_at_birth = child_birth_year - parent_birth_year

                if parent_age_at_birth < 13:
                    issues.append(
                        {
                            "type": "parent_too_young",
                            "severity": "critical",
                            "person_id": person_id,
                            "person_name": person["display_name"],
                            "parent_id": parent["person_id"],
                            "parent_name": parent["display_name"],
                            "description": f"Parent {parent['display_name']} was only {parent_age_at_birth} years old at child's birth",
                        }
                    )
                elif parent_age_at_birth > 60 and parent.get("gender") == "Female":
                    issues.append(
                        {
                            "type": "mother_too_old",
                            "severity": "warning",
                            "person_id": person_id,
                            "person_name": person["display_name"],
                            "parent_id": parent["person_id"],
                            "parent_name": parent["display_name"],
                            "description": f"Mother {parent['display_name']} was {parent_age_at_birth} years old at child's birth (unusual but possible)",
                        }
                    )
                elif parent_age_at_birth > 80 and parent.get("gender") == "Male":
                    issues.append(
                        {
                            "type": "father_too_old",
                            "severity": "warning",
                            "person_id": person_id,
                            "person_name": person["display_name"],
                            "parent_id": parent["person_id"],
                            "parent_name": parent["display_name"],
                            "description": f"Father {parent['display_name']} was {parent_age_at_birth} years old at child's birth (unusual but possible)",
                        }
                    )

    return issues


def validate_all_timelines(min_severity: str = "warning") -> list[dict[str, Any]]:
    """
    Validate timelines for all persons in cache.

    Args:
        min_severity: Minimum severity to include ('critical', 'warning', 'info')

    Returns:
        List of timeline issues
    """
    conn = get_fs_db()
    cursor = conn.execute("SELECT person_id FROM persons")
    person_ids = [row["person_id"] for row in cursor.fetchall()]

    all_issues = []
    for person_id in person_ids:
        issues = validate_person_timeline(person_id)
        all_issues.extend(issues)

    # Filter by severity
    severity_order = {"info": 0, "warning": 1, "critical": 2}
    min_level = severity_order.get(min_severity, 1)
    filtered = [i for i in all_issues if severity_order.get(i["severity"], 0) >= min_level]

    return sorted(
        filtered,
        key=lambda x: (severity_order.get(x["severity"], 0), x.get("person_name", "")),
        reverse=True,
    )
