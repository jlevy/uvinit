"""
uvtemplate: Create a new Python project with uv.

Run 'uvtemplate readme' for full documentation.
"""

import argparse
import sys
from importlib.resources import files
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.rule import Rule
from rich_argparse.contrib import ParagraphRichHelpFormatter

from uvtemplate.copier_workflow import DEFAULT_TEMPLATE
from uvtemplate.main_workflow import main_workflow
from uvtemplate.shell_utils import rprint

APP_NAME = "uvtemplate"

DESCRIPTION = f"{APP_NAME}: Create a new Python project with uv using the simple-modern-uv template"


def get_app_version() -> str:
    try:
        from importlib.metadata import version

        return "v" + version(APP_NAME)
    except Exception:
        return "unknown"


def _strip_html_from_markdown(content: str) -> str:
    """
    Strip HTML tags from markdown content for cleaner CLI display.
    This removes HTML image tags, divs, and badge links that don't render well in terminal.
    """
    import re

    # Remove HTML comments
    content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)

    # Remove <div> tags and their contents if they only contain images/badges
    content = re.sub(r"<div[^>]*>.*?</div>", "", content, flags=re.DOTALL | re.IGNORECASE)

    # Remove standalone HTML tags like <img>
    content = re.sub(r"<img[^>]*>", "", content, flags=re.IGNORECASE)

    # Remove badge image links like [![alt](url)](link)
    content = re.sub(r"\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)", "", content)

    # Clean up multiple blank lines
    content = re.sub(r"\n{3,}", "\n\n", content)

    # Remove leading whitespace lines
    content = content.lstrip()

    return content


def get_readme_content() -> str:
    """
    Get README content from package resources or source tree.
    HTML content is stripped for cleaner CLI display.
    """
    from pathlib import Path

    content = None

    # Try 1: Load from package resources (README.md is included via hatch force-include)
    try:
        readme_file = files("uvtemplate").joinpath("README.md")
        content = readme_file.read_text()
    except Exception:
        pass

    # Try 2: Load from source tree (for development mode)
    if not content:
        try:
            # Go up from src/uvtemplate/uvtemplate.py to project root
            project_root = Path(__file__).parent.parent.parent
            readme_path = project_root / "README.md"
            if readme_path.exists():
                content = readme_path.read_text()
        except Exception:
            pass

    # If we got content, strip HTML for cleaner CLI display
    if content:
        return _strip_html_from_markdown(content)

    # Fallback: minimal help text
    return """# uvtemplate

A time-saving CLI to start a new Python project with uv.

## Quick Start

### Interactive (for humans)
    uvx uvtemplate create

### Non-Interactive (for AI agents)
    uvx uvtemplate --yes --destination my-project --skip-git

Run 'uvtemplate --help' for all options.

More info: https://github.com/jlevy/uvtemplate
"""


def parse_data_args(data_args: list[str] | None) -> dict[str, Any]:
    """
    Parse --data KEY=VALUE arguments into a dictionary.
    """
    if not data_args:
        return {}

    result: dict[str, Any] = {}
    for item in data_args:
        if "=" not in item:
            print(f"Warning: Invalid --data format '{item}'. Expected KEY=VALUE.", file=sys.stderr)
            continue
        key, value = item.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def cmd_readme() -> int:
    """Print the README content with Rich formatting and auto-detection."""
    content = get_readme_content()

    # Create console with auto-detection: will use colors if terminal, plain text if piped
    # force_terminal=None means auto-detect
    console = Console(force_terminal=None, width=100)
    console.print(Markdown(content))
    return 0


def cmd_create(args: argparse.Namespace) -> int:
    """Run the main project creation workflow."""
    # Parse --data arguments
    data = parse_data_args(args.data)

    # Show intro unless in non-interactive mode
    if not args.yes:
        readme_content = get_readme_content()
        rprint()
        rprint(Rule("What is uvtemplate?"))
        rprint()
        rprint(f"[bold]{DESCRIPTION}[/bold]")
        rprint()
        rprint(Markdown(markup=readme_content))
        rprint()

    return main_workflow(
        template=args.template,
        destination=args.destination,
        answers_file=args.answers_file,
        auto_confirm=args.yes,
        data=data if data else None,
        skip_git=args.skip_git,
        use_gh_cli=not args.no_gh_cli,
        is_public=args.public,
        git_protocol=args.git_protocol,
    )


def main() -> int:
    """
    Main entry point for the CLI.
    """
    parser = build_parser()

    # If no arguments, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return 0

    args = parser.parse_args()

    # Handle subcommands
    if hasattr(args, "func"):
        return args.func(args)

    # Default: run create workflow
    return cmd_create(args)


def build_parser() -> argparse.ArgumentParser:
    """
    Build the argument parser with rich formatting.
    """

    class CustomFormatter(ParagraphRichHelpFormatter):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, width=88, **kwargs)

    parser = argparse.ArgumentParser(
        description=DESCRIPTION,
        epilog="Run 'uvtemplate readme' for full documentation, or 'uvtemplate create' to start interactively.",
        formatter_class=CustomFormatter,
    )

    # Subcommands
    subparsers = parser.add_subparsers(title="commands", dest="command")

    # create subcommand (explicit way to start interactive workflow)
    create_parser = subparsers.add_parser(
        "create",
        help="Create a new project (interactive mode)",
        formatter_class=CustomFormatter,
    )
    create_parser.set_defaults(func=cmd_create)
    # Add all the same options to the create subcommand
    _add_create_options(create_parser)

    # readme subcommand
    readme_parser = subparsers.add_parser(
        "readme",
        help="Print the full README documentation",
        formatter_class=CustomFormatter,
    )
    readme_parser.set_defaults(func=lambda _args: cmd_readme())  # pyright: ignore[reportUnknownLambdaType]

    # Main options (for default create workflow when using flags directly)
    _add_create_options(parser)

    parser.add_argument(
        "--version",
        action="version",
        version=f"{APP_NAME} {get_app_version()}",
    )

    return parser


def _add_create_options(parser: argparse.ArgumentParser) -> None:
    """Add options for the create workflow to a parser."""
    parser.add_argument(
        "--template",
        default=DEFAULT_TEMPLATE,
        help=f"Copier template to use (default: {DEFAULT_TEMPLATE})",
    )

    parser.add_argument(
        "--destination",
        nargs="?",
        help="Destination directory (will prompt if not provided)",
    )

    parser.add_argument(
        "--answers-file",
        help="Path to a .copier-answers.yml file to use for default values",
    )

    parser.add_argument(
        "--data",
        action="append",
        metavar="KEY=VALUE",
        help="Set a template value (can be repeated). Example: --data package_name=my-project",
    )

    parser.add_argument(
        "--yes",
        action="store_true",
        help="Auto-confirm all prompts (non-interactive mode for automation/agents)",
    )

    parser.add_argument(
        "--skip-git",
        action="store_true",
        help="Skip GitHub repository setup and git initialization",
    )

    parser.add_argument(
        "--no-gh-cli",
        action="store_true",
        help="Don't use gh CLI to create repo (assume repo already exists)",
    )

    parser.add_argument(
        "--public",
        action="store_true",
        help="Create a public repository (default is private)",
    )

    parser.add_argument(
        "--git-protocol",
        choices=["ssh", "https"],
        default="ssh",
        help="Git protocol to use for repository URL (default: ssh)",
    )


if __name__ == "__main__":
    sys.exit(main())
