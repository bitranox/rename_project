"""Core renaming logic for rename_project."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path  # noqa: TC003 - needed at runtime for dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

# Directories to always exclude from processing
EXCLUDE_DIRS = {".git", ".idea", "__pycache__", ".venv", "venv", ".tox", ".nox", ".mypy_cache"}

# Binary file extensions to skip
BINARY_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".so",
    ".dll",
    ".exe",
    ".bin",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".ico",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".7z",
    ".rar",
    ".whl",
    ".egg",
}


@dataclass
class NameVariations:
    """All naming variations for a project name."""

    lowercase_underscore: str  # my_project
    lowercase_hyphen: str  # my-project
    uppercase_underscore: str  # MY_PROJECT
    uppercase_hyphen: str  # MY-PROJECT
    pascal_case: str  # MyProject

    def as_dict(self) -> dict[str, str]:
        """Return variations as a dictionary."""
        return {
            "lowercase_underscore": self.lowercase_underscore,
            "lowercase_hyphen": self.lowercase_hyphen,
            "uppercase_underscore": self.uppercase_underscore,
            "uppercase_hyphen": self.uppercase_hyphen,
            "pascal_case": self.pascal_case,
        }


def _empty_path_list() -> list[Path]:
    return []


def _empty_path_tuple_list() -> list[tuple[Path, Path]]:
    return []


@dataclass
class RenameResult:
    """Result of a rename operation."""

    files_modified: list[Path] = field(default_factory=_empty_path_list)
    files_renamed: list[tuple[Path, Path]] = field(default_factory=_empty_path_tuple_list)
    dirs_renamed: list[tuple[Path, Path]] = field(default_factory=_empty_path_tuple_list)


def normalize_name(name: str) -> str:
    """Normalize a name to lowercase_underscore format.

    Converts hyphens to underscores and lowercases the string.
    Also handles PascalCase by inserting underscores before capitals.
    """
    # First, handle PascalCase by inserting underscores before capitals
    # But only if it's not all caps
    if not name.isupper() and "_" not in name and "-" not in name:
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", name)

    # Replace hyphens with underscores and lowercase
    return name.replace("-", "_").lower()


def to_pascal_case(name: str) -> str:
    """Convert a name to PascalCase.

    Examples:
        my_project -> MyProject
        my-project -> MyProject
        foo_bar_baz -> FooBarBaz
    """
    # Split on underscores or hyphens
    parts = re.split(r"[_-]", name)
    # Capitalize first letter of each part
    return "".join(part.capitalize() for part in parts if part)


def generate_name_variations(name: str) -> NameVariations:
    """Generate all naming variations from a base name.

    The input name can be in any format (underscore, hyphen, or PascalCase).
    """
    # Normalize to lowercase_underscore first
    normalized = normalize_name(name)

    return NameVariations(
        lowercase_underscore=normalized,
        lowercase_hyphen=normalized.replace("_", "-"),
        uppercase_underscore=normalized.upper(),
        uppercase_hyphen=normalized.upper().replace("_", "-"),
        pascal_case=to_pascal_case(normalized),
    )


def get_old_name_from_pyproject(path: Path) -> str:
    """Read the project name from pyproject.toml.

    Args:
        path: Path to the directory containing pyproject.toml

    Returns:
        The project name from the [project] name field

    Raises:
        FileNotFoundError: If pyproject.toml doesn't exist
        ValueError: If name field is missing or invalid
    """
    pyproject_path = path / "pyproject.toml"

    if not pyproject_path.exists():
        raise FileNotFoundError(f"pyproject.toml not found in {path}")

    content = pyproject_path.read_text(encoding="utf-8")

    # Simple regex to find name in [project] section
    # This handles the common case without requiring toml library
    pattern = r'^\[project\]\s*\n(?:.*\n)*?name\s*=\s*["\']([^"\']+)["\']'
    match = re.search(pattern, content, re.MULTILINE)

    if not match:
        # Try alternative: name might be before other fields
        match = re.search(r'\[project\][\s\S]*?name\s*=\s*["\']([^"\']+)["\']', content)

    if not match:
        raise ValueError("Could not find 'name' field in [project] section of pyproject.toml")

    return match.group(1)


def get_new_name_from_directory(path: Path) -> str:
    """Get the new project name from the directory name.

    Args:
        path: Path to the project directory

    Returns:
        The directory name as the new project name
    """
    return path.resolve().name


def is_binary_file(path: Path) -> bool:
    """Check if a file is binary.

    Uses extension check first, then null byte detection.
    """
    if path.suffix.lower() in BINARY_EXTENSIONS:
        return True

    try:
        with path.open("rb") as f:
            chunk = f.read(8192)
            return b"\x00" in chunk
    except (OSError, PermissionError):
        return True


def should_exclude_path(path: Path, exclude: set[str]) -> bool:
    """Check if a path should be excluded from processing."""
    return any(part in exclude for part in path.parts)


def find_files_to_process(root: Path, exclude: set[str]) -> Iterator[Path]:
    """Find all files to process, excluding specified directories.

    Files are yielded in order from deepest to shallowest.
    """
    all_files: list[Path] = []

    for path in root.rglob("*"):
        if path.is_file() and not should_exclude_path(path.relative_to(root), exclude):
            all_files.append(path)

    # Sort by depth (deepest first) for bottom-up processing
    all_files.sort(key=lambda p: len(p.parts), reverse=True)

    yield from all_files


def find_paths_to_rename(
    root: Path, old_vars: NameVariations, exclude: set[str]
) -> list[tuple[Path, Path]]:
    """Find all files and directories that need to be renamed.

    Returns list of (old_path, new_path) tuples, sorted deepest first.
    """
    renames: list[tuple[Path, Path]] = []
    old_names = [
        old_vars.lowercase_underscore,
        old_vars.lowercase_hyphen,
        old_vars.uppercase_underscore,
        old_vars.uppercase_hyphen,
        old_vars.pascal_case,
    ]

    for path in root.rglob("*"):
        if should_exclude_path(path.relative_to(root), exclude):
            continue

        name = path.name
        for old_name in old_names:
            if old_name in name:
                renames.append((path, path))
                break

    # Sort by depth (deepest first)
    renames.sort(key=lambda x: len(x[0].parts), reverse=True)

    return renames


def create_replacement_map(old_vars: NameVariations, new_vars: NameVariations) -> dict[str, str]:
    """Create a mapping of old names to new names for all variations."""
    return {
        old_vars.lowercase_underscore: new_vars.lowercase_underscore,
        old_vars.lowercase_hyphen: new_vars.lowercase_hyphen,
        old_vars.uppercase_underscore: new_vars.uppercase_underscore,
        old_vars.uppercase_hyphen: new_vars.uppercase_hyphen,
        old_vars.pascal_case: new_vars.pascal_case,
    }


def replace_in_file(path: Path, replacements: dict[str, str]) -> bool:
    """Replace all occurrences in a file.

    Args:
        path: Path to the file
        replacements: Dict mapping old strings to new strings

    Returns:
        True if any replacements were made, False otherwise
    """
    if is_binary_file(path):
        return False

    try:
        content = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return False

    original = content

    for old, new in replacements.items():
        content = content.replace(old, new)

    if content != original:
        path.write_text(content, encoding="utf-8")
        return True

    return False


def rename_path(path: Path, replacements: dict[str, str]) -> Path | None:
    """Rename a file or directory if its name contains any old name variations.

    Args:
        path: Path to rename
        replacements: Dict mapping old strings to new strings

    Returns:
        New path if renamed, None if not renamed
    """
    name = path.name
    new_name = name

    for old, new in replacements.items():
        new_name = new_name.replace(old, new)

    if new_name != name:
        new_path = path.parent / new_name
        path.rename(new_path)
        return new_path

    return None


def _check_file_for_modifications(
    file_path: Path, replacements: dict[str, str]
) -> bool:
    """Check if a file would be modified during dry run."""
    if is_binary_file(file_path):
        return False
    try:
        content = file_path.read_text(encoding="utf-8")
        return any(old in content for old in replacements)
    except (UnicodeDecodeError, OSError):
        return False


def _process_file_contents(
    root: Path, exclude: set[str], replacements: dict[str, str], dry_run: bool
) -> list[Path]:
    """Process file contents and return list of modified files."""
    files_modified: list[Path] = []
    for file_path in find_files_to_process(root, exclude):
        if dry_run:
            if _check_file_for_modifications(file_path, replacements):
                files_modified.append(file_path)
        elif replace_in_file(file_path, replacements):
            files_modified.append(file_path)
    return files_modified


def _rename_paths(
    root: Path, exclude: set[str], replacements: dict[str, str], dry_run: bool
) -> tuple[list[tuple[Path, Path]], list[tuple[Path, Path]]]:
    """Rename files and directories, return (files_renamed, dirs_renamed)."""
    files_renamed: list[tuple[Path, Path]] = []
    dirs_renamed: list[tuple[Path, Path]] = []

    paths_to_check = sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True)

    for path in paths_to_check:
        if should_exclude_path(path.relative_to(root), exclude):
            continue

        name = path.name
        new_name_computed = name
        for old, new in replacements.items():
            new_name_computed = new_name_computed.replace(old, new)

        if new_name_computed != name:
            new_path = path.parent / new_name_computed
            if path.is_dir():
                if not dry_run:
                    path.rename(new_path)
                dirs_renamed.append((path, new_path))
            else:
                if not dry_run:
                    path.rename(new_path)
                files_renamed.append((path, new_path))

    return files_renamed, dirs_renamed


def rename_project(
    root: Path,
    *,
    dry_run: bool = False,
    old_name: str | None = None,
    new_name: str | None = None,
) -> RenameResult:
    """Rename a project by replacing all name variations.

    Args:
        root: Root directory of the project
        dry_run: If True, don't make any changes
        old_name: Override old name (for testing)
        new_name: Override new name (for testing)

    Returns:
        RenameResult with lists of modified/renamed files and directories
    """
    exclude = EXCLUDE_DIRS

    # Get names
    if old_name is None:
        old_name = get_old_name_from_pyproject(root)
    if new_name is None:
        new_name = get_new_name_from_directory(root)

    # Generate variations
    old_vars = generate_name_variations(old_name)
    new_vars = generate_name_variations(new_name)

    # Create replacement map
    replacements = create_replacement_map(old_vars, new_vars)

    # Process file contents (deepest first)
    files_modified = _process_file_contents(root, exclude, replacements, dry_run)

    # Rename files and directories (deepest first)
    files_renamed, dirs_renamed = _rename_paths(root, exclude, replacements, dry_run)

    return RenameResult(
        files_modified=files_modified,
        files_renamed=files_renamed,
        dirs_renamed=dirs_renamed,
    )
