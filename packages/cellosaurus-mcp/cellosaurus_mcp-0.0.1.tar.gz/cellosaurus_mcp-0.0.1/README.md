# Cellosaurus MCP Server

[![BioContextAI - Registry](https://img.shields.io/badge/Registry-package?style=flat&label=BioContextAI&labelColor=%23fff&color=%233555a1&link=https%3A%2F%2Fbiocontext.ai%2Fregistry)](https://biocontext.ai/registry)
[![Tests][badge-tests]][tests]
[![Documentation][badge-docs]][documentation]

[badge-tests]: https://img.shields.io/github/actions/workflow/status/biocontext-ai/unofficial-cellosaurus-mcp/test.yaml?branch=main
[badge-docs]: https://img.shields.io/readthedocs/unofficial-cellosaurus-mcp

An unofficial Model Context Protocol (MCP) server for the SIB Cellosaurus cell line knowledge resource.

## About Cellosaurus

[Cellosaurus](https://www.cellosaurus.org) is a comprehensive knowledge resource on cell lines developed by the CALIPHO group at the SIB Swiss Institute of Bioinformatics. It provides detailed information about:

- Immortalized cell lines used in biomedical research
- Cell line characteristics, genetics, and metadata
- Cross-references to databases and publications
- STR profiles for authentication
- Disease associations and tissue origins

**License Notice**: The Cellosaurus database is made available under the [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) license. When using data from Cellosaurus, please provide appropriate attribution to the Cellosaurus team and cite their work.

## Features

This MCP server provides the following tools for accessing Cellosaurus data:

### Core Tools

- **`search_cell_lines`**: Search for cell lines using flexible Solr syntax
- **`get_cell_line_info`**: Get detailed information about a specific cell line by accession
- **`get_release_info`**: Get current database version and statistics

### Specialized Search Tools

- **`find_cell_lines_by_disease`**: Find cell lines associated with specific diseases
- **`find_cell_lines_by_tissue`**: Find cell lines derived from specific tissues/organs
- **`list_available_fields`**: Get all available data fields and their descriptions

### Example Queries

```python
# Search for HeLa cell lines
search_cell_lines(query="id:HeLa", fields=["id", "ac", "ox", "di"])

# Find liver cancer cell lines
find_cell_lines_by_disease(disease="hepatocellular carcinoma", species="human")

# Find all liver-derived cell lines
find_cell_lines_by_tissue(tissue="liver", species="human")

# Get detailed info for a specific cell line
get_cell_line_info(accession="CVCL_0030", fields=["id", "str", "karyotype"])
```

## Installation

You need to have Python 3.11 or newer installed on your system.

### Option 1: Using uvx (recommended)

```bash
uvx cellosaurus_mcp
```

### Option 2: MCP Client Configuration

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "cellosaurus": {
      "command": "uvx",
      "args": ["cellosaurus_mcp"],
      "env": {
        "UV_PYTHON": "3.11"
      }
    }
  }
}
```

### Option 3: Direct Installation

```bash
pip install cellosaurus_mcp
```

## Contact

If you found a bug, please use the [issue tracker][].

## Citation

> t.b.a

[uv]: https://github.com/astral-sh/uv
[issue tracker]: https://github.com/biocontext-ai/unofficial-cellosaurus-mcp/issues
[tests]: https://github.com/biocontext-ai/unofficial-cellosaurus-mcp/actions/workflows/test.yaml
[documentation]: https://unofficial-cellosaurus-mcp.readthedocs.io
[changelog]: https://unofficial-cellosaurus-mcp.readthedocs.io/en/latest/changelog.html
[api documentation]: https://unofficial-cellosaurus-mcp.readthedocs.io/en/latest/api.html
[pypi]: https://pypi.org/project/unofficial-cellosaurus-mcp
