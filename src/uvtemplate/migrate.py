"""
Project analysis and migration recommendations for uvtemplate migrate command.
"""

from __future__ import annotations

import configparser
import subprocess
import tomllib
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from rich.panel import Panel
from rich.rule import Rule

from uvtemplate.copier_workflow import DEFAULT_TEMPLATE
from uvtemplate.shell_utils import print_subtle, print_success, print_warning, rprint

# Default template version to use when adopting a template
# This should be updated when new template versions are released
DEFAULT_TEMPLATE_VERSION = "v0.2.20"


class BuildSystem(StrEnum):
    """Detected build system types."""

    UV = "uv"
    POETRY = "poetry"
    PDM = "pdm"
    FLIT = "flit"
    SETUPTOOLS = "setuptools"
    PIPENV = "pipenv"
    REQUIREMENTS = "requirements"
    UNKNOWN = "unknown"


@dataclass
class TemplateVariables:
    """Extracted template variables for .copier-answers.yml."""

    package_name: str | None = None
    package_module: str | None = None
    package_description: str | None = None
    package_author_name: str | None = None
    package_author_email: str | None = None
    package_github_org: str | None = None

    def to_answers_dict(self, template_src: str, template_version: str) -> dict[str, Any]:
        """Convert to a copier answers dictionary."""
        answers: dict[str, Any] = {
            "_commit": template_version,
            "_src_path": template_src,
        }
        if self.package_name:
            answers["package_name"] = self.package_name
        if self.package_module:
            answers["package_module"] = self.package_module
        if self.package_description:
            answers["package_description"] = self.package_description
        if self.package_author_name:
            answers["package_author_name"] = self.package_author_name
        if self.package_author_email:
            answers["package_author_email"] = self.package_author_email
        if self.package_github_org:
            answers["package_github_org"] = self.package_github_org
        return answers

    def get_missing_fields(self) -> list[str]:
        """Return list of fields that are None or 'changeme'."""
        field_names = [
            "package_name",
            "package_module",
            "package_description",
            "package_author_name",
            "package_author_email",
            "package_github_org",
        ]
        return [
            name
            for name in field_names
            if (value := getattr(self, name)) is None or value == "changeme"
        ]


@dataclass
class ProjectAnalysis:
    """Results of analyzing a project."""

    build_system: BuildSystem
    project_dir: Path
    detected_files: list[str] = field(default_factory=list)
    package_name: str | None = None
    python_requires: str | None = None
    warnings: list[str] = field(default_factory=list)
    # Copier template info (if project was created from a template)
    copier_template: str | None = None
    copier_version: str | None = None
    # Extracted template variables for adoption
    template_vars: TemplateVariables = field(default_factory=TemplateVariables)


def analyze_project(project_dir: Path) -> ProjectAnalysis:
    """
    Analyze a project directory and detect its build system and metadata.
    """
    build_system, detected_files = detect_build_system(project_dir)

    analysis = ProjectAnalysis(
        build_system=build_system,
        project_dir=project_dir,
        detected_files=detected_files,
    )

    # Check for .copier-answers.yml (indicates project was created from a copier template)
    _extract_copier_info(analysis)

    # Try to extract metadata from pyproject.toml if it exists
    pyproject: dict[str, Any] | None = None
    pyproject_path = project_dir / "pyproject.toml"
    if pyproject_path.exists():
        try:
            with open(pyproject_path, "rb") as f:
                pyproject = tomllib.load(f)
            _extract_metadata(analysis, pyproject)
        except Exception as e:
            analysis.warnings.append(f"Could not parse pyproject.toml: {e}")

    # Try to extract from other sources based on build system
    if build_system == BuildSystem.PIPENV:
        _extract_pipenv_metadata(analysis)
    elif build_system == BuildSystem.SETUPTOOLS:
        _extract_setuptools_metadata(analysis)

    # Extract template variables for potential adoption
    _extract_template_variables(analysis, pyproject)

    return analysis


