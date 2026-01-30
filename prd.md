# PRD: rename_project Core Functionality

## Overview
Implement the core renaming functionality for the `rename_project` CLI tool. The tool renames a Python project by replacing all occurrences of the old project name with a new project name across all files in the directory.

## Requirements

### 1. New Project Name Source
- Derive the new project name from the **current directory name**
- Example: If CWD is `/path/to/my_new_project`, new name = `my_new_project`

### 2. Old Project Name Source
- Read from `pyproject.toml` in the current directory
- Parse the `[project] name` field
- Exit with error if `pyproject.toml` doesn't exist or `name` field is missing

### 3. Name Variations
Generate 5 variations for both old and new names:

| Variation | Example (for `my_project`) |
|-----------|---------------------------|
| lowercase_underscore | `my_project` |
| lowercase_hyphen | `my-project` |
| UPPERCASE_UNDERSCORE | `MY_PROJECT` |
| UPPERCASE_HYPHEN | `MY-PROJECT` |
| PascalCase | `MyProject` |

### 4. Same-Name Check
- Normalize both names to `lowercase_underscore` format
- If they match, exit with error message:
  ```
  Error: New project name 'xxx' matches old project name. Nothing to rename.
  ```

### 5. File Content Replacement
- Recursively process all files in the current directory
- **Exclude directories:** `.idea`, `.git`
- Skip binary files (detect via null byte check or file extension)
- For each text file, replace all 5 variations:
  - `old_lowercase_underscore` → `new_lowercase_underscore`
  - `old_lowercase_hyphen` → `new_lowercase_hyphen`
  - `old_UPPERCASE_UNDERSCORE` → `new_UPPERCASE_UNDERSCORE`
  - `old_UPPERCASE_HYPHEN` → `new_UPPERCASE_HYPHEN`
  - `OldPascalCase` → `NewPascalCase`

### 6. Directory and File Renaming
- Rename directories containing old name variations
  - Example: `src/old_project/` → `src/new_project/`
- Rename files containing old name variations
  - Example: `old_project.py` → `new_project.py`
- Process from deepest to shallowest (bottom-up) to avoid path issues
- **Exclude:** `.idea`, `.git` directories

### 7. Dry-Run Mode
- `--dry-run` flag shows what would be changed without modifying anything
- List files that would be modified and renames that would occur

### 8. Confirmation Prompt
- Before making changes, display summary and prompt for confirmation
- `--yes` flag skips the confirmation prompt

---

## PascalCase Conversion Rules
- Split name on `_` or `-`
- Capitalize first letter of each word
- Join without separator
- Examples:
  - `my_project` → `MyProject`
  - `my-project` → `MyProject`
  - `foo_bar_baz` → `FooBarBaz`

---

## Implementation Plan

### Files to Modify/Create

| File | Purpose |
|------|---------|
| `src/rename_project/cli.py` | Update CLI with --dry-run and --yes flags |
| `src/rename_project/renamer.py` | Core renaming logic (new file) |
| `tests/test_renamer.py` | Unit tests for renaming logic (new file) |

### Module: `renamer.py`

```python
@dataclass
class NameVariations:
    lowercase_underscore: str  # my_project
    lowercase_hyphen: str      # my-project
    uppercase_underscore: str  # MY_PROJECT
    uppercase_hyphen: str      # MY-PROJECT
    pascal_case: str           # MyProject

@dataclass
class RenameResult:
    files_modified: list[Path]
    files_renamed: list[tuple[Path, Path]]
    dirs_renamed: list[tuple[Path, Path]]

# Key functions:
def get_old_name_from_pyproject(path: Path) -> str
def get_new_name_from_directory(path: Path) -> str
def generate_name_variations(name: str) -> NameVariations
def normalize_name(name: str) -> str  # Convert to lowercase_underscore
def to_pascal_case(name: str) -> str  # my_project -> MyProject
def is_binary_file(path: Path) -> bool
def find_files_to_process(root: Path, exclude: set[str]) -> Iterator[Path]
def replace_in_file(path: Path, replacements: dict[str, str]) -> bool
def rename_paths(root: Path, old_vars: NameVariations, new_vars: NameVariations, exclude: set[str]) -> list[tuple[Path, Path]]
def rename_project(root: Path, dry_run: bool = False) -> RenameResult
```

### CLI Integration

```
rename-project [OPTIONS]

Options:
  --dry-run    Preview changes without modifying files
  --yes, -y    Skip confirmation prompt
  -V, --version
  -h, --help
```

**Flow:**
1. Read old name from pyproject.toml
2. Get new name from directory
3. Check if names are the same (error if so)
4. Generate variations for both
5. If not --dry-run: show summary and prompt for confirmation (unless --yes)
6. Replace file contents (deepest files first)
7. Rename files and directories (bottom-up)
8. Display results

---

## Verification

1. Create a test project with various name occurrences in files and paths
2. Run `rename-project --dry-run` and verify preview output
3. Run `rename-project --yes` and verify:
   - All 5 variations replaced correctly in file contents
   - Directories and files renamed correctly
   - `.git` and `.idea` directories untouched
   - `pyproject.toml` name field updated
4. Run `make test` - all tests pass (pytest + ruff + pyright)
