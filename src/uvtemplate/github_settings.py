import subprocess
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import yaml


@dataclass(frozen=True)
class GitHubDefaults:
    """User defaults from Git and GitHub config files."""

    author_name: str | None = None
    author_email: str | None = None
    github_username: str | None = None
    git_protocol: str | None = None


def get_git_config_value(key: str) -> str | None:
    """
    Get a value from git config.
    """
    try:
        result = subprocess.run(
            ["git", "config", "--get", key],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        return None
    except Exception:
        return None


@cache
def get_github_defaults() -> GitHubDefaults:
    """
    Get user defaults from Git and GitHub configs, if available.

    Reads name and email from their git config and username and protocol from
    ~/.config/gh/hosts.yml used by the gh CLI.
    """
    # Get git user info
    author_name = get_git_config_value("user.name")
    author_email = get_git_config_value("user.email")

    # Get GitHub info from gh config file
    github_username = None
    git_protocol = None
    gh_config_path = Path.home() / ".config" / "gh" / "hosts.yml"

    if gh_config_path.exists():
        try:
            with open(gh_config_path) as f:
                config = yaml.safe_load(f)
                if config and "github.com" in config:
                    gh_config = config["github.com"]
                    # Get the protocol
                    git_protocol = gh_config.get("git_protocol")
                    # Get the username - first try user field
                    github_username = gh_config.get("user")
                    # If not found, try first user in users dict
                    if not github_username and "users" in gh_config:
                        # Get first key in users dict
                        users = list(gh_config["users"].keys())
                        if users:
                            github_username = users[0]
        except Exception:
            pass  # Ignore errors reading the config

    return GitHubDefaults(
        author_name=author_name,
        author_email=author_email,
        github_username=github_username,
        git_protocol=git_protocol,
    )
