# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python AzViz is a Python implementation of the PowerShell AzViz module for generating Azure resource topology diagrams. It discovers Azure resources, maps their relationships, and creates visual diagrams using NetworkX and Graphviz.

## Development Commands

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Development installation (editable)
pip install -e .

# Install development dependencies
pip install -e .[dev]
```

### Running the Application
```bash
# Direct execution from source
python azviz.py --help
python azviz.py export --resource-group my-rg

# After installation
python-azviz --help
python-azviz export --resource-group my-rg

# HTML output for interactive diagrams
python-azviz export --format html --output topology.html
```

### Code Quality Tools
```bash
# Format code
black src/ examples/ azviz.py

# Lint code
ruff check src/ examples/ azviz.py

# Type checking
mypy src/azviz/
```

### Testing
```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=azviz tests/
```

## Architecture Overview

### Core Components

1. **AzViz Main Class** (`src/azviz/core/azviz.py`)
   - Primary interface for diagram generation
   - Orchestrates Azure client, graph building, and rendering
   - Handles authentication and prerequisite validation

2. **Azure Client** (`src/azviz/azure/client.py`) 
   - Manages Azure API interactions using Azure SDK
   - Discovers resources and network topology
   - Handles authentication via DefaultAzureCredential

3. **Visualization Pipeline**:
   - **GraphBuilder** (`src/azviz/visualization/graph_builder.py`) - Creates NetworkX graph from Azure resources
   - **DOTGenerator** (`src/azviz/visualization/dot_generator.py`) - Converts graph to Graphviz DOT format
   - **GraphRenderer** (`src/azviz/visualization/renderer.py`) - Renders DOT to PNG/SVG/HTML using Graphviz

4. **Data Models** (`src/azviz/core/models.py`)
   - Defines enums for themes, formats, directions
   - AzureResource and NetworkTopology dataclasses
   - Configuration models using Pydantic

5. **CLI Interface** (`src/azviz/cli.py`)
   - Click-based command interface with Rich for formatting
   - Commands: export, list-rg, preview, validate, info
   - Global and command-level subscription ID support

6. **Icon Management** (`src/azviz/icons/icon_manager.py`)
   - Maps Azure resource types to service icons
   - 40+ Azure service icons in `src/azviz/icons/azure_icons/`

### Key Design Patterns

- **Configuration-driven**: VisualizationConfig object drives entire pipeline
- **Layered architecture**: Clear separation between Azure API, graph logic, and rendering
- **Flexible authentication**: Supports Azure CLI, service principal, managed identity
- **Theme system**: Light, dark, and neon themes with configurable styling
- **Hybrid layout**: Horizontal resource group clustering with vertical resource stacking

### Resource Discovery Process

1. Authenticate with Azure using DefaultAzureCredential
2. Query Resource Graph API for resources in target resource groups
3. Categorize resources by type (compute, network, storage, etc.)
4. Discover network topology (VNets, subnets, NSGs, load balancers)
5. Map resource relationships and dependencies
6. Build NetworkX graph with subgraph clustering
7. Generate Graphviz DOT representation
8. Render to PNG/SVG/HTML with icons and themes

### Output Formats

- **PNG**: Raster image format, good for static viewing and embedding in documents
- **SVG**: Vector format, scalable and good for web usage 
- **HTML**: Interactive web page with zoom, pan, drag, and source viewing capabilities

### Entry Points

- `azviz.py` - Wrapper script for development usage
- `src/azviz/cli.py:main()` - Primary CLI entry point
- `python-azviz` command after installation

## Prerequisites

- Python 3.8+
- Graphviz installed on system
- Azure authentication configured (az login, service principal, etc.)
- Required Python packages in requirements.txt