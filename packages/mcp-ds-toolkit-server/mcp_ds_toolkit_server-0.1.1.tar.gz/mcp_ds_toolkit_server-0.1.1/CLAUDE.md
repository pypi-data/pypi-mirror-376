# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP DS Toolkit Server is a standalone Model Context Protocol (MCP) server that provides complete data science capabilities to AI assistants. It offers 31 DS tools across data management, model training, and experiment tracking with local SQLite persistence.

## Development Commands

### Environment Setup
```bash
# Development setup
uv sync

# Install with optional dependencies
uv sync --extra dev          # Development tools
uv sync --extra aws          # AWS cloud storage
uv sync --extra all          # All extras
```

### Testing
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/mcp_ds_toolkit_server --cov-report=html

# Run specific test types
uv run pytest -m unit                    # Unit tests only
uv run pytest -m integration             # Integration tests only
uv run pytest -m "not slow"              # Skip slow tests
uv run pytest tests/test_server.py       # Single test file
```

### Code Quality
```bash
# Format code
uv run black src/ tests/
uv run isort src/ tests/

# Lint and type checking
uv run flake8 src/ tests/
uv run mypy src/

# Security scanning
uv run bandit -r src/
uv run safety check

# Run all pre-commit hooks
pre-commit run --all-files
```

### Running the Server
```bash
# Development mode (from source)
uv run mcp-mlops-server

# Or via python module
uv run python -m mcp_ds_toolkit_server

# CLI entry point for testing
uv run python src/mcp_ds_toolkit_server/__main__.py
```

### Building and Distribution
```bash
# Build package
uv build

# Install locally for testing
pip install -e .
```

## Code Architecture

### Core Components

#### 1. Server Layer (`server.py`)
- **MCPDataScienceServer**: Main MCP protocol handler
- Orchestrates all tool categories and manages server lifecycle
- Handles MCP protocol initialization and tool registration

#### 2. Tool Categories (`tools/`)
- **DataManagementTools**: 15 tools for data loading, validation, preprocessing, cleaning
- **TrainingTools**: 6 tools for model training, evaluation, comparison, hyperparameter tuning
- **TrackingTools**: 10 tools for experiment tracking with local SQLite persistence
- **BaseMCPTools**: Abstract base class defining tool interface

#### 3. Data Processing Layer (`data/`)
- **loader.py**: Multi-format data loading (CSV, JSON, Excel, sklearn datasets)
- **preprocessing.py**: Feature scaling, encoding, selection pipeline
- **cleaning.py**: Missing value handling, outlier detection/removal
- **validation.py**: Data quality checks and integrity validation
- **profiling.py**: Statistical analysis and data profiling
- **splitting.py**: Train/test/validation dataset splitting
- **visualization.py**: Plot generation for EDA and model analysis

#### 4. Machine Learning Layer (`training/`, `workflows/`)
- **trainer.py**: Model training orchestration with 20+ scikit-learn algorithms
- **evaluator.py**: Performance evaluation and metrics calculation
- Supports classification and regression with automatic hyperparameter tuning

#### 5. Persistence Layer (`tracking/`)
- **local_tracking.py**: SQLite-based experiment tracking
- **ArtifactBridge**: File system artifact management
- Storage structure: `~/.mcp-ds-toolkit/` with experiments.db and artifacts/

#### 6. Utilities (`utils/`)
- **config.py**: Settings and configuration management
- **logger.py**: Logging setup and utilities
- **persistence.py**: File system and storage utilities

### Key Design Patterns

1. **Tool-Based Architecture**: Each capability exposed as an MCP tool with consistent interface
2. **Local-First Storage**: All data persisted locally in SQLite with artifact filesystem
3. **Pipeline Integration**: Tools designed to work together in data science workflows
4. **Type Safety**: Comprehensive type hints throughout codebase (mypy strict mode)
5. **Async-First**: Full async/await pattern for MCP protocol compliance

### Data Flow

```
AI Assistant Request → MCP Protocol → Tool Router → Core Logic → Local Storage
                                                      ↓
                                             Data/Model/Artifact
                                                      ↓
                                              SQLite Tracking DB
```

### Critical Dependencies

- **mcp>=1.0.0**: MCP protocol implementation
- **scikit-learn>=1.4.0**: Core ML algorithms and utilities
- **pandas>=2.2.0**: Data manipulation and analysis
- **matplotlib>=3.7.0**: Plotting and visualization
- **Python 3.12+**: Required minimum version

### Testing Strategy

- **Unit Tests**: Individual component testing (`tests/test_*.py`)
- **Integration Tests**: End-to-end workflow testing
- **Coverage Target**: 50% minimum (configured in pyproject.toml)
- **Test Organization**: Mirrors source structure (`tests/tools/`, `tests/data/`)

### Configuration Management

- **pyproject.toml**: Primary configuration for build, dependencies, tools
- **Settings class**: Runtime configuration with environment variable support
- **Local storage**: `~/.mcp-ds-toolkit/` for data persistence and artifacts

## Package Structure Notes

- Entry point: `mcp-mlops-server` command (mapped to `__main__.py:cli_main`)
- Source code: `src/mcp_ds_toolkit_server/` (standard src layout)
- Package name mismatch: PyPI package is `mcp-mlops-server`, source module is `mcp_ds_toolkit_server`
- Build system: Hatchling with wheel packaging for `src/mcp_ds_toolkit_server`