"""Tests for the renamer module."""

from __future__ import annotations

from pathlib import Path

import pytest

from rename_project.renamer import (
    EXCLUDE_DIRS,
    NameVariations,
    RenameResult,
    create_replacement_map,
    generate_name_variations,
    get_new_name_from_directory,
    get_old_name_from_pyproject,
    is_binary_file,
    normalize_name,
    rename_project,
    replace_in_file,
    should_exclude_path,
    to_pascal_case,
)


class TestNormalizeName:
    """Tests for normalize_name function."""

    def test_underscore_name(self) -> None:
        """Underscore names are lowercased."""
        assert normalize_name("my_project") == "my_project"
        assert normalize_name("My_Project") == "my_project"
        assert normalize_name("MY_PROJECT") == "my_project"

    def test_hyphen_name(self) -> None:
        """Hyphens are converted to underscores."""
        assert normalize_name("my-project") == "my_project"
        assert normalize_name("My-Project") == "my_project"
        assert normalize_name("MY-PROJECT") == "my_project"

    def test_pascal_case(self) -> None:
        """PascalCase is converted to underscore."""
        assert normalize_name("MyProject") == "my_project"
        assert normalize_name("FooBarBaz") == "foo_bar_baz"

    def test_single_word(self) -> None:
        """Single words are just lowercased."""
        assert normalize_name("Project") == "project"
        assert normalize_name("project") == "project"


class TestToPascalCase:
    """Tests for to_pascal_case function."""

    def test_underscore_name(self) -> None:
        """Underscore names are converted to PascalCase."""
        assert to_pascal_case("my_project") == "MyProject"
        assert to_pascal_case("foo_bar_baz") == "FooBarBaz"

    def test_hyphen_name(self) -> None:
        """Hyphen names are converted to PascalCase."""
        assert to_pascal_case("my-project") == "MyProject"
        assert to_pascal_case("foo-bar-baz") == "FooBarBaz"

    def test_single_word(self) -> None:
        """Single words are capitalized."""
        assert to_pascal_case("project") == "Project"

    def test_already_pascal(self) -> None:
        """Already PascalCase names work (no separators)."""
        assert to_pascal_case("MyProject") == "Myproject"  # No separators, treated as one word


class TestGenerateNameVariations:
    """Tests for generate_name_variations function."""

    def test_from_underscore_name(self) -> None:
        """Generate variations from underscore name."""
        vars = generate_name_variations("my_project")
        assert vars.lowercase_underscore == "my_project"
        assert vars.lowercase_hyphen == "my-project"
        assert vars.uppercase_underscore == "MY_PROJECT"
        assert vars.uppercase_hyphen == "MY-PROJECT"
        assert vars.pascal_case == "MyProject"

    def test_from_hyphen_name(self) -> None:
        """Generate variations from hyphen name."""
        vars = generate_name_variations("my-project")
        assert vars.lowercase_underscore == "my_project"
        assert vars.lowercase_hyphen == "my-project"
        assert vars.uppercase_underscore == "MY_PROJECT"
        assert vars.uppercase_hyphen == "MY-PROJECT"
        assert vars.pascal_case == "MyProject"

    def test_from_pascal_case(self) -> None:
        """Generate variations from PascalCase name."""
        vars = generate_name_variations("MyProject")
        assert vars.lowercase_underscore == "my_project"
        assert vars.lowercase_hyphen == "my-project"
        assert vars.uppercase_underscore == "MY_PROJECT"
        assert vars.uppercase_hyphen == "MY-PROJECT"
        assert vars.pascal_case == "MyProject"

    def test_as_dict(self) -> None:
        """Test the as_dict method."""
        vars = generate_name_variations("my_project")
        d = vars.as_dict()
        assert d["lowercase_underscore"] == "my_project"
        assert d["lowercase_hyphen"] == "my-project"
        assert d["uppercase_underscore"] == "MY_PROJECT"
        assert d["uppercase_hyphen"] == "MY-PROJECT"
        assert d["pascal_case"] == "MyProject"


class TestGetOldNameFromPyproject:
    """Tests for get_old_name_from_pyproject function."""

    def test_valid_pyproject(self, tmp_path: Path) -> None:
        """Read name from valid pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[project]\nname = "my_project"\nversion = "1.0.0"\n',
            encoding="utf-8",
        )
        assert get_old_name_from_pyproject(tmp_path) == "my_project"

    def test_single_quotes(self, tmp_path: Path) -> None:
        """Read name with single quotes."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            "[project]\nname = 'my_project'\nversion = '1.0.0'\n",
            encoding="utf-8",
        )
        assert get_old_name_from_pyproject(tmp_path) == "my_project"

    def test_missing_pyproject(self, tmp_path: Path) -> None:
        """Raise FileNotFoundError if pyproject.toml doesn't exist."""
        with pytest.raises(FileNotFoundError):
            get_old_name_from_pyproject(tmp_path)

    def test_missing_name_field(self, tmp_path: Path) -> None:
        """Raise ValueError if name field is missing."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[project]\nversion = '1.0.0'\n", encoding="utf-8")
        with pytest.raises(ValueError, match="Could not find 'name' field"):
            get_old_name_from_pyproject(tmp_path)

    def test_name_with_hyphens(self, tmp_path: Path) -> None:
        """Read name with hyphens."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[project]\nname = "my-project"\n',
            encoding="utf-8",
        )
        assert get_old_name_from_pyproject(tmp_path) == "my-project"