def detect_build_system(project_dir: Path) -> tuple[BuildSystem, list[str]]:
    """
    Detect build system by checking for signature files.
    Returns (build_system, list_of_detected_files).
    """
    detected_files: list[str] = []
    pyproject_path = project_dir / "pyproject.toml"
    pyproject: dict[str, Any] | None = None

    # Parse pyproject.toml if it exists
    if pyproject_path.exists():
        detected_files.append("pyproject.toml")
        try:
            with open(pyproject_path, "rb") as f:
                pyproject = tomllib.load(f)
        except Exception:
            pass

    # Check for uv (already migrated)
    if (project_dir / "uv.lock").exists():
        detected_files.append("uv.lock")
        return BuildSystem.UV, detected_files
    if pyproject and "tool" in pyproject and "uv" in pyproject["tool"]:
        detected_files.append("pyproject.toml with [tool.uv]")
        return BuildSystem.UV, detected_files

    # Check for Poetry
    if (project_dir / "poetry.lock").exists():
        detected_files.append("poetry.lock")
        return BuildSystem.POETRY, detected_files
    if pyproject and "tool" in pyproject and "poetry" in pyproject["tool"]:
        detected_files.append("pyproject.toml with [tool.poetry]")
        return BuildSystem.POETRY, detected_files

    # Check for PDM
    if (project_dir / "pdm.lock").exists():
        detected_files.append("pdm.lock")
        return BuildSystem.PDM, detected_files
    if pyproject and "tool" in pyproject and "pdm" in pyproject["tool"]:
        detected_files.append("pyproject.toml with [tool.pdm]")
        return BuildSystem.PDM, detected_files

    # Check for Flit
    if pyproject and "tool" in pyproject and "flit" in pyproject["tool"]:
        detected_files.append("pyproject.toml with [tool.flit]")
        return BuildSystem.FLIT, detected_files

    # Check for setuptools
    if (project_dir / "setup.py").exists():
        detected_files.append("setup.py")
        return BuildSystem.SETUPTOOLS, detected_files
    if (project_dir / "setup.cfg").exists():
        detected_files.append("setup.cfg")
        return BuildSystem.SETUPTOOLS, detected_files

    # Check for Pipenv
    if (project_dir / "Pipfile").exists():
        detected_files.append("Pipfile")
        if (project_dir / "Pipfile.lock").exists():
            detected_files.append("Pipfile.lock")
        return BuildSystem.PIPENV, detected_files

    # Check for requirements.txt
    if (project_dir / "requirements.txt").exists():
        detected_files.append("requirements.txt")
        return BuildSystem.REQUIREMENTS, detected_files

    return BuildSystem.UNKNOWN, detected_files


def _extract_metadata(analysis: ProjectAnalysis, pyproject: dict[str, Any]) -> None:
    """Extract metadata from pyproject.toml based on build system."""
    # Try standard [project] section first
    if "project" in pyproject:
        project: dict[str, Any] = pyproject["project"]
        analysis.package_name = project.get("name")
        analysis.python_requires = project.get("requires-python")

    # Poetry-specific extraction
    if analysis.build_system == BuildSystem.POETRY:
        poetry: dict[str, Any] = pyproject.get("tool", {}).get("poetry", {})
        if not analysis.package_name:
            analysis.package_name = poetry.get("name")
        if not analysis.python_requires:
            # Poetry uses "python" in dependencies
            deps: dict[str, Any] = poetry.get("dependencies", {})
            if "python" in deps:
                analysis.python_requires = deps["python"]

    # PDM-specific extraction
    if analysis.build_system == BuildSystem.PDM:
        pdm: dict[str, Any] = pyproject.get("tool", {}).get("pdm", {})
        if not analysis.package_name:
            analysis.package_name = pdm.get("name")

    # Flit-specific extraction
    if analysis.build_system == BuildSystem.FLIT:
        flit: dict[str, Any] = pyproject.get("tool", {}).get("flit", {}).get("metadata", {})
        if not analysis.package_name:
            analysis.package_name = flit.get("module")


