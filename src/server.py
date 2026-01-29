#!/usr/bin/env python3
"""Tree Analyzer MCP Server - Analysis and reporting for family tree data."""

import json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from tools.analysis_tools import (
    tool_analyze_source_coverage,
    tool_check_relationships,
    tool_compare_persons,
    tool_detect_name_duplicates,
    tool_find_duplicates,
    tool_validate_timeline,
)
from tools.report_tools import (
    tool_generate_audit_report,
    tool_generate_name_clusters_report,
    tool_generate_person_profile,
    tool_generate_research_leads,
)

# Create server instance
app = Server("tree-analyzer-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    return [
        Tool(
            name="detect_name_duplicates",
            description="Detect clusters of persons with similar names (potential duplicates or confused persons)",
            inputSchema={
                "type": "object",
                "properties": {
                    "surname_filter": {
                        "type": "string",
                        "description": "Optional surname to focus on (e.g., 'Ibarra')",
                    },
                    "similarity_threshold": {
                        "type": "number",
                        "description": "Minimum similarity score (0-1, default 0.60)",
                        "default": 0.60,
                        "minimum": 0.0,
                        "maximum": 1.0,
                    },
                },
            },
        ),
        Tool(
            name="validate_timeline",
            description="Validate timeline plausibility (birth before death, reasonable ages)",
            inputSchema={
                "type": "object",
                "properties": {
                    "person_id": {
                        "type": "string",
                        "description": "Specific person to validate (if omitted, validates all)",
                    },
                    "min_severity": {
                        "type": "string",
                        "description": "Minimum severity to include",
                        "enum": ["critical", "warning", "info"],
                        "default": "warning",
                    },
                },
            },
        ),
        Tool(
            name="check_relationships",
            description="Check relationship structure (circular ancestry, multiple parents, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "person_id": {"type": "string", "description": "Person to analyze"},
                    "check_types": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["circular", "structure"]},
                        "description": "Types of checks to perform",
                    },
                },
                "required": ["person_id"],
            },
        ),
        Tool(
            name="analyze_source_coverage",
            description="Analyze source coverage and identify persons/events missing sources",
            inputSchema={
                "type": "object",
                "properties": {
                    "root_person_id": {"type": "string", "description": "Root person of tree"},
                    "min_sources_per_person": {
                        "type": "integer",
                        "description": "Minimum acceptable sources per person",
                        "default": 1,
                        "minimum": 0,
                    },
                },
                "required": ["root_person_id"],
            },
        ),
        Tool(
            name="find_duplicates",
            description="Find likely duplicate persons (very high similarity)",
            inputSchema={
                "type": "object",
                "properties": {
                    "threshold": {
                        "type": "number",
                        "description": "Similarity threshold (0-1, default 0.85)",
                        "default": 0.85,
                        "minimum": 0.0,
                        "maximum": 1.0,
                    }
                },
            },
        ),
        Tool(
            name="compare_persons",
            description="Deep comparison of two persons to determine if they are duplicates",
            inputSchema={
                "type": "object",
                "properties": {
                    "person_id_a": {"type": "string", "description": "First person ID"},
                    "person_id_b": {"type": "string", "description": "Second person ID"},
                },
                "required": ["person_id_a", "person_id_b"],
            },
        ),
        Tool(
            name="generate_person_profile",
            description="Generate a detailed Markdown profile for a single person",
            inputSchema={
                "type": "object",
                "properties": {
                    "person_id": {"type": "string", "description": "FamilySearch person ID"}
                },
                "required": ["person_id"],
            },
        ),
        Tool(
            name="generate_audit_report",
            description="Generate a comprehensive tree audit report",
            inputSchema={
                "type": "object",
                "properties": {
                    "root_person_id": {"type": "string", "description": "Root person for the tree"},
                    "generations": {
                        "type": "integer",
                        "description": "Number of generations to analyze",
                        "default": 4,
                        "minimum": 1,
                        "maximum": 10,
                    },
                },
                "required": ["root_person_id"],
            },
        ),
        Tool(
            name="generate_name_clusters_report",
            description="Generate a report of name duplicate clusters",
            inputSchema={
                "type": "object",
                "properties": {
                    "surname_filter": {
                        "type": "string",
                        "description": "Optional surname to focus on",
                    },
                    "similarity_threshold": {
                        "type": "number",
                        "description": "Minimum similarity score",
                        "default": 0.60,
                        "minimum": 0.0,
                        "maximum": 1.0,
                    },
                },
            },
        ),
        Tool(
            name="generate_research_leads",
            description="Generate prioritized research leads report",
            inputSchema={
                "type": "object",
                "properties": {
                    "root_person_id": {"type": "string", "description": "Root person for analysis"},
                    "focus_area": {
                        "type": "string",
                        "description": "Focus area",
                        "enum": ["all", "sources", "records"],
                        "default": "all",
                    },
                },
                "required": ["root_person_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    try:
        result = None

        if name == "detect_name_duplicates":
            result = tool_detect_name_duplicates(
                surname_filter=arguments.get("surname_filter"),
                similarity_threshold=arguments.get("similarity_threshold", 0.60),
            )
        elif name == "validate_timeline":
            result = tool_validate_timeline(
                person_id=arguments.get("person_id"),
                min_severity=arguments.get("min_severity", "warning"),
            )
        elif name == "check_relationships":
            result = tool_check_relationships(
                person_id=arguments["person_id"], check_types=arguments.get("check_types")
            )
        elif name == "analyze_source_coverage":
            result = tool_analyze_source_coverage(
                root_person_id=arguments["root_person_id"],
                min_sources_per_person=arguments.get("min_sources_per_person", 1),
            )
        elif name == "find_duplicates":
            result = tool_find_duplicates(threshold=arguments.get("threshold", 0.85))
        elif name == "compare_persons":
            result = tool_compare_persons(
                person_id_a=arguments["person_id_a"], person_id_b=arguments["person_id_b"]
            )
        elif name == "generate_person_profile":
            result = tool_generate_person_profile(person_id=arguments["person_id"])
        elif name == "generate_audit_report":
            result = tool_generate_audit_report(
                root_person_id=arguments["root_person_id"],
                generations=arguments.get("generations", 4),
            )
        elif name == "generate_name_clusters_report":
            result = tool_generate_name_clusters_report(
                surname_filter=arguments.get("surname_filter"),
                similarity_threshold=arguments.get("similarity_threshold", 0.60),
            )
        elif name == "generate_research_leads":
            result = tool_generate_research_leads(
                root_person_id=arguments["root_person_id"],
                focus_area=arguments.get("focus_area", "all"),
            )
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
