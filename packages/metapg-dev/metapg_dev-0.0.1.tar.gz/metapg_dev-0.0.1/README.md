# metapg-dev

Development dependencies for the metapg project.

## Purpose

This package provides all development dependencies needed for metapg development to ensure consistent development environments across all contributors.

## Installation

```bash
# Install development environment
pip install -e src/dev
```

## Included Tools

### Testing
- **pytest** - Testing framework with async support
- **pytest-asyncio** - Async test support
- **pytest-cov** - Coverage reporting

### Code Quality
- **black** - Code formatting
- **ruff** - Fast Python linter
- **mypy** - Static type checking

### Build Tools
- **build** - Modern Python package building
- **setuptools** - Package setup utilities
- **wheel** - Wheel format support

### Development Utilities
- **ipython** - Enhanced interactive Python shell
- **ipdb** - IPython debugger

## Usage

After installation, you can use all the development tools:

```bash
# Format code
black src/ tests/ examples/

# Lint code  
ruff check src/ tests/ examples/

# Type check
mypy src/pool/ src/migration/ src/cli/ src/metapg/

# Run tests
pytest tests/ -v --cov=metapg

# Build packages
python -m build
```

## Development Workflow

1. Install metapg-dev: `pip install -e src/dev`
2. Set up packages: `just install-dev`
3. Run quality checks: `just check`
4. Run tests: `just test`
5. Build packages: `just build`

This package ensures all developers have the same tools and versions for consistent development experience.