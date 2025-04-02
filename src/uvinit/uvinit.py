"""
Welcome to uvinit!

This is a fast way to have Python project template that is ready to use,
using [uv](https://docs.astral.sh/uv/), the modern Python package manager.

It sets up a Python project using [copier](https://github.com/copier-org/copier),
a templating tool, to make the whole process quick: you just run
`uvx uvinit` and then follow the prompts.

uv has greatly improved Python project setup. But it is still quite confusing
to find out the best practices to set up a real project in a simple and clean
way, with dependencies, developer workflows, CI, and publishing to PyPI as a pip.

I built this tool as I was switching to uv, to make the process of setting up
a new project as low-friction as possible.

The project template used is
[simple-modern-uv](https://github.com/jlevy/simple-modern-uv),
which aims to be minimal and modern:

- uv for project setup and dependencies.

- ruff for modern linting and formatting.

- GitHub Actions for CI and publishing workflows.

- Dynamic versioning so release and package publication is as simple as creating a tag/release on GitHub.

- Workflows for packaging and publishing to PyPI with uv.

- Type checking with BasedPyright.

- Pytest for tests.

- codespell for drop-in spell checking.

That's quite a bit, but it's just the essentials and is not intended to be complex;
the template is still very small, so you can adapt it to your needs.

This tool will ask you to confirm at each step, so there is no harm in getting
started then hitting ctrl-c to abort then rerun again.

Contact me: github.com/jlevy (email), x.com/ojoshe (DMs)

More information: git.new/uvinit
"""

import argparse
import sys
from pathlib import Path
from typing import Any

import copier
import questionary
import yaml
from prettyfmt import fmt_path
from rich.markdown import Markdown
from rich.rule import Rule
from rich_argparse.contrib import ParagraphRichHelpFormatter

from uvinit.shell_utils import (
    print_cancelled,
    print_failed,
    print_warning,
    rprint,
    run_commands_sequence,
)

APP_NAME = "uvinit"

DESCRIPTION = f"{APP_NAME}: Create a new Python project with uv using the simple-modern-uv template"

DEFAULT_TEMPLATE = "gh:jlevy/simple-modern-uv"

# Git repository setup commands template
GIT_INIT_COMMANDS = [
    ("git init", "Initialize Git repository"),
    ("git add .", "Add all files to Git"),
    ('git commit -m "Initial commit from simple-modern-uv"', "Create initial commit"),
]

GIT_REMOTE_COMMANDS = [
    ("git remote add origin {repo_url}", "Add remote repository"),
    ("git branch -M main", "Rename branch to main"),
    ("git push -u origin main", "Push to remote repository"),
]


def copy_template(
    src_path: str,
    dst_path: str | None = None,
    answers_file: str | None = None,
    user_defaults: dict[str, Any] | None = None,
) -> Path | None:
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
            rprint("[yellow]No destination provided.[/yellow]")
            print_cancelled()
            return None

    # Extract project name from destination path to pre-fill answers
    project_name = Path(dst_path).name

    # Prepare default data based on the destination directory name
    user_defaults = {
        # kebab-case for package name
        "package_name": "-".join(project_name.split()).replace("_", "-"),
        # snake_case for module name
        "package_module": "".join(project_name.split()).replace("-", "_"),
    }

    rprint()
    rprint(f"[bold]Creating project from:[/bold] [green]{src_path}[/green]")
    rprint()
    rprint(f"[bold]Destination:[/bold] {fmt_path(dst_path)}")
    rprint()
    # Ask for confirmation using questionary to match copier's style
    rprint("We will now instantiate the template with:")
    rprint()
    rprint(f"[bold blue]copier copy {src_path} {dst_path}[/bold blue]")
    rprint()
    rprint(f"With user_defaults={user_defaults}, answers_file={answers_file}", style="bright_black")
    rprint()
    if not questionary.confirm("Proceed with template copy?", default=True).ask():
        print_cancelled()
        return None

    try:
        rprint()
        copier.run_copy(
            src_path=src_path,
            dst_path=dst_path,
            user_defaults=user_defaults,
            answers_file=answers_file,
        )
    except (KeyboardInterrupt, copier.CopierAnswersInterrupt):
        print_cancelled()
        return None

    rprint("[bold green]✓ Project created successfully[/bold green]")
    return Path(dst_path)


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

    rprint(f"[bright_black]Reading answers from: {answers_path}[/bright_black]")
    try:
        with open(answers_path) as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        rprint(f"[yellow]Warning: Could not read answers file: {e}[/yellow]")
        return {}


def github_repo_url(package_github_org: str, package_name: str, protocol: str = "ssh") -> str:
    """
    Generate GitHub repository URL based on organization and package name.
    """
    if protocol == "ssh":
        return f"git@github.com:{package_github_org}/{package_name}.git"
    else:
        return f"https://github.com/{package_github_org}/{package_name}.git"


