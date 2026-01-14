from pathlib import Path

import questionary

from uvtemplate.shell_utils import (
    Cancelled,
    Failed,
    confirm_action,
    print_status,
    print_success,
    print_warning,
    rprint,
    run_command_with_confirmation,
    run_commands_sequence,
)

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


def github_repo_url(package_github_org: str, package_name: str, protocol: str = "ssh") -> str:
    """
    GitHub repository URL based on organization and package name.
    """
    if protocol == "ssh":
        return f"git@github.com:{package_github_org}/{package_name}.git"
    else:
        return f"https://github.com/{package_github_org}/{package_name}.git"


def gh_authenticate(auto_confirm: bool = False) -> None:
    """
    Authenticate with GitHub using `gh` if not already authenticated.
    """
    try:
        run_command_with_confirmation(
            "gh auth status",
            "Check if you are authenticated with GitHub",
            auto_confirm=auto_confirm,
        )
        success = True
    except Failed:
        success = False

    if not success:
        if auto_confirm:
            raise Failed("Not authenticated with GitHub. Run 'gh auth login' first.")
        rprint()
        print_status("You are not yet authenticated with GitHub.")
        rprint()
        rprint("Let's log in. Follow the prompts from GitHub to log in.")
        rprint()
        run_command_with_confirmation(
            "gh auth login",
            "Authenticate with GitHub",
            capture_output=False,  # Important since this gh command is interactive
            auto_confirm=auto_confirm,
        )

    print_success("Authenticated with GitHub.")


def create_or_confirm_github_repo(
    project_path: Path,
    package_name: str,
    package_github_org: str,
    auto_confirm: bool = False,
    use_gh_cli: bool = True,
    is_public: bool = False,
    git_protocol: str = "ssh",
) -> str:
    """
    Confirm or create a GitHub repository for the project.

    Args:
        project_path: Path to the project directory.
        package_name: Name of the package/repository.
        package_github_org: GitHub organization or username.
        auto_confirm: If True, skip all confirmations (non-interactive mode).
        use_gh_cli: If True, use gh CLI to create repo. If False, assume repo exists.
        is_public: If True, create public repo. Only used with use_gh_cli=True.
        git_protocol: "ssh" or "https" for repository URL. Only used with use_gh_cli=False.
    """

    rprint()
    rprint(
        "If you have the `gh` command installed (see cli.github.com), "
        "this tool can help you create the repository. Or you can "
        "create the repo yourself on GitHub.com."
    )
    rprint()

    # In auto mode, use the provided use_gh_cli value; otherwise ask
    if auto_confirm:
        should_use_gh = use_gh_cli
    else:
        should_use_gh = confirm_action(
            "Do you want to create the repository with `gh`?",
            default=True,
            auto_confirm=False,
        )

    if should_use_gh:
        gh_authenticate(auto_confirm=auto_confirm)
        rprint()

        # In auto mode, use the provided is_public value; otherwise ask
        if not auto_confirm:
            is_public = confirm_action(
                "Is the repository public (if unsure say no as you can always make it public later)?",
                default=False,
                auto_confirm=False,
            )

        public_flag_str = "--public" if is_public else "--private"
        result = run_command_with_confirmation(
            f"gh repo create {package_github_org}/{package_name} {public_flag_str}",
            "Create GitHub repository",
            cwd=project_path,
            auto_confirm=auto_confirm,
        )
        repo_url = result.strip()
        print_success("Created GitHub repository")
        rprint()
        rprint(f"Your GitHub repository URL: [bold blue]{repo_url}[/bold blue]")
        rprint()
    else:
        rprint()
        if not auto_confirm:
            rprint("Okay, then you'll need to create the repository manually.")
            # Ask for protocol preference
            proto_choices = [
                {
                    "name": f"ssh (git@github.com:{package_github_org}/{package_name}.git)",
                    "value": "ssh",
                },
                {
                    "name": f"https (https://github.com/{package_github_org}/{package_name}.git)",
                    "value": "https",
                },
            ]
            git_protocol = questionary.select(
                "Which type of GitHub repo URL do you want to use (if unsure, check "
                "which you use on another project and do that)?",
                choices=proto_choices,
                default=proto_choices[0],
            ).ask()

        repo_url = github_repo_url(package_github_org, package_name, git_protocol)

        rprint()
        rprint(f"This will be your GitHub repository URL: [bold blue]{repo_url}[/bold blue]")
        rprint()
        rprint(
            "If you haven't already created the repository, you can do it now. See: https://github.com/new"
        )
        rprint()

        if not confirm_action(
            "Confirm this is correct and you have created the repository?",
            default=True,
            auto_confirm=auto_confirm,
        ):
            raise Cancelled()

    return repo_url


def init_git_repo(project_path: Path, repo_url: str, auto_confirm: bool = False) -> None:
    """
    Initialize the git repository and push to GitHub.
    """
    # Run initialization commands
    run_commands_sequence(GIT_INIT_COMMANDS, project_path, auto_confirm=auto_confirm)

    # Run remote setup commands with the repo URL
    run_commands_sequence(
        GIT_REMOTE_COMMANDS, project_path, auto_confirm=auto_confirm, repo_url=repo_url
    )

    print_success("Git repository setup complete.")


def print_git_setup_help() -> None:
    for cmd in GIT_INIT_COMMANDS + GIT_REMOTE_COMMANDS:
        rprint(f"[dim]# {cmd[1]}[/dim]")
        rprint(f"{cmd[0]}")


def print_incomplete_git_setup() -> None:
    print_warning("Git repository setup not completed.")
    rprint()
    rprint("If you want to continue, you can rerun `uvtemplate`.")
    rprint(
        "Or if you want to set up the repository manually, you can "
        "pick up where you left off by running any commands that failed:"
    )
    rprint()
    print_git_setup_help()
    rprint()
