import questionary
from prettyfmt import fmt_path
from rich.rule import Rule

from uvinit.copier_workflow import copy_template, read_copier_answers
from uvinit.github_workflow import (
    create_or_confirm_github_repo,
    init_git_repo,
    print_incomplete_git_setup,
)
from uvinit.shell_utils import (
    Cancelled,
    Failed,
    print_cancelled,
    print_failed,
    print_success,
    print_warning,
    rprint,
)

ERR = 1


def main_workflow(template: str, destination: str, answers_file: str) -> int:
    try:
        rprint()
        rprint(Rule("Step 1 of 3: Copy the project template"))
        rprint()

        project_path = copy_template(template, destination, answers_file)
        rprint()
        rprint(f"Your project directory is: [bold blue]{fmt_path(project_path)}[/bold blue]")
        rprint()
    except (Cancelled, Failed, KeyboardInterrupt):
        print_cancelled()
        return ERR
    except Exception as e:
        print_failed(e)
        raise e

    try:
        rprint()
        rprint(Rule("Step 2 of 3: Set up your repository on GitHub.com"))
        rprint()

        rprint(f"Files are now copied to: [bold blue]{fmt_path(project_path)}[/bold blue]")
        rprint()
        rprint("Next, you will need to set up a git repository on GitHub.com.")
        rprint(
            "If you haven't already created the repository, you can do it now: https://github.com/new"
        )
        rprint()
        rprint(
            "If you already have an existing project that's not on uv, "
            "you can cancel now and copy the files from this project into your "
            "existing project."
        )
        rprint()

        # Re-read project metadata from copier answers.
        answers = read_copier_answers(project_path)
        package_name = answers.get("package_name")
        package_github_org = answers.get("package_github_org")

        if not package_name or not package_github_org:
            print_warning("Missing package name or organization.")
            raise Cancelled()

        confirm = questionary.confirm(
            "Ready to continue?",
            default=True,
        ).ask()

        if not confirm:
            raise Cancelled()

        repo_url = create_or_confirm_github_repo(project_path, package_name, package_github_org)

        rprint()
        rprint(Rule("Step 3 of 3: Initialize your local git repo"))
        rprint()

        init_git_repo(project_path, repo_url)

    except (Cancelled, Failed, KeyboardInterrupt):
        print_cancelled()
        return ERR
    except Exception as e:
        print_failed(e)
        raise e
    finally:
        print_incomplete_git_setup()

    rprint()
    print_success("Project creation complete!")
    rprint()
    rprint(f"Your template code is now ready: [bold blue]{fmt_path(project_path)}[/bold blue]")
    rprint()
    rprint(f"Your repository is at: [bold blue]{repo_url}[/bold blue]")
    rprint()
    rprint(
        "For more information, see `README.md`, `development.md` (for dev workflows), "
        "and `publishing.md` (for PyPI publishing instructions), all in your new repository."
    )
    rprint()
    rprint("Happy coding!")
    rprint()
    return 0
