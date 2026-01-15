"""
Project analysis and migration recommendations for uvtemplate migrate command.
"""

import tomllib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from rich.panel import Panel
from rich.rule import Rule

from uvtemplate.shell_utils import print_subtle, print_success, print_warning, rprint


class BuildSystem(Enum):
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
    # Try setup.cfg first (safer to parse)
    setup_cfg = analysis.project_dir / "setup.cfg"
    if setup_cfg.exists():
        try:
            import configparser

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
    import yaml

    answers_path = analysis.project_dir / ".copier-answers.yml"
    if not answers_path.exists():
        return

    analysis.detected_files.append(".copier-answers.yml")

    try:
        with open(answers_path) as f:
            answers: dict[str, Any] = yaml.safe_load(f) or {}

        # Extract template source and version
        analysis.copier_template = answers.get("_src_path")
        analysis.copier_version = answers.get("_commit")
    except Exception as e:
        analysis.warnings.append(f"Could not parse .copier-answers.yml: {e}")


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

    # Common first step: create reference template
    recommendations.append(
        "CREATE a fresh template for reference:\n"
        "   uvtemplate create --skip-git --destination .uvtemplate-ref"
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

    recommendations.append(
        "CLEANUP:\n   rm -rf .uvtemplate-ref  # Remove the reference template when done"
    )

    return recommendations


def display_analysis(analysis: ProjectAnalysis) -> None:
    """Display the project analysis and migration recommendations."""
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

        # Show update recommendations
        rprint(Rule("Update Recommendations"))
        rprint()
        recommendations = generate_recommendations(analysis)
        for rec in recommendations:
            rprint(rec)
        return

    if analysis.build_system == BuildSystem.UNKNOWN:
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

    # Generate and display recommendations
    rprint()
    rprint(Rule("Migration Recommendations"))
    rprint()

    recommendations = generate_recommendations(analysis)

    rprint("To migrate this project to uv:\n")

    for i, rec in enumerate(recommendations, 1):
        # Format as a numbered list with the action highlighted
        lines = rec.split("\n")
        action = lines[0]
        details = "\n".join(lines[1:]) if len(lines) > 1 else ""

        rprint(f"[bold cyan]{i}.[/bold cyan] [bold]{action}[/bold]")
        if details:
            rprint(f"[dim]{details}[/dim]")
        rprint()

    # Footer with link to docs
    rprint(
        Panel(
            "For template reference: [link=https://github.com/jlevy/simple-modern-uv]https://github.com/jlevy/simple-modern-uv[/link]",
            style="dim",
        )
    )