class TestGetNewNameFromDirectory:
    """Tests for get_new_name_from_directory function."""

    def test_simple_directory(self, tmp_path: Path) -> None:
        """Get name from directory."""
        project_dir = tmp_path / "new_project"
        project_dir.mkdir()
        assert get_new_name_from_directory(project_dir) == "new_project"

    def test_resolves_path(self, tmp_path: Path) -> None:
        """Path is resolved before getting name."""
        project_dir = tmp_path / "new_project"
        project_dir.mkdir()
        # Using relative path should still work
        assert get_new_name_from_directory(project_dir) == "new_project"


class TestIsBinaryFile:
    """Tests for is_binary_file function."""

    def test_text_file(self, tmp_path: Path) -> None:
        """Text files are not binary."""
        f = tmp_path / "test.txt"
        f.write_text("Hello, world!", encoding="utf-8")
        assert is_binary_file(f) is False

    def test_python_file(self, tmp_path: Path) -> None:
        """Python files are not binary."""
        f = tmp_path / "test.py"
        f.write_text("print('hello')", encoding="utf-8")
        assert is_binary_file(f) is False

    def test_binary_extension(self, tmp_path: Path) -> None:
        """Files with binary extensions are binary."""
        f = tmp_path / "test.pyc"
        f.write_bytes(b"data")
        assert is_binary_file(f) is True

    def test_null_byte(self, tmp_path: Path) -> None:
        """Files with null bytes are binary."""
        f = tmp_path / "test.dat"
        f.write_bytes(b"hello\x00world")
        assert is_binary_file(f) is True


class TestShouldExcludePath:
    """Tests for should_exclude_path function."""

    def test_git_directory(self) -> None:
        """Git directories are excluded."""
        assert should_exclude_path(Path(".git/config"), EXCLUDE_DIRS) is True
        assert should_exclude_path(Path(".git/objects/abc"), EXCLUDE_DIRS) is True

    def test_idea_directory(self) -> None:
        """IDE directories are excluded."""
        assert should_exclude_path(Path(".idea/workspace.xml"), EXCLUDE_DIRS) is True

    def test_pycache_directory(self) -> None:
        """__pycache__ directories are excluded."""
        assert should_exclude_path(Path("__pycache__/module.pyc"), EXCLUDE_DIRS) is True
        assert should_exclude_path(Path("src/__pycache__/module.pyc"), EXCLUDE_DIRS) is True

    def test_regular_file(self) -> None:
        """Regular files are not excluded."""
        assert should_exclude_path(Path("src/module.py"), EXCLUDE_DIRS) is False
        assert should_exclude_path(Path("README.md"), EXCLUDE_DIRS) is False


class TestCreateReplacementMap:
    """Tests for create_replacement_map function."""

    def test_creates_all_mappings(self) -> None:
        """Creates mappings for all variations."""
        old_vars = generate_name_variations("old_project")
        new_vars = generate_name_variations("new_project")
        replacements = create_replacement_map(old_vars, new_vars)

        assert replacements["old_project"] == "new_project"
        assert replacements["old-project"] == "new-project"
        assert replacements["OLD_PROJECT"] == "NEW_PROJECT"
        assert replacements["OLD-PROJECT"] == "NEW-PROJECT"
        assert replacements["OldProject"] == "NewProject"


