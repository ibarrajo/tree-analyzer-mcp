# Tree Analyzer MCP Server

> Family tree analysis and error detection for Claude Code via MCP

Analyze genealogy trees for errors, duplicates, timeline issues, and missing sources through Claude's Model Context Protocol.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- 🔍 **Name Disambiguation** - Detect duplicate persons using fuzzy matching and phonetic algorithms (Soundex, NYSIIS, Metaphone)
- ⏱️ **Timeline Validation** - Find impossible dates, age issues, and chronological errors
- 🔗 **Relationship Checker** - Detect circular ancestry and structural tree problems
- 📊 **Source Coverage** - Identify persons and events missing source citations
- 📝 **Report Generation** - Create detailed Markdown reports with FamilySearch links
- 🧬 **Spanish Name Support** - Optimized for Spanish/Latin American naming patterns

## Installation

### Via Claude Desktop

Add to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "tree-analyzer": {
      "command": "python",
      "args": ["-m", "tree_analyzer_mcp.server"],
      "cwd": "/path/to/tree-analyzer-mcp-standalone"
    }
  }
}
```

### Via Docker

```bash
docker run -v /path/to/data:/app/data tree-analyzer-mcp
```

### From Source

```bash
git clone https://github.com/YOUR_USERNAME/tree-analyzer-mcp
cd tree-analyzer-mcp
pip install -e .
```

## Tools Available

| Tool | Description |
|------|-------------|
| `detect_name_duplicates` | Find potential duplicate persons using fuzzy name matching |
| `validate_timeline` | Check for impossible dates, age issues, parent-child age gaps |
| `check_relationships` | Detect circular ancestry and structural tree problems |
| `analyze_source_coverage` | Find persons and events missing source citations |
| `generate_person_profile` | Create detailed Markdown profile for a person |
| `generate_audit_report` | Comprehensive tree audit with all issues and statistics |
| `generate_research_leads` | Prioritized next-steps for genealogy research |
| `compare_persons` | Deep comparison of two persons to identify duplicates |

## Usage Examples

### Detect Duplicate Names

Ask Claude Code:
```
Find potential duplicate persons in my family tree
```

Claude will use:
```python
detect_name_duplicates(
    surname_filter="Smith",  # Optional: focus on specific surname
    similarity_threshold=0.8
)
```

### Validate Timeline

Ask Claude Code:
```
Check my family tree for timeline errors and impossible dates
```

Claude will use:
```python
validate_timeline(
    person_id=None,  # None = check entire tree
    max_parent_age=60,
    min_parent_age=14
)
```

### Generate Audit Report

Ask Claude Code:
```
Create a comprehensive audit report for my 8-generation tree starting with person GK1Y-97Y
```

Claude will use:
```python
generate_audit_report(
    root_person_id="GK1Y-97Y",
    generations=8,
    sections=["all"]
)
```

### Find Missing Sources

Ask Claude Code:
```
Which ancestors are missing source citations?
```

Claude will use:
```python
analyze_source_coverage(
    root_person_id="GK1Y-97Y",
    min_sources_per_person=1
)
```

## Development

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/tree-analyzer-mcp
cd tree-analyzer-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html

# Lint code
ruff check src
black --check src
mypy src

# Format code
black src
ruff check --fix src
```

## Architecture

- **Python 3.11+** - Modern Python with type hints
- **FastMCP** - Official Model Context Protocol framework for Python
- **SQLite** - Local database access (reads from familysearch-mcp cache)
- **Fuzzy Matching** - RapidFuzz for name similarity
- **Phonetic Coding** - Soundex, NYSIIS, Metaphone for name variants
- **Jinja2** - Report templating

### Data Flow

```
Claude Code
    ↓
MCP Protocol (stdio)
    ↓
tree-analyzer-mcp (Python)
    ↓
┌──────────────────┬──────────────────┐
│ familysearch-mcp │ research-sources │
│   cache.sqlite   │   -cache.sqlite  │
└──────────────────┴──────────────────┘
    ↓
Analysis & Reports
```

### Name Disambiguation Algorithm

Optimized for Spanish/Latin American naming conventions:

