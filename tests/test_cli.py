"""Tests for the CLI module."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if sys.version_info >= (3, 11):
    import tomllib

if TYPE_CHECKING:
    from click.testing import CliRunner

from rename_project import __version__
from rename_project.cli import main


class TestVersionFlag:
    """Tests for the --version flag."""

    def test_version_long_flag(self, cli_runner: CliRunner) -> None:
        """Test that --version prints the version."""
        result = cli_runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output
        assert "rename-project" in result.output

    def test_version_short_flag(self, cli_runner: CliRunner) -> None:
        """Test that -V prints the version."""
        result = cli_runner.invoke(main, ["-V"])
        assert result.exit_code == 0
        assert __version__ in result.output


class TestHelpFlag:
    """Tests for the --help flag."""

    def test_help_long_flag(self, cli_runner: CliRunner) -> None:
        """Test that --help prints help text."""
        result = cli_runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Rename a Python project" in result.output
        assert "--version" in result.output
        assert "--help" in result.output
        assert "--dry-run" in result.output
        assert "--yes" in result.output

    def test_help_short_flag(self, cli_runner: CliRunner) -> None:
        """Test that -h prints help text."""
        result = cli_runner.invoke(main, ["-h"])
        assert result.exit_code == 0
        assert "Rename a Python project" in result.output


class TestMissingPyproject:
    """Tests for missing pyproject.toml."""

    def test_no_pyproject_error(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Test error when pyproject.toml is missing."""
        old_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            result = cli_runner.invoke(main, [])
            assert result.exit_code == 1
            assert "pyproject.toml not found" in result.output
        finally:
            os.chdir(old_cwd)


class TestSameNameError:
    """Tests for same name error."""

    def test_same_name_error(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Test error when old and new names are the same."""
        project_dir = tmp_path / "my_project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text(
            '[project]\nname = "my_project"\n',
            encoding="utf-8",
        )

        old_cwd = Path.cwd()
        try:
            os.chdir(project_dir)
            result = cli_runner.invoke(main, [])
            assert result.exit_code == 1
            assert "matches old project name" in result.output
        finally:
            os.chdir(old_cwd)


class TestDryRun:
    """Tests for --dry-run flag."""

    def test_dry_run_shows_preview(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Test that --dry-run shows preview without making changes."""
        project_dir = tmp_path / "new_project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text(
            '[project]\nname = "old_project"\n',
            encoding="utf-8",
        )
        src = project_dir / "src" / "old_project"
        src.mkdir(parents=True)
        (src / "__init__.py").write_text('"""old_project"""', encoding="utf-8")

        old_cwd = Path.cwd()
        try:
            os.chdir(project_dir)
            result = cli_runner.invoke(main, ["--dry-run"])
            assert result.exit_code == 0
            assert "Dry run" in result.output
            assert "Name Variations" in result.output
        finally:
            os.chdir(old_cwd)

        # Files should not be changed
        assert (project_dir / "src" / "old_project").exists()
        assert not (project_dir / "src" / "new_project").exists()


class TestConfirmation:
    """Tests for confirmation prompt."""

    def test_aborts_on_no(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Test that 'n' aborts the rename."""
        project_dir = tmp_path / "new_project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text(
            '[project]\nname = "old_project"\n',
            encoding="utf-8",
        )
        src = project_dir / "src" / "old_project"
        src.mkdir(parents=True)
        (src / "__init__.py").write_text('"""old_project"""', encoding="utf-8")

        old_cwd = Path.cwd()
        try:
            os.chdir(project_dir)
            result = cli_runner.invoke(main, [], input="n\n")
            assert result.exit_code == 0
            assert "Aborted" in result.output
        finally:
            os.chdir(old_cwd)

        # Files should not be changed
        assert (project_dir / "src" / "old_project").exists()

    def test_yes_flag_skips_prompt(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Test that --yes skips confirmation prompt."""
        project_dir = tmp_path / "new_project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text(
            '[project]\nname = "old_project"\n',
            encoding="utf-8",
        )
        src = project_dir / "src" / "old_project"
        src.mkdir(parents=True)
        (src / "__init__.py").write_text('"""old_project"""', encoding="utf-8")

        old_cwd = Path.cwd()
        try:
            os.chdir(project_dir)
            result = cli_runner.invoke(main, ["--yes"])
            assert result.exit_code == 0
            assert "Rename completed" in result.output
        finally:
            os.chdir(old_cwd)

        # Files should be changed
        assert (project_dir / "src" / "new_project").exists()
        assert not (project_dir / "src" / "old_project").exists()

    def test_short_yes_flag(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Test that -y skips confirmation prompt."""
        project_dir = tmp_path / "new_project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text(
            '[project]\nname = "old_project"\n',
            encoding="utf-8",
        )

        old_cwd = Path.cwd()
        try:
            os.chdir(project_dir)
            result = cli_runner.invoke(main, ["-y"])
            # Should complete (even if no changes to make)
            assert result.exit_code == 0
        finally:
            os.chdir(old_cwd)


class TestFullRename:
    """Integration tests for full rename operation."""

    def test_full_rename_all_variations(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Test that all name variations are replaced."""
        project_dir = tmp_path / "new_project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text(
            '[project]\nname = "old_project"\n',
            encoding="utf-8",
        )
        src = project_dir / "src" / "old_project"
        src.mkdir(parents=True)
        (src / "__init__.py").write_text(
            """\"\"\"old_project module.\"\"\"
from old_project.utils import OldProject
OLD_PROJECT = "old-project"
""",
            encoding="utf-8",
        )

        old_cwd = Path.cwd()
        try:
            os.chdir(project_dir)
            result = cli_runner.invoke(main, ["--yes"])
            assert result.exit_code == 0
        finally:
            os.chdir(old_cwd)

        # Check directory renamed
        assert (project_dir / "src" / "new_project").exists()

        # Check content replaced
        content = (project_dir / "src" / "new_project" / "__init__.py").read_text(encoding="utf-8")
        assert "new_project module" in content
        assert "from new_project.utils import NewProject" in content
        assert 'NEW_PROJECT = "new-project"' in content


