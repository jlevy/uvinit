from pathlib import Path
from typing import Any

import copier
import questionary
import yaml
from prettyfmt import fmt_path

from uvinit.github_settings import get_github_defaults
from uvinit.shell_utils import (
    Cancelled,
    print_subtle,
    print_success,
    print_warning,
    rprint,
)

DEFAULT_TEMPLATE = "gh:jlevy/simple-modern-uv"


def read_copier_answers(project_path: Path) -> dict[str, Any]:
    """
    Read the copier answers file to extract project metadata.

    # Sample answers file:
    _commit: v0.2.3
    _src_path: gh:jlevy/simple-modern-uv
    package_author_email: changeme@example.com
    package_author_name: changeme
    package_description: changeme
    package_github_org: changeme
    package_module: changeme
    package_name: changeme
    """
    answers_path = project_path / ".copier-answers.yml"

    if not answers_path.exists():
        raise ValueError(f"Answers file not found: {answers_path}")
    print_subtle(f"Reading answers from: {answers_path}")
    try:
        with open(answers_path) as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print_warning(f"Could not read answers file: {e}")
        return {}


def copy_template(
    src_path: str,
    dst_path: str | None = None,
    answers_file: str | None = None,
    user_defaults: dict[str, Any] | None = None,
) -> Path:
    """
    Create a new Python project using copier with user confirmation.
    """
    # If no destination is provided, prompt for it
    if dst_path is None:
        dst_path = questionary.text(
            "Destination directory (usually kebab-case or snake_case):",
            default="changeme",
        ).ask()

        if not dst_path:
            print_warning("No destination provided.")
            raise Cancelled()

    # Extract project name from destination path to pre-fill answers
    project_name = Path(dst_path).name

    github_defaults = get_github_defaults()

    # Initialize user_defaults if not provided
    if user_defaults is None:
        user_defaults = {}

    # Prepare default data based on the destination directory name
    # and GitHub defaults, if available.
    user_defaults.update(
        {
            # kebab-case for package name
            "package_name": "-".join(project_name.split()).replace("_", "-"),
            # snake_case for module name
            "package_module": "".join(project_name.split()).replace("-", "_"),
            # Add GitHub defaults
            "package_author_name": github_defaults.author_name or "changeme",
            "package_author_email": github_defaults.author_email or "changeme@example.com",
            "package_github_org": github_defaults.github_username or "changeme",
        }
    )

    rprint()
    rprint(f"Creating project from: [bold blue]{src_path}[/bold blue]")
    rprint()
    rprint(f"Destination: [bold blue]{fmt_path(dst_path)}[/bold blue]")
    rprint()
    # Ask for confirmation using questionary to match copier's style
    rprint("We will now instantiate the template with:")
    rprint()
    rprint(f"[bold blue]copier copy {src_path} {dst_path}[/bold blue]")
    rprint()
    print_subtle(
        f"Current settings (you will still be able to change these): user_defaults={user_defaults}, answers_file={answers_file}"
    )
    rprint()
    if not questionary.confirm("Proceed with copying the template?", default=True).ask():
        raise Cancelled()

    try:
        rprint()
        copier.run_copy(
            src_path=src_path,
            dst_path=dst_path,
            user_defaults=user_defaults,
            answers_file=answers_file,
        )
    except (KeyboardInterrupt, copier.CopierAnswersInterrupt):
        raise Cancelled() from None

    print_success(message="Project template copied successfully.")

    return Path(dst_path)
