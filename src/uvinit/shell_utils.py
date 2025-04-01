import subprocess
from pathlib import Path
from typing import Any

import questionary
from rich.console import Console

console = Console(width=88)


def rprint(*args: Any, **kwargs: Any) -> None:
    console.print(*args, **kwargs)


def print_warning(message: str) -> None:
    rprint(f"\n[bold yellow]✗ {message}[/bold yellow] ")


def print_error(message: str) -> None:
    rprint(f"\n[bold red]‼️ Error:[/bold red] {message}")


def print_cancelled() -> None:
    print_warning("Operation cancelled.")


def print_failed(e: Exception) -> None:
    print_error(f"Failed to create project: {e}")


def run_command_with_confirmation(command: str, cwd: Path | None = None) -> bool:
    """
    Print a command, ask for confirmation, and run it if confirmed.
    """
    rprint(f"\n[bold]Command: ❯[/bold] [bold blue]{command}[/bold blue]")
    rprint()

    if not questionary.confirm("Run this command?", default=True).ask():
        print_cancelled()
        return False

    try:
        rprint(f"[bold]Running: ❯[/bold] [bold blue]{command}[/bold blue]")
        result = subprocess.run(
            command, shell=True, check=True, text=True, capture_output=True, cwd=cwd
        )
        if result.stdout:
            rprint(result.stdout)
        rprint("[bold green]✓[/bold green] [green]Command executed successfully[/green]")
        return True
    except subprocess.CalledProcessError as e:
        rprint(f"[bold red]✗ Command failed with exit code {e.returncode}[/bold red]")
        if e.stdout:
            rprint(e.stdout)
        if e.stderr:
            rprint(f"[red]{e.stderr}[/red]")
        return False


def run_commands_sequence(commands: list[tuple[str, str]], cwd: Path, **format_args: Any) -> bool:
    """
    Run a sequence of commands with confirmation. Each command is formatted with
    the provided arguments.
    """
    rprint(f"Working from directory: [bold blue]{cwd.absolute()}[/bold blue]")
    rprint()
    for cmd_template, description in commands:
        cmd = cmd_template.format(**format_args)
        if description:
            rprint(f"\n[bold]Step:[/bold] {description}")
        if not run_command_with_confirmation(cmd, cwd=cwd):
            return False

    return True
