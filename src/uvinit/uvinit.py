"""
Welcome to uvinit!

This tool is intended to be the easiest way to start a new, fully configured
Python project using [uv](https://docs.astral.sh/uv/), the modern Python
package manager.

It sets up a Python project using [copier](https://github.com/copier-org/copier),
a templating tool, to make the whole process quick: you just run
`uvx uvinit` and then follow the prompts.

uv has greatly improved Python project setup. But it can still be confusing
to find out the best practices to set up a project in a simple and clean
way, with dependency management, developer workflows, GitHub Actions for CI,
and publishing to PyPI as a pip. I built (and now personally use) this tool
as I was switching to uv, to make the process of setting up a new project as
low-friction as possible.

The project template used is
[simple-modern-uv](https://github.com/jlevy/simple-modern-uv),
which aims to be minimal and modern:

- uv for project setup and dependencies.

- ruff for modern linting and formatting.

- GitHub Actions for CI and publishing workflows.

- Dynamic versioning so release and package publication is as simple as creating
  a tag/release on GitHub.

- Workflows for packaging and publishing to PyPI with uv.

- Type checking with BasedPyright.

- Pytest for tests.

- Codespell for drop-in spell checking.

Unlike some more complex project templates, this aims only to include the
essentials for a production-ready Python project. Once it is created, you can
easily add to or adapt it to your needs.

The setup is in three phases:

1. Copy the project template, instantiating your project name, module name, etc.

2. Set up a GitHub repository and push your project to it.

3. Initialize your local git repo and push to GitHub.

This tool will ask you to confirm at each step, so there is no harm in getting
started then hitting ctrl-c to abort then rerun again.

More information: git.new/uvinit
Contact me with feedback: x.com/ojoshe (DMs), github.com/jlevy (email)
"""

import argparse
import sys
from typing import Any

from rich.markdown import Markdown
from rich.rule import Rule
from rich_argparse.contrib import ParagraphRichHelpFormatter

from uvinit.copier_workflow import DEFAULT_TEMPLATE
from uvinit.main_workflow import main_workflow
from uvinit.shell_utils import (
    rprint,
)

APP_NAME = "uvinit"

DESCRIPTION = f"{APP_NAME}: Create a new Python project with uv using the simple-modern-uv template"


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

    rprint()
    rprint(Rule("What is uvinit?"))
    rprint()
    rprint(f"[bold]{DESCRIPTION}[/bold]")
    rprint()
    rprint(Markdown(markup=__doc__ or ""))
    rprint()

    return main_workflow(args.template, args.destination, args.answers_file)


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
