import subprocess
from pathlib import Path
from typing import Any

import questionary
from rich.console import Console

console = Console(width=88)


def rprint(*args: Any, **kwargs: Any) -> None:
    console.print(*args, **kwargs)


def print_subtle(message: str) -> None:
    rprint(f"[bright_black]{message}[/bright_black]")


def print_success(message: str) -> None:
    rprint()
    rprint(f"[bold green]✓ {message}[/bold green]")


def print_status(message: str) -> None:
    rprint()
    rprint(f"[bold yellow]{message}[/bold yellow]")


def print_warning(message: str) -> None:
    rprint()
    rprint(f"[bold yellow]✗ {message}[/bold yellow] ")


def print_error(message: str) -> None:
    rprint()
    rprint(f"[bold red]‼️ Error:[/bold red] {message}")


def print_cancelled() -> None:
    print_warning("Operation cancelled.")


def print_failed(e: Exception) -> None:
    print_error(f"Failed to create project: {e}")


class Failed(RuntimeError):
    """
    Raised for fatal errors.
    """

    def __init__(self, message: str = "Operation failed"):
        super().__init__(message)


class Cancelled(RuntimeError):
    """
    Raised for cancelled operations.
    """


def confirm_action(message: str, default: bool = True, auto_confirm: bool = False) -> bool:
    """
    Ask for confirmation, or auto-confirm if in non-interactive mode.
    """
    if auto_confirm:
        rprint(f"[dim]Auto-confirming: {message}[/dim]")
        return True
    result = questionary.confirm(message, default=default).ask()
    if result is None:
        raise Cancelled()
    return result


def run_command_with_confirmation(
    command: str,
    description: str | None = None,
    cwd: Path | None = None,
    capture_output: bool = True,
    auto_confirm: bool = False,
) -> str:
    """
    Print a command, ask for confirmation, and run it if confirmed.
    """
    if description:
        rprint()
        rprint(f"Step: [bold]{description}[/bold]")
    rprint()
    rprint(f"Will run: [bold]❯[/bold] [bold blue]{command}[/bold blue]")
    rprint()

    if not confirm_action("Run this command?", default=True, auto_confirm=auto_confirm):
        raise Cancelled()

    try:
        rprint()
        rprint(
            f"[bold yellow]Running:[/bold yellow] [bold]❯[/bold] [bold blue]{command}[/bold blue]"
        )
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            text=True,
            capture_output=capture_output,
            cwd=cwd,
        )
        if result.stdout:
            rprint(result.stdout)
        rprint("[bold green]✓[/bold green] [green]Command executed successfully[/green]")
        return result.stdout
    except subprocess.CalledProcessError as e:
        rprint(f"[bold red]✗ Command failed with exit code {e.returncode}[/bold red]")
        if e.stdout:
            rprint(e.stdout)
        if e.stderr:
            rprint(f"[red]{e.stderr}[/red]")
        raise Failed() from e


def run_commands_sequence(
    commands: list[tuple[str, str]],
    cwd: Path,
    auto_confirm: bool = False,
    **format_args: Any,
) -> list[str]:
    """
    Run a sequence of commands with confirmation. Each command is formatted with
    the provided arguments.
    """
    rprint(f"Working from directory: [bold blue]{cwd.absolute()}[/bold blue]")
    rprint()
    results: list[str] = []
    for cmd_template, description in commands:
        cmd = cmd_template.format(**format_args)
        result = run_command_with_confirmation(cmd, description, cwd=cwd, auto_confirm=auto_confirm)
        results.append(result)

    return results