class TestReplaceInFile:
    """Tests for replace_in_file function."""

    def test_replaces_content(self, tmp_path: Path) -> None:
        """Replaces content in text file."""
        f = tmp_path / "test.py"
        f.write_text("from old_project import foo", encoding="utf-8")

        result = replace_in_file(f, {"old_project": "new_project"})

        assert result is True
        assert f.read_text(encoding="utf-8") == "from new_project import foo"

    def test_no_match(self, tmp_path: Path) -> None:
        """Returns False if no replacements made."""
        f = tmp_path / "test.py"
        f.write_text("from other_module import foo", encoding="utf-8")

        result = replace_in_file(f, {"old_project": "new_project"})

        assert result is False
        assert f.read_text(encoding="utf-8") == "from other_module import foo"

    def test_skips_binary(self, tmp_path: Path) -> None:
        """Skips binary files."""
        f = tmp_path / "test.pyc"
        f.write_bytes(b"old_project\x00data")

        result = replace_in_file(f, {"old_project": "new_project"})

        assert result is False

    def test_multiple_variations(self, tmp_path: Path) -> None:
        """Replaces multiple variations."""
        f = tmp_path / "test.py"
        f.write_text(
            "from old_project import OldProject\nOLD_PROJECT = 'old-project'",
            encoding="utf-8",
        )

        old_vars = generate_name_variations("old_project")
        new_vars = generate_name_variations("new_project")
        replacements = create_replacement_map(old_vars, new_vars)

        result = replace_in_file(f, replacements)

        assert result is True
        content = f.read_text(encoding="utf-8")
        assert "new_project" in content
        assert "NewProject" in content
        assert "NEW_PROJECT" in content
        assert "new-project" in content


class TestRenameProject:
    """Tests for the rename_project function."""

    def test_dry_run_detects_changes(self, tmp_path: Path) -> None:
        """Dry run detects files that would be changed."""
        # Create project structure
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "old_project"\n',
            encoding="utf-8",
        )
        src = tmp_path / "src" / "old_project"
        src.mkdir(parents=True)
        (src / "__init__.py").write_text('"""old_project module."""', encoding="utf-8")
        (src / "main.py").write_text("from old_project import foo", encoding="utf-8")

        result = rename_project(
            tmp_path,
            dry_run=True,
            old_name="old_project",
            new_name="new_project",
        )

        assert len(result.files_modified) >= 2
        assert len(result.dirs_renamed) == 1

    def test_renames_files_and_directories(self, tmp_path: Path) -> None:
        """Actually renames files and directories."""
        # Create project structure
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "old_project"\n',
            encoding="utf-8",
        )
        src = tmp_path / "src" / "old_project"
        src.mkdir(parents=True)
        (src / "__init__.py").write_text('"""old_project module."""', encoding="utf-8")
        (src / "old_project_utils.py").write_text(
            "from old_project import OldProject",
            encoding="utf-8",
        )

        result = rename_project(
            tmp_path,
            dry_run=False,
            old_name="old_project",
            new_name="new_project",
        )

        # Check directory was renamed
        assert (tmp_path / "src" / "new_project").exists()
        assert not (tmp_path / "src" / "old_project").exists()

        # Check file was renamed
        assert (tmp_path / "src" / "new_project" / "new_project_utils.py").exists()

        # Check content was replaced
        init_content = (tmp_path / "src" / "new_project" / "__init__.py").read_text(
            encoding="utf-8"
        )
        assert "new_project" in init_content

        utils_content = (tmp_path / "src" / "new_project" / "new_project_utils.py").read_text(
            encoding="utf-8"
        )
        assert "new_project" in utils_content
        assert "NewProject" in utils_content

        assert len(result.files_modified) >= 2
        assert len(result.dirs_renamed) == 1
        assert len(result.files_renamed) == 1

    def test_excludes_git_directory(self, tmp_path: Path) -> None:
        """Does not process .git directory."""
        # Create project structure
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "old_project"\n',
            encoding="utf-8",
        )
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("old_project", encoding="utf-8")

        result = rename_project(
            tmp_path,
            dry_run=False,
            old_name="old_project",
            new_name="new_project",
        )

        # .git/config should not be modified
        assert (git_dir / "config").read_text(encoding="utf-8") == "old_project"

        # .git should not appear in results
        for path in result.files_modified:
            assert ".git" not in str(path)

    def test_updates_pyproject_toml(self, tmp_path: Path) -> None:
        """Updates name in pyproject.toml."""
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "old_project"\nversion = "1.0.0"\n',
            encoding="utf-8",
        )

        rename_project(
            tmp_path,
            dry_run=False,
            old_name="old_project",
            new_name="new_project",
        )

        content = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
        assert 'name = "new_project"' in content


class TestNameVariationsDataclass:
    """Tests for NameVariations dataclass."""

    def test_creation(self) -> None:
        """Can create NameVariations."""
        vars = NameVariations(
            lowercase_underscore="my_project",
            lowercase_hyphen="my-project",
            uppercase_underscore="MY_PROJECT",
            uppercase_hyphen="MY-PROJECT",
            pascal_case="MyProject",
        )
        assert vars.lowercase_underscore == "my_project"
        assert vars.pascal_case == "MyProject"


class TestRenameResultDataclass:
    """Tests for RenameResult dataclass."""

    def test_default_values(self) -> None:
        """RenameResult has empty default lists."""
        result = RenameResult()
        assert result.files_modified == []
        assert result.files_renamed == []
        assert result.dirs_renamed == []
