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

### Why we recommend uv: supply-chain protection

This repository commits a `uv.lock`. It pins every package the project needs, transitive
dependencies included, to an exact version and to the hashes of that version's files. The
`exclude-newer` setting under `[tool.uv]` in `pyproject.toml` adds a cooldown: uv leaves any
release younger than that out of the lock. `uv sync --locked` installs from the lock, so a
hijacked release that gets pulled again within the cooldown never reaches a checkout of this
repository, and a file whose hash does not match is refused.

That protection stays in this repository. The installable package declares only lower bounds
(`>=`) for its dependencies, so a plain `pip install` takes the newest release of every transitive
dependency at the moment you run it. If one of them was hijacked an hour earlier, you get the
hijacked version. `pipx install` and `uv tool install` without options do the same.

To install the command line tool with a cooldown of your own (uv then skips any release younger
than 7 days, transitive ones included), or to run the exact tree our tests run against:

```bash
uv tool install --exclude-newer "7 days" git+https://github.com/bitranox/rename_project.git
git clone https://github.com/bitranox/rename_project.git && cd rename_project && uv sync --locked && uv run rename-project --help
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

| Variation            | Example      |
|----------------------|--------------|
| lowercase_underscore | `my_project` |
| lowercase-hyphen     | `my-project` |
| UPPERCASE_UNDERSCORE | `MY_PROJECT` |
| UPPERCASE-HYPHEN     | `MY-PROJECT` |
| PascalCase           | `MyProject`  |

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
