"""Command-line interface for rename_project."""

from __future__ import annotations

import sys
from pathlib import Path

import rich_click as click
from rich.console import Console
from rich.table import Table

from rename_project import __version__
from rename_project.renamer import (
    RenameResult,
    generate_name_variations,
    get_new_name_from_directory,
    get_old_name_from_pyproject,
    normalize_name,
    rename_project,
)

console = Console()


def display_preview(
    old_name: str,
    new_name: str,
    result: RenameResult,
) -> None:
    """Display a preview of changes that would be made."""
    old_vars = generate_name_variations(old_name)
    new_vars = generate_name_variations(new_name)

    # Show name variations
    console.print("\n[bold]Name Variations:[/bold]")
    table = Table(show_header=True, header_style="bold")
    table.add_column("Variation")
    table.add_column("Old")
    table.add_column("New")

    table.add_row(
        "lowercase_underscore", old_vars.lowercase_underscore, new_vars.lowercase_underscore
    )
    table.add_row("lowercase_hyphen", old_vars.lowercase_hyphen, new_vars.lowercase_hyphen)
    table.add_row(
        "uppercase_underscore", old_vars.uppercase_underscore, new_vars.uppercase_underscore
    )
    table.add_row("uppercase_hyphen", old_vars.uppercase_hyphen, new_vars.uppercase_hyphen)
    table.add_row("PascalCase", old_vars.pascal_case, new_vars.pascal_case)

    console.print(table)

    # Show files that would be modified
    if result.files_modified:
        console.print(f"\n[bold]Files to modify ({len(result.files_modified)}):[/bold]")
        for path in result.files_modified:
            console.print(f"  {path}")

    # Show files that would be renamed
    if result.files_renamed:
        console.print(f"\n[bold]Files to rename ({len(result.files_renamed)}):[/bold]")
        for old_path, new_path in result.files_renamed:
            console.print(f"  {old_path.name} -> {new_path.name}")

    # Show directories that would be renamed
    if result.dirs_renamed:
        console.print(f"\n[bold]Directories to rename ({len(result.dirs_renamed)}):[/bold]")
        for old_path, new_path in result.dirs_renamed:
            console.print(f"  {old_path} -> {new_path}")

    if not result.files_modified and not result.files_renamed and not result.dirs_renamed:
        console.print("\n[yellow]No changes detected.[/yellow]")


def display_results(result: RenameResult) -> None:
    """Display the results of the rename operation."""
    console.print("\n[bold green]Rename completed![/bold green]")

    if result.files_modified:
        console.print(f"\n[bold]Files modified ({len(result.files_modified)}):[/bold]")
        for path in result.files_modified:
            console.print(f"  [green]✓[/green] {path}")

    if result.files_renamed:
        console.print(f"\n[bold]Files renamed ({len(result.files_renamed)}):[/bold]")
        for old_path, new_path in result.files_renamed:
            console.print(f"  [green]✓[/green] {old_path.name} -> {new_path.name}")

    if result.dirs_renamed:
        console.print(f"\n[bold]Directories renamed ({len(result.dirs_renamed)}):[/bold]")
        for old_path, new_path in result.dirs_renamed:
            console.print(f"  [green]✓[/green] {old_path} -> {new_path}")

    total = len(result.files_modified) + len(result.files_renamed) + len(result.dirs_renamed)
    console.print(f"\n[bold]Total changes: {total}[/bold]")


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--version",
    "-V",
    is_flag=True,
    help="Show version and exit.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview changes without modifying files.",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt.",
)
def main(*, version: bool, dry_run: bool, yes: bool) -> None:
    """Rename a Python project by replacing all occurrences of the old name.

    The new project name is derived from the current directory name.
    The old project name is read from pyproject.toml.

    All 5 naming variations are replaced:
      - lowercase_underscore (my_project)
      - lowercase-hyphen (my-project)
      - UPPERCASE_UNDERSCORE (MY_PROJECT)
      - UPPERCASE-HYPHEN (MY-PROJECT)
      - PascalCase (MyProject)
    """
    if version:
        click.echo(f"rename-project {__version__}")
        sys.exit(0)

    root = Path.cwd()

    # Get old and new names
    try:
        old_name = get_old_name_from_pyproject(root)
    except FileNotFoundError:
        console.print("[red]Error: pyproject.toml not found in current directory.[/red]")
        sys.exit(1)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)

    new_name = get_new_name_from_directory(root)

    # Check if names are the same
    old_normalized = normalize_name(old_name)
    new_normalized = normalize_name(new_name)

    if old_normalized == new_normalized:
        console.print(
            f"[red]Error: New project name '{new_normalized}' matches old project name. "
            f"Nothing to rename.[/red]"
        )
        sys.exit(1)

    console.print(f"[bold]Renaming project:[/bold] {old_name} -> {new_name}")

    if dry_run:
        console.print("[yellow](Dry run - no changes will be made)[/yellow]")
        result = rename_project(root, dry_run=True)
        display_preview(old_name, new_name, result)
        return

    # Preview changes
    preview_result = rename_project(root, dry_run=True)
    display_preview(old_name, new_name, preview_result)

    total_changes = (
        len(preview_result.files_modified)
        + len(preview_result.files_renamed)
        + len(preview_result.dirs_renamed)
    )

    if total_changes == 0:
        console.print("\n[yellow]No changes to make.[/yellow]")
        return

    # Confirm unless --yes
    if not yes:
        console.print()
        if not click.confirm("Proceed with rename?"):
            console.print("[yellow]Aborted.[/yellow]")
            sys.exit(0)

    # Perform the rename
    result = rename_project(root, dry_run=False)
    display_results(result)


if __name__ == "__main__":
    main()
