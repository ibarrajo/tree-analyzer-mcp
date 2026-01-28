"""MCP tools for report generation."""

from typing import Dict, Any
from ..reports.generator import (
    generate_person_profile,
    generate_audit_report,
    generate_name_clusters_report,
    generate_research_leads,
)


def tool_generate_person_profile(person_id: str) -> Dict[str, Any]:
    """
    Generate a detailed Markdown profile for a single person.

    Args:
        person_id: FamilySearch person ID
    """
    output_file = generate_person_profile(person_id)
    return {
        'person_id': person_id,
        'output_file': output_file,
        'message': f'Profile generated at {output_file}',
    }


def tool_generate_audit_report(
    root_person_id: str,
    generations: int = 4
) -> Dict[str, Any]:
    """
    Generate a comprehensive tree audit report.

    Args:
        root_person_id: Root person for the tree
        generations: Number of generations to analyze
    """
    output_file = generate_audit_report(root_person_id, generations)
    return {
        'root_person_id': root_person_id,
        'generations': generations,
        'output_file': output_file,
        'message': f'Audit report generated at {output_file}',
    }


def tool_generate_name_clusters_report(
    surname_filter: str | None = None,
    similarity_threshold: float = 0.60
) -> Dict[str, Any]:
    """
    Generate a report of name duplicate clusters.

    Args:
        surname_filter: Optional surname to focus on
        similarity_threshold: Minimum similarity score
    """
    output_file = generate_name_clusters_report(surname_filter, similarity_threshold)
    return {
        'surname_filter': surname_filter or 'All',
        'threshold': similarity_threshold,
        'output_file': output_file,
        'message': f'Name clusters report generated at {output_file}',
    }


def tool_generate_research_leads(
    root_person_id: str,
    focus_area: str = 'all'
) -> Dict[str, Any]:
    """
    Generate prioritized research leads report.

    Args:
        root_person_id: Root person for analysis
        focus_area: Focus area ('all', 'sources', 'records')
    """
    output_file = generate_research_leads(root_person_id, focus_area)
    return {
        'root_person_id': root_person_id,
        'focus_area': focus_area,
        'output_file': output_file,
        'message': f'Research leads report generated at {output_file}',
    }