# A pyproject shaped like bitranox_template_py_cli's: two [project.scripts] keys
# that differ only in separator, so a ONE-WORD new name maps both onto one key.
_TEMPLATE_PYPROJECT = """\
[project]
name = "bitranox_template_py_cli"
version = "1.0.0"

[project.scripts]
# both spellings start the same CLI
bitranox_template_py_cli = "bitranox_template_py_cli.entry:main"
bitranox-template-py-cli = "bitranox_template_py_cli.entry:main"

[tool.example]
setting = "bitranox-template-py-cli"
"""

_RENAMED_PYPROJECT = """\
[project]
name = "foo"
version = "1.0.0"

[project.scripts]
# both spellings start the same CLI
foo = "foo.entry:main"

[tool.example]
setting = "foo"
"""


def _make_template_project(root: Path, pyproject: str) -> Path:
    """Create a one-word-named project dir holding the given pyproject."""
    project_dir = root / "foo"
    package = project_dir / "src" / "bitranox_template_py_cli"
    package.mkdir(parents=True)
    (package / "entry.py").write_text("def main() -> None: ...\n", encoding="utf-8")
    (project_dir / "pyproject.toml").write_text(pyproject, encoding="utf-8")
    return project_dir


class TestOneWordRename:
    """A one-word new name collapses the template's two script keys into one."""

    def test_duplicate_script_key_is_dropped(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The renamed pyproject keeps one key and every other byte unchanged."""
        project_dir = _make_template_project(tmp_path, _TEMPLATE_PYPROJECT)
        monkeypatch.chdir(project_dir)

        result = cli_runner.invoke(main, ["--yes"])

        assert result.exit_code == 0, result.output
        pyproject = (project_dir / "pyproject.toml").read_bytes()
        assert pyproject == _RENAMED_PYPROJECT.encode("utf-8")
        assert (project_dir / "src" / "foo" / "entry.py").exists()

    def test_renamed_pyproject_parses_as_toml(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The result is valid TOML with the single script entry."""
        if sys.version_info < (3, 11):
            pytest.skip("tomllib is in the standard library from Python 3.11")
        project_dir = _make_template_project(tmp_path, _TEMPLATE_PYPROJECT)
        monkeypatch.chdir(project_dir)

        result = cli_runner.invoke(main, ["--yes"])

        assert result.exit_code == 0, result.output
        text = (project_dir / "pyproject.toml").read_text(encoding="utf-8")
        parsed = tomllib.loads(text)
        assert parsed["project"]["scripts"] == {"foo": "foo.entry:main"}

    def test_duplicate_key_with_different_target_is_refused(
        self, cli_runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Two keys collapsing onto one name with different targets stop the rename."""
        conflicting = _TEMPLATE_PYPROJECT.replace(
            'bitranox-template-py-cli = "bitranox_template_py_cli.entry:main"',
            'bitranox-template-py-cli = "bitranox_template_py_cli.other:run"',
        )
        project_dir = _make_template_project(tmp_path, conflicting)
        monkeypatch.chdir(project_dir)

        result = cli_runner.invoke(main, ["--yes"])

        assert result.exit_code == 1
        assert "[project.scripts]" in result.output
        assert "'foo'" in result.output
        assert (project_dir / "pyproject.toml").read_text(encoding="utf-8") == conflicting
        assert (project_dir / "src" / "bitranox_template_py_cli").exists()