def _extract_pipenv_metadata(analysis: ProjectAnalysis) -> None:
    """Extract metadata from Pipfile."""
    pipfile_path = analysis.project_dir / "Pipfile"
    if not pipfile_path.exists():
        return

    try:
        content = pipfile_path.read_text()
        # Simple parsing for python_version
        for line in content.splitlines():
            if "python_version" in line and "=" in line:
                # Extract version from line like: python_version = "3.11"
                version = line.split("=")[1].strip().strip('"').strip("'")
                analysis.python_requires = f">={version}"
                break
    except Exception as e:
        analysis.warnings.append(f"Could not parse Pipfile: {e}")


def _extract_setuptools_metadata(analysis: ProjectAnalysis) -> None:
    """Extract metadata from setup.py or setup.cfg."""
    setup_cfg = analysis.project_dir / "setup.cfg"
    if setup_cfg.exists():
        try:
            config = configparser.ConfigParser()
            config.read(setup_cfg)
            if config.has_option("metadata", "name"):
                analysis.package_name = config.get("metadata", "name")
            if config.has_option("options", "python_requires"):
                analysis.python_requires = config.get("options", "python_requires")
        except Exception as e:
            analysis.warnings.append(f"Could not parse setup.cfg: {e}")


def _extract_copier_info(analysis: ProjectAnalysis) -> None:
    """Extract copier template information from .copier-answers.yml."""
    answers_path = analysis.project_dir / ".copier-answers.yml"
    if not answers_path.exists():
        return

    analysis.detected_files.append(".copier-answers.yml")

    try:
        answers: dict[str, Any] = yaml.safe_load(answers_path.read_text()) or {}
        analysis.copier_template = answers.get("_src_path")
        analysis.copier_version = answers.get("_commit")
    except Exception as e:
        analysis.warnings.append(f"Could not parse .copier-answers.yml: {e}")


def _extract_template_variables(
    analysis: ProjectAnalysis, pyproject: dict[str, Any] | None
) -> None:
    """
    Extract template variables from pyproject.toml, git, and project structure.
    Populates analysis.template_vars with best-effort extraction.
    """
    tv = analysis.template_vars

    # Extract from [project] section of pyproject.toml (standard PEP 621)
    if pyproject and "project" in pyproject:
        project = pyproject["project"]

        # package_name
        if project.get("name"):
            tv.package_name = project["name"]

        # package_description
        if project.get("description"):
            tv.package_description = project["description"]

        # package_author_name and package_author_email from authors list
        authors = project.get("authors", [])
        if authors and isinstance(authors[0], dict):
            first_author = authors[0]
            if first_author.get("name"):
                tv.package_author_name = first_author["name"]
            if first_author.get("email"):
                tv.package_author_email = first_author["email"]

    # Extract from [tool.poetry] section for Poetry projects
    if pyproject and analysis.build_system == BuildSystem.POETRY:
        poetry = pyproject.get("tool", {}).get("poetry", {})

        # package_name (if not already found)
        if not tv.package_name and poetry.get("name"):
            tv.package_name = poetry["name"]

        # package_description (if not already found)
        if not tv.package_description and poetry.get("description"):
            tv.package_description = poetry["description"]

        # Poetry authors format: ["Name <email>"] or ["Name"]
        if not tv.package_author_name:
            authors = poetry.get("authors", [])
            if authors:
                first_author = authors[0]
                # Parse "Name <email>" format
                if "<" in first_author and ">" in first_author:
                    name_part = first_author.split("<")[0].strip()
                    email_part = first_author.split("<")[1].rstrip(">").strip()
                    tv.package_author_name = name_part
                    if not tv.package_author_email:
                        tv.package_author_email = email_part
                else:
                    tv.package_author_name = first_author.strip()

    # Try to detect package_module from src/ directory or root-level packages
    if not tv.package_module:
        tv.package_module = _detect_package_module(analysis.project_dir)

    # If we have package_name but not module, derive module from name
    if tv.package_name and not tv.package_module:
        # Convert kebab-case to snake_case
        tv.package_module = tv.package_name.replace("-", "_")

    # Try to extract github org from git remote
    if not tv.package_github_org:
        tv.package_github_org = _extract_github_org_from_git(analysis.project_dir)