def confirm_github_repo(project_path: Path) -> str | None:
    """
    Set up a git repository for the project and push to GitHub.
    """
    # Read project metadata from copier answers
    answers = read_copier_answers(project_path)
    package_name = answers.get("package_name")
    package_github_org = answers.get("package_github_org")

    if not package_name or not package_github_org:
        rprint("[yellow]Missing package name or organization.[/yellow]")
        print_cancelled()
        return None

    # Ask for protocol preference
    choices = [
        {
            "name": f"ssh (git@github.com:{package_github_org}/{package_name}.git)",
            "value": "ssh",
        },
        {
            "name": f"https (https://github.com:{package_github_org}/{package_name}.git)",
            "value": "https",
        },
    ]

    protocol = questionary.select(
        "Select GitHub URL format:", choices=choices, default=choices[0]
    ).ask()

    repo_url = github_repo_url(package_github_org, package_name, protocol)

    rprint()
    rprint(f"This will be your GitHub repository URL: [bold yellow]{repo_url}[/bold yellow]")
    rprint()
    rprint(
        "If you haven't already created the repository, you can do it now. See: https://github.com/new"
    )
    rprint()

    if not questionary.confirm(
        "Confirm this is correct and you have created the repository?", default=True
    ).ask():
        print_cancelled()
        return None

    return repo_url


def init_git_repo(project_path: Path, repo_url: str) -> bool:
    """
    Initialize a git repository and push to GitHub.
    """

    # Run initialization commands
    if not run_commands_sequence(GIT_INIT_COMMANDS, project_path):
        return False

    # Run remote setup commands with the repo URL
    if not run_commands_sequence(GIT_REMOTE_COMMANDS, project_path, repo_url=repo_url):
        return False

    rprint("[bold green]✓ Git repository setup complete![/bold green]")
    return True


def print_git_setup_help() -> None:
    for cmd in GIT_INIT_COMMANDS + GIT_REMOTE_COMMANDS:
        rprint(f"[dim]# {cmd[1]}[/dim]")
        rprint(f"{cmd[0]}")


def print_incomplete_git_setup() -> None:
    print_warning("Git repository setup not completed.")
    rprint()
    rprint("If you want to continue, you can rerun `uvinit`.")
    rprint("Or if you want to set up the repository manually, you can use these commands:")
    print_git_setup_help()
    rprint()


ERR = 1


def get_app_version() -> str:
    try:
        from importlib.metadata import version

        return "v" + version(APP_NAME)
    except Exception:
        return "unknown"


def main() -> int:
    """
    Main entry point for the CLI.
    """
    parser = build_parser()
    args = parser.parse_args()

    try:
        rprint()
        rprint(Rule("What is uvinit?"))
        rprint()
        rprint(f"[bold]{DESCRIPTION}[/bold]")
        rprint()
        rprint(Markdown(markup=__doc__ or ""))
        rprint()

        rprint()
        rprint(Rule("Step 1 of 3: Copy the project template"))
        rprint()

        project_path = copy_template(args.template, args.destination, args.answers_file)
        if project_path is None:
            return ERR
        rprint("\n[bold green]✓ Project creation complete![/bold green]")

        # Ensure we show the correct path, considering it might have been provided via prompt
        rprint()
        rprint(f"Your project directory is now ready: [bold]{fmt_path(project_path)}[/bold]")

    except KeyboardInterrupt:
        print_cancelled()
        return 1
    except Exception as e:
        print_failed(e)
        raise e

    try:
        rprint()
        rprint(Rule("Step 2 of 3: Confirm your repository on GitHub.com"))
        rprint()

        rprint(f"Files are now copied to: [bold]{fmt_path(project_path)}[/bold]")
        rprint()
        rprint("Next, you will need to set up a git repository on GitHub.com.")
        rprint(
            "If you haven't already created the repository, you can do it now: https://github.com/new"
        )
        rprint()

        # Set up git repository and push to GitHub.
        repo_url = confirm_github_repo(project_path)
        if not repo_url:
            return ERR

        rprint()
        rprint(Rule("Step 3 of 3: Initialize your local git repository"))
        rprint()

        success = init_git_repo(project_path, repo_url)
        if not success:
            return ERR

    except KeyboardInterrupt:
        print_cancelled()
        return 1
    except Exception as e:
        print_failed(e)
        raise e
    finally:
        print_incomplete_git_setup()

    rprint()
    rprint("[bold green]✓ Project creation complete![/bold green]")
    rprint()
    rprint(f"Your template code is now ready: [bold]{fmt_path(project_path)}[/bold]")
    rprint()
    rprint(f"Your repository is at: [bold yellow]{repo_url}[/bold yellow]")
    rprint()
    rprint(
        "For more information, see `README.md`, `development.md` (for dev workflows), "
        "and `publishing.md` (for PyPI publishing instructions), all in your new repository."
    )
    rprint()
    rprint("Happy coding!")
    rprint()
    return 0


def build_parser() -> argparse.ArgumentParser:
    """
    Build the argument parser with rich formatting.
    """

    class CustomFormatter(ParagraphRichHelpFormatter):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, width=88, **kwargs)

    parser = argparse.ArgumentParser(
        description=DESCRIPTION
        + "\n\nJust run `uvx uvinit` without arguments to interactively create a new project.",
        epilog=__doc__,
        formatter_class=CustomFormatter,
    )

    parser.add_argument(
        "--template",
        default=DEFAULT_TEMPLATE,
        help=f"Copier template to use (defaults to {DEFAULT_TEMPLATE}, which is probably what you want)",
    )

    parser.add_argument(
        "--destination",
        nargs="?",
        help="Destination directory (optional, will prompt if not provided)",
    )

    parser.add_argument(
        "--answers-file", help="Path to a .copier-answers.yml file to use for default values"
    )

    parser.add_argument("--skip-git", action="store_true", help="Skip GitHub repository setup")

    parser.add_argument("--version", action="version", version=f"{APP_NAME} {get_app_version()}")

    return parser


if __name__ == "__main__":
    sys.exit(main())
