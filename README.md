# rename_project

A CLI tool for renaming Python projects. Replaces all occurrences of the old project name with a new name across all files, including 5 naming variations (lowercase_underscore, lowercase-hyphen, UPPERCASE_UNDERSCORE, UPPERCASE-HYPHEN, PascalCase).

## Quick Start with uvx

Run directly from GitHub without installing:

```bash
# Navigate to your project directory (the new name)
cd /path/to/my_new_project

# Preview changes (dry run)
uvx --from git+https://github.com/bitranox/rename_project.git rename-project --dry-run

# Apply changes
uvx --from git+https://github.com/bitranox/rename_project.git rename-project --yes
```

## Installation

```bash
pip install rename_project
```

For development:

```bash
pip install -e ".[dev]"
```

## Usage

The tool reads the old project name from `pyproject.toml` and derives the new name from the current directory name.

```bash
# Preview changes without modifying files
rename-project --dry-run

# Apply changes (with confirmation prompt)
rename-project

# Apply changes without confirmation
rename-project --yes

# Show version
rename-project --version

# Show help
rename-project --help
```

### Name Variations

The tool replaces all 5 naming variations:

| Variation | Example |
|-----------|---------|
| lowercase_underscore | `my_project` |
| lowercase-hyphen | `my-project` |
| UPPERCASE_UNDERSCORE | `MY_PROJECT` |
| UPPERCASE-HYPHEN | `MY-PROJECT` |
| PascalCase | `MyProject` |

### Excluded Directories

The following directories are automatically excluded:
- `.git`
- `.idea`
- `__pycache__`
- `.venv`, `venv`
- `.tox`, `.nox`
- `.mypy_cache`

## Development

```bash
# Install dev dependencies
make dev

# Run tests
make test

# Run tests with coverage
make test-cov

# Run linter
make lint

# Format code
make format

# Run type checker
make typecheck

# Run all checks
make all
```

## License

MIT