def _detect_package_module(project_dir: Path) -> str | None:
    """
    Detect the Python module name from directory structure.
    Checks both src/<module_name>/__init__.py (src layout) and
    <module_name>/__init__.py (flat layout) patterns.
    """
    # First, try src/ layout (preferred modern layout)
    src_dir = project_dir / "src"
    if src_dir.exists():
        for item in src_dir.iterdir():
            if item.is_dir() and (item / "__init__.py").exists():
                # Skip common non-module directories
                if item.name not in ("__pycache__", ".pytest_cache", "tests"):
                    return item.name

    # Then, try flat/root layout (common in older projects)
    # Skip common non-module directories
    skip_dirs = {
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        ".venv",
        "venv",
        ".git",
        ".github",
        ".claude",
        "tests",
        "test",
        "docs",
        "doc",
        "build",
        "dist",
        "devtools",
        "scripts",
        "images",
        "node_modules",
    }
    for item in project_dir.iterdir():
        if item.is_dir() and (item / "__init__.py").exists():
            if item.name not in skip_dirs and not item.name.startswith("."):
                return item.name

    return None


def _extract_github_org_from_git(project_dir: Path) -> str | None:
    """
    Extract GitHub organization/username from git remote URL.
    Handles both SSH (git@github.com:org/repo.git) and HTTPS (https://github.com/org/repo.git) formats.
    """
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return None

        remote_url = result.stdout.strip()

        # SSH format: git@github.com:org/repo.git
        if remote_url.startswith("git@github.com:"):
            path = remote_url.replace("git@github.com:", "").rstrip(".git")
            parts = path.split("/")
            if len(parts) >= 1:
                return parts[0]

        # HTTPS format: https://github.com/org/repo.git
        if "github.com/" in remote_url:
            # Extract path after github.com/
            path = remote_url.split("github.com/")[-1].rstrip(".git")
            parts = path.split("/")
            if len(parts) >= 1:
                return parts[0]

    except Exception:
        pass

    return None


def write_copier_answers(
    project_dir: Path,
    template_vars: TemplateVariables,
    template_src: str = DEFAULT_TEMPLATE,
    template_version: str = DEFAULT_TEMPLATE_VERSION,
) -> Path:
    """
    Write .copier-answers.yml file to enable future template updates.
    Returns the path to the created file.
    """
    answers = template_vars.to_answers_dict(template_src, template_version)
    answers_path = project_dir / ".copier-answers.yml"

    # Write with the standard copier header comment
    content = "# Changes here will be overwritten by Copier. Do not edit manually.\n"
    content += yaml.dump(answers, default_flow_style=False, sort_keys=True)

    answers_path.write_text(content)
    return answers_path