1. **Normalize**: Remove accents, lowercase, strip particles (de, del, y)
2. **Expand**: Ma. → Maria, Fco. → Francisco, Jph → Joseph
3. **Index**: Compute Soundex, NYSIIS, Metaphone codes
4. **Block**: Match candidates via phonetic codes (avoids O(n²))
5. **Score**: Multi-factor similarity (0-1):
   - Surname exact: 0.25
   - Given name fuzzy: 0.20
   - Birth year proximity: 0.15
   - Birth place: 0.10
   - Death year proximity: 0.10
   - Parent names: 0.10
   - Spouse names: 0.05
   - Source overlap: 0.05
6. **Cluster**: Union-Find algorithm for grouping
7. **Output**: Disambiguation tables with timeline overlap

## Tool Reference

### `detect_name_duplicates`

Find potential duplicate persons using fuzzy matching.

**Parameters:**
- `surname_filter` (optional): Focus on specific surname
- `similarity_threshold` (optional): Minimum similarity score (0.0-1.0, default 0.75)

**Returns:** Markdown report with name clusters and similarity scores

### `validate_timeline`

Check for impossible dates and age issues.

**Parameters:**
- `person_id` (optional): Check specific person (None = entire tree)
- `max_parent_age` (optional): Maximum age for having children (default 60)
- `min_parent_age` (optional): Minimum age for having children (default 14)
- `max_lifespan` (optional): Maximum human lifespan (default 120)

**Returns:** Markdown report with timeline errors and recommendations

### `check_relationships`

Detect structural tree problems.

**Parameters:**
- `person_id` (optional): Starting person (None = check all)
- `check_types` (optional): Types of checks ["circular", "orphans", "marriages"]

**Returns:** Markdown report with relationship issues

### `analyze_source_coverage`

Find persons and events missing sources.

**Parameters:**
- `root_person_id` (required): Starting person for analysis
- `generations` (optional): Number of generations to analyze (default 8)
- `min_sources_per_person` (optional): Minimum sources required (default 1)

**Returns:** Markdown report prioritized by generation proximity

### `generate_person_profile`

Create detailed profile for one person.

**Parameters:**
- `person_id` (required): FamilySearch person ID

**Returns:** Markdown profile with all facts, relationships, sources

### `generate_audit_report`

Comprehensive tree audit report.

**Parameters:**
- `root_person_id` (required): Starting person
- `generations` (optional): Depth to analyze (default 8)
- `sections` (optional): Sections to include (default ["all"])

**Returns:** Full Markdown audit with statistics, issues, recommendations

### `generate_research_leads`

Prioritized research suggestions.

**Parameters:**
- `root_person_id` (required): Starting person
- `focus_area` (optional): "missing_sources", "timeline_errors", "duplicates"

**Returns:** Markdown report with actionable next steps

### `compare_persons`

Deep comparison of two persons.

**Parameters:**
- `person_id_a` (required): First person ID
- `person_id_b` (required): Second person ID

**Returns:** Markdown comparison table with similarity score

## Report Output

All reports are Markdown format with:

- **Executive summary** with issue counts by severity
- **FamilySearch links** for all persons (`https://www.familysearch.org/tree/person/details/{PID}`)
- **Actionable recommendations** with specific next steps
- **Statistics** (person counts, source coverage, etc.)
- **Tables** for easy scanning of issues

Example report sections:
- Critical issues (circular ancestry, impossible dates)
- Name duplicate clusters with similarity scores
- Missing sources by generation
- Timeline validation results
- Research leads with collection suggestions

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Credits

Built as part of the FamilySearch genealogy research system. Part of a suite of MCP servers:

- [familysearch-mcp](https://github.com/YOUR_USERNAME/familysearch-mcp) - FamilySearch API integration
- **tree-analyzer-mcp** - Family tree analysis and error detection (this repository)
- [research-sources-mcp](https://github.com/ibarrajo/research-sources-mcp) - External source search

## Links

- [MCP Protocol Documentation](https://modelcontextprotocol.io/)
- [FastMCP Framework](https://github.com/modelcontextprotocol/python-sdk)
- [FamilySearch Developer](https://www.familysearch.org/developers/)

## Support

- [Issues](https://github.com/YOUR_USERNAME/tree-analyzer-mcp/issues)
- [Discussions](https://github.com/YOUR_USERNAME/tree-analyzer-mcp/discussions)
