"""Report generator using Jinja2 templates."""

from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from analysis.duplicate_detector import find_likely_duplicates
from analysis.name_disambiguation import detect_name_clusters
from analysis.relationship_checker import validate_relationships_for_tree
from analysis.source_coverage import prioritize_source_research
from analysis.timeline_validator import validate_all_timelines
from db.queries import (
    get_parents,
    get_person_by_id,
    get_person_facts,
    get_person_sources,
    get_spouses,
)

from .links import person_url

TEMPLATE_DIR = Path(__file__).parent / "templates"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "reports"

# Ensure output directory exists
OUTPUT_DIR.mkdir(exist_ok=True)

# Setup Jinja2 environment
env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)

# Add custom filters
env.filters["person_url"] = person_url


def generate_person_profile(person_id: str) -> str:
    """Generate detailed profile report for a single person."""
    person = get_person_by_id(person_id)
    if not person:
        return f"Person {person_id} not found"

    facts = get_person_facts(person_id)
    parents = get_parents(person_id)
    spouses = get_spouses(person_id)
    sources = get_person_sources(person_id)

    context = {
        "person": person,
        "facts": facts,
        "parents": parents,
        "spouses": spouses,
        "sources": sources,
        "generated_at": datetime.now().isoformat(),
    }

    template = env.get_template("person_profile.md.j2")
    content = template.render(context)

    output_file = OUTPUT_DIR / f"person_{person_id}.md"
    output_file.write_text(content)

    return str(output_file)


def generate_audit_report(root_person_id: str, generations: int = 4) -> str:
    """Generate comprehensive audit report for a tree."""
    root_person = get_person_by_id(root_person_id)
    if not root_person:
        return f"Root person {root_person_id} not found"

    # Collect all analysis results
    timeline_issues = validate_all_timelines(min_severity="warning")
    relationship_issues = validate_relationships_for_tree(root_person_id, max_persons=500)
    source_priorities = prioritize_source_research(root_person_id, generations)
    duplicates = find_likely_duplicates(threshold=0.85)

    # Count by severity
    critical_count = len(
        [i for i in timeline_issues + relationship_issues if i.get("severity") == "critical"]
    )
    warning_count = len(
        [i for i in timeline_issues + relationship_issues if i.get("severity") == "warning"]
    )

    context = {
        "root_person": root_person,
        "generations": generations,
        "timeline_issues": timeline_issues,
        "relationship_issues": relationship_issues,
        "source_priorities": source_priorities[:50],  # Top 50
        "duplicates": duplicates[:20],  # Top 20
        "critical_count": critical_count,
        "warning_count": warning_count,
        "generated_at": datetime.now().isoformat(),
    }

    template = env.get_template("full_audit.md.j2")
    content = template.render(context)

    output_file = (
        OUTPUT_DIR / f"audit_{root_person_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    )
    output_file.write_text(content)

    return str(output_file)


def generate_name_clusters_report(
    surname_filter: str | None = None, threshold: float = 0.60
) -> str:
    """Generate report of name duplicate clusters."""
    clusters = detect_name_clusters(surname_filter, threshold)

    context = {
        "surname_filter": surname_filter or "All",
        "threshold": threshold,
        "clusters": clusters,
        "total_clusters": len(clusters),
        "generated_at": datetime.now().isoformat(),
    }

    template = env.get_template("name_clusters.md.j2")
    content = template.render(context)

    surname_suffix = f"_{surname_filter}" if surname_filter else "_all"
    output_file = (
        OUTPUT_DIR / f"name_clusters{surname_suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    )
    output_file.write_text(content)

    return str(output_file)


def generate_research_leads(root_person_id: str, focus_area: str = "all") -> str:
    """Generate prioritized research leads report."""
    source_priorities = prioritize_source_research(root_person_id, generations=5)

    context = {
        "root_person_id": root_person_id,
        "focus_area": focus_area,
        "priorities": source_priorities[:30],  # Top 30
        "generated_at": datetime.now().isoformat(),
    }

    template = env.get_template("research_leads.md.j2")
    content = template.render(context)

    output_file = (
        OUTPUT_DIR
        / f"research_leads_{root_person_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    )
    output_file.write_text(content)

    return str(output_file)