def generate_recommendations(analysis: ProjectAnalysis) -> list[str]:
    """Generate migration recommendations based on analysis."""
    recommendations: list[str] = []

    if analysis.build_system == BuildSystem.UV:
        if analysis.copier_template:
            # Project was created from a copier template - suggest update
            recommendations.append(
                "This project was created from a copier template. To update to the latest template version:\n"
                "   uvtemplate update\n"
                "\n"
                "Or run copier directly:\n"
                "   copier update"
            )
        else:
            recommendations.append(
                "This project already uses uv. No migration needed.\n"
                "\n"
                "Note: This project was not created from a copier template,\n"
                "so automatic template updates are not available."
            )
        return recommendations

    if analysis.build_system == BuildSystem.UNKNOWN:
        recommendations.append(
            "Could not detect a build system. You may need to create a pyproject.toml from scratch."
        )
        recommendations.append("Run: uvtemplate create --skip-git --destination .uvtemplate-ref")
        recommendations.append("Then copy the pyproject.toml structure to your project.")
        return recommendations

    # Common first step: reference the template
    recommendations.append(
        "REFERENCE the template pyproject.toml:\n"
        "   https://github.com/jlevy/simple-modern-uv/blob/main/template/pyproject.toml.jinja\n"
        "   (Or run: uvtemplate create --skip-git --destination .uvtemplate-ref)"
    )

    # Build system specific recommendations
    # Note: Use \[ to escape brackets so Rich doesn't interpret them as markup
    if analysis.build_system == BuildSystem.POETRY:
        recommendations.append(
            "UPDATE pyproject.toml:\n"
            "   - Replace \\[build-system] with hatchling (see template)\n"
            "   - Move \\[tool.poetry.dependencies] to \\[project.dependencies]\n"
            "   - Move dev dependencies to \\[dependency-groups.dev]\n"
            "   - Add \\[tool.ruff], \\[tool.basedpyright], \\[tool.pytest.ini_options] from template\n"
            "   - Remove \\[tool.poetry] section entirely"
        )
        recommendations.append(
            "CONVERT dependency syntax (Poetry → PEP 621):\n"
            '   - python = "^3.10"       →  requires-python = ">=3.10"\n'
            '   - requests = "^2.28"     →  "requests>=2.28"\n'
            '   - click = "~8.0"         →  "click>=8.0,<8.1"\n'
            '   - foo = { version = "^1.0", extras = ["bar"] }  →  "foo[bar]>=1.0"'
        )
        recommendations.append(
            "DELETE obsolete files:\n   - poetry.lock (uv sync will create uv.lock)"
        )

    elif analysis.build_system == BuildSystem.SETUPTOOLS:
        recommendations.append(
            "UPDATE pyproject.toml:\n"
            "   - Add \\[build-system] with hatchling (see template)\n"
            "   - Move metadata from setup.py/setup.cfg to \\[project] section\n"
            "   - Add \\[tool.ruff], \\[tool.basedpyright], \\[tool.pytest.ini_options] from template"
        )
        files_to_delete: list[str] = []
        if (analysis.project_dir / "setup.py").exists():
            files_to_delete.append("setup.py")
        if (analysis.project_dir / "setup.cfg").exists():
            files_to_delete.append("setup.cfg")
        if (analysis.project_dir / "MANIFEST.in").exists():
            files_to_delete.append("MANIFEST.in")
        if files_to_delete:
            recommendations.append(
                "DELETE obsolete files:\n   - " + "\n   - ".join(files_to_delete)
            )

    elif analysis.build_system == BuildSystem.PDM:
        recommendations.append(
            "UPDATE pyproject.toml:\n"
            "   - Replace \\[build-system] with hatchling (see template)\n"
            "   - Keep \\[project] section (PDM uses standard format)\n"
            "   - Move \\[tool.pdm.dev-dependencies] to \\[dependency-groups.dev]\n"
            "   - Add \\[tool.ruff], \\[tool.basedpyright], \\[tool.pytest.ini_options] from template\n"
            "   - Remove \\[tool.pdm] section"
        )
        recommendations.append(
            "DELETE obsolete files:\n   - pdm.lock (uv sync will create uv.lock)"
        )

    elif analysis.build_system == BuildSystem.FLIT:
        recommendations.append(
            "UPDATE pyproject.toml:\n"
            "   - Replace \\[build-system] with hatchling (see template)\n"
            "   - Move \\[tool.flit.metadata] to \\[project] section\n"
            "   - Add \\[tool.ruff], \\[tool.basedpyright], \\[tool.pytest.ini_options] from template\n"
            "   - Remove \\[tool.flit] section"
        )

    elif analysis.build_system == BuildSystem.PIPENV:
        recommendations.append(
            "CREATE pyproject.toml:\n"
            "   - Copy structure from template\n"
            "   - Move \\[packages] from Pipfile to \\[project.dependencies]\n"
            "   - Move \\[dev-packages] from Pipfile to \\[dependency-groups.dev]"
        )
        recommendations.append("DELETE obsolete files:\n   - Pipfile\n   - Pipfile.lock")

    elif analysis.build_system == BuildSystem.REQUIREMENTS:
        recommendations.append(
            "CREATE pyproject.toml:\n"
            "   - Copy structure from template\n"
            "   - Move dependencies from requirements.txt to \\[project.dependencies]\n"
            "   - If you have requirements-dev.txt, move to \\[dependency-groups.dev]"
        )
        recommendations.append(
            "OPTIONALLY delete:\n   - requirements.txt (after migrating deps to pyproject.toml)"
        )

    # Common recommendations for all build systems
    recommendations.append(
        "COPY from template:\n"
        "   - .github/workflows/ci.yml\n"
        "   - .github/workflows/publish.yml\n"
        "   - Makefile\n"
        "   - devtools/lint.py\n"
        "   - docs/development.md (optional)\n"
        "   - docs/publishing.md (optional)"
    )

    recommendations.append("RUN:\n   uv sync")

    return recommendations


def run_migration(analysis: ProjectAnalysis) -> None:
    """Run the migration: create answers file, display analysis, and show next steps."""
    rprint()
    rprint(Rule("Project Analysis"))
    rprint()

    # Build system detection
    if analysis.build_system == BuildSystem.UV:
        print_success("This project already uses uv!")
        rprint()

        # Show copier template info if available
        if analysis.copier_template:
            rprint(f"[bold]Template:[/bold] {analysis.copier_template}")
            if analysis.copier_version:
                rprint(f"[bold]Version:[/bold] {analysis.copier_version}")
            rprint()

            # Already has answers file - just suggest update
            rprint(Rule("Next Steps"))
            rprint()
            rprint("This project is already set up for template updates. Run:")
            rprint()
            rprint("   [bold cyan]uvtemplate update[/bold cyan]")
            rprint()
            rprint("Or run copier directly:")
            rprint()
            rprint("   [bold cyan]copier update[/bold cyan]")
            return

        # UV project but no copier answers - we'll create one
        rprint("This project uses uv but was not created from a copier template.")
        rprint()

    elif analysis.build_system == BuildSystem.UNKNOWN:
        print_warning("Could not detect a build system")
    else:
        rprint(f"[bold]Detected:[/bold] {analysis.build_system.value.title()} project")

    # Show detected files
    if analysis.detected_files:
        for f in analysis.detected_files:
            print_subtle(f"  Found: {f}")

    # Show extracted metadata
    rprint()
    if analysis.package_name:
        rprint(f"[bold]Package:[/bold] {analysis.package_name}")
    if analysis.python_requires:
        rprint(f"[bold]Python:[/bold] {analysis.python_requires}")

    # Show warnings
    if analysis.warnings:
        rprint()
        for warning in analysis.warnings:
            print_warning(warning)

    # Display extracted template variables
    rprint()
    rprint(Rule("Extracted Template Variables"))
    rprint()

    tv = analysis.template_vars
    _display_template_var("package_name", tv.package_name)
    _display_template_var("package_module", tv.package_module)
    _display_template_var("package_description", tv.package_description)
    _display_template_var("package_author_name", tv.package_author_name)
    _display_template_var("package_author_email", tv.package_author_email)
    _display_template_var("package_github_org", tv.package_github_org)

    # Check if answers file already exists
    answers_path = analysis.project_dir / ".copier-answers.yml"
    if answers_path.exists():
        rprint()
        print_warning(f".copier-answers.yml already exists at {answers_path}")
        rprint("Skipping creation. Delete it first if you want to regenerate.")
    else:
        # Create the answers file
        rprint()
        rprint(Rule("Creating .copier-answers.yml"))
        rprint()

        try:
            created_path = write_copier_answers(
                analysis.project_dir,
                analysis.template_vars,
                template_src=DEFAULT_TEMPLATE,
                template_version=DEFAULT_TEMPLATE_VERSION,
            )
            print_success(f"Created: {created_path}")
            rprint()
            rprint("[dim]This file enables future template updates with 'uvtemplate update'.[/dim]")
        except Exception as e:
            print_warning(f"Could not create .copier-answers.yml: {e}")

    # Show missing fields that need review
    missing = tv.get_missing_fields()
    if missing:
        rprint()
        print_warning("Some fields could not be extracted and may need manual editing:")
        for field in missing:
            rprint(f"   - {field}")
        rprint()
        rprint("[dim]Edit .copier-answers.yml to fill in missing values.[/dim]")

    # Generate and display migration recommendations
    rprint()
    rprint(Rule("Migration Recommendations"))
    rprint()

    recommendations = generate_recommendations(analysis)

    if analysis.build_system != BuildSystem.UV:
        rprint("To complete the migration to uv:\n")

        for i, rec in enumerate(recommendations, 1):
            # Format as a numbered list with the action highlighted
            lines = rec.split("\n")
            action = lines[0]
            details = "\n".join(lines[1:]) if len(lines) > 1 else ""

            rprint(f"[bold cyan]{i}.[/bold cyan] [bold]{action}[/bold]")
            if details:
                rprint(f"[dim]{details}[/dim]")
            rprint()

    # Show next steps - different for UV vs other build systems
    rprint()
    rprint(Rule("Next Steps"))
    rprint()

    if analysis.build_system != BuildSystem.UV:
        # For non-UV projects, emphasize manual migration first
        rprint(
            "[bold yellow]⚠ Important:[/bold yellow] This is a [bold]guided manual migration[/bold]."
        )
        rprint()
        rprint(
            "[dim]uvtemplate update does NOT automatically transform your pyproject.toml.\n"
            "You must manually update your pyproject.toml first (see recommendations above),\n"
            "then use uvtemplate update to pull in CI workflows, Makefile, etc.[/dim]"
        )
        rprint()
        rprint("1. [bold]Manually update[/bold] pyproject.toml following the recommendations above")
        rprint(
            "   [dim]See template reference for examples: https://github.com/jlevy/simple-modern-uv[/dim]"
        )
        rprint()
        rprint("2. [bold]Run[/bold] uv sync to verify your pyproject.toml is valid:")
        rprint()
        rprint("   [bold cyan]uv sync[/bold cyan]")
        rprint()
        rprint("3. [bold]Commit[/bold] your changes, including .copier-answers.yml:")
        rprint()
        rprint(
            "   [bold cyan]git add -A && git commit -m 'Migrate to uv with simple-modern-uv template'[/bold cyan]"
        )
        rprint()
        rprint("4. [bold]Optionally run[/bold] uvtemplate update to pull in CI/tooling files:")
        rprint()
        rprint("   [bold cyan]uvtemplate update[/bold cyan]")
        rprint()
        rprint(
            "[dim]This will show merge conflicts for files like .github/workflows/*.yml.\n"
            "Resolve conflicts by choosing template or existing versions, then commit.[/dim]"
        )
    else:
        # For UV projects, simpler flow
        rprint("1. [bold]Review[/bold] the .copier-answers.yml file and edit any incorrect values")
        rprint()
        rprint("2. [bold]Commit[/bold] the answers file:")
        rprint()
        rprint(
            "   [bold cyan]git add .copier-answers.yml && git commit -m 'Add copier answers for template adoption'[/bold cyan]"
        )
        rprint()
        rprint("3. [bold]Run[/bold] uvtemplate update to sync with template:")
        rprint()
        rprint("   [bold cyan]uvtemplate update[/bold cyan]")

    # Footer with link to docs
    rprint()
    rprint(
        Panel(
            "For template reference: [link=https://github.com/jlevy/simple-modern-uv]https://github.com/jlevy/simple-modern-uv[/link]",
            style="dim",
        )
    )


def _display_template_var(name: str, value: str | None) -> None:
    """Display a template variable with its extraction status."""
    if value and value != "changeme":
        rprint(f"  [green]✓[/green] {name}: [bold]{value}[/bold]")
    elif value == "changeme":
        rprint(f"  [yellow]?[/yellow] {name}: [dim]changeme (needs review)[/dim]")
    else:
        rprint(f"  [red]✗[/red] {name}: [dim]not found[/dim]")
