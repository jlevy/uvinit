<div align="center">

<!-- <img alt="Using uvtemplate" src="https://github.com/user-attachments/assets/4325c251-26b7-4c4c-b46f-00759e53f7ae" /> -->
<img alt="Using uvtemplate" src="https://github.com/user-attachments/assets/8d048d1c-4fef-4c0c-aa9b-e05885ff4fbf" />

</div>

# uvtemplate

[![Documentation](https://img.shields.io/badge/documentation-go)](https://www.github.com/jlevy/simple-modern-uv)
[![CI status](https://github.com/jlevy/uvtemplate/actions/workflows/ci.yml/badge.svg)](https://github.com/jlevy/uvtemplate/actions/workflows/ci.yml?query=branch%3Amain)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/uvtemplate.svg?v=1)](https://pypi.python.org/pypi/uvtemplate)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Copier](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/copier-org/copier/master/img/badge/badge-grayscale-border.json)](https://github.com/copier-org/copier)
[![X (formerly Twitter) Follow](https://img.shields.io/twitter/follow/ojoshe)](https://x.com/ojoshe)

A time-saving CLI tool to quickly start new Python projects with
[**uv**](https://github.com/astral-sh/uv) using the
[**simple-modern-uv**](https://github.com/jlevy/simple-modern-uv) template.

## Quick Start

### For Humans (Interactive Mode)

```bash
uvx uvtemplate create
```

This will guide you through creating a new project step by step.

### For AI Agents (Non-Interactive Mode)

AI coding agents like Claude Code can create projects programmatically:

```bash
uvx uvtemplate --yes --destination my-project \
  --data package_name=my-project \
  --data package_description="My awesome project" \
  --data package_author_name="Your Name" \
  --skip-git
```

## Do I Need uv?

Yes. You will need to [**have uv installed**](https://github.com/astral-sh/uv).
Read that page or my [template docs](https://github.com/jlevy/simple-modern-uv) for
background on why uv is such an improved package manager for Python.

## What is uvtemplate?

It’s the tool I wish I’d had when setting up projects with uv.

**`uvx uvtemplate create`** will clone a new project template and help you set up your
GitHub repo. The template is tiny and sets up **uv**, **ruff** linting and formatting,
**GitHub Actions**, **publishing to PyPI**, **type checking**, and more.

## Usage

### Commands

| Command | Description |
| --- | --- |
| `uvtemplate` | Show help and available options |
| `uvtemplate create` | Start interactive project creation |
| `uvtemplate migrate` | Analyze an existing project and show migration recommendations |
| `uvtemplate update` | Update a template-based project to the latest template version |
| `uvtemplate readme` | Print this documentation |

### Options

| Option | Description |
| --- | --- |
| `--destination DIR` | Destination directory for the project |
| `--data KEY=VALUE` | Set a template value (can be repeated) |
| `--yes` | Auto-confirm all prompts (non-interactive mode) |
| `--skip-git` | Skip GitHub repository and git setup |
| `--template URL` | Use a custom copier template |
| `--answers-file FILE` | Load defaults from a .copier-answers.yml file |
| `--no-gh-cli` | Don't use gh CLI to create repo |
| `--public` | Create a public repository (default: private) |
| `--git-protocol ssh | https` |

### Template Values

Use `--data KEY=VALUE` to set these values:

| Key | Description | Example |
| --- | --- | --- |
| `package_name` | Package name (kebab-case) | `my-project` |
| `package_module` | Python module name (snake_case) | `my_project` |
| `package_description` | Short description | `"A useful tool"` |
| `package_author_name` | Author's name | `"Jane Doe"` |
| `package_author_email` | Author's email | `"jane@example.com"` |
| `package_github_org` | GitHub username or org | `"janedev"` |

## Examples

### Interactive (Human) Usage

Start the interactive wizard:

```bash
uvx uvtemplate create
```

Skip git setup (just create the project files):

```bash
uvx uvtemplate create --skip-git
```

### Non-Interactive (Agent) Usage

Create a complete project without any prompts:

```bash
uvx uvtemplate --yes --destination my-cli-tool \
  --data package_name=my-cli-tool \
  --data package_module=my_cli_tool \
  --data package_description="A command-line tool for doing things" \
  --data package_author_name="Claude" \
  --data package_author_email="ai@example.com" \
  --data package_github_org="myorg" \
  --skip-git
```

Create a project and set up a private GitHub repo:

```bash
uvx uvtemplate --yes --destination my-project \
  --data package_name=my-project \
  --data package_description="My project" \
  --data package_github_org="myorg"
```

Create a project with a public GitHub repo:

```bash
uvx uvtemplate --yes --destination my-project \
  --data package_name=my-project \
  --public
```

### Using an Answers File

If you have a `.copier-answers.yml` from a previous project:

```bash
uvx uvtemplate --yes --destination new-project \
  --answers-file /path/to/existing/.copier-answers.yml
```

## For AI Coding Agents

This tool is designed to work well with AI coding agents like Claude Code, Cursor,
GitHub Copilot, etc.

### Key Points for Agents

1. **Use `--yes` flag**: This auto-confirms all prompts, making the tool fully
   non-interactive.

2. **Provide all values via `--data`**: Set template values upfront to avoid interactive
   prompts.

3. **Use `--skip-git`** if you want to handle git setup separately or don’t need it.

4. **The tool uses exit codes**: `0` for success, `1` for failure/cancellation.

5. **Values are derived intelligently**: If you provide `--destination my-project`, the
   tool will automatically derive `package_name=my-project` and
   `package_module=my_project` unless you override them.

### Minimal Agent Example

The simplest non-interactive usage:

```bash
uvx uvtemplate --yes --destination my-project --skip-git
```

This creates a project with sensible defaults derived from the destination name and your
git/GitHub config.

### Complete Agent Example

For full control:

```bash
uvx uvtemplate --yes --destination my-project \
  --data package_name=my-project \
  --data package_module=my_project \
  --data package_description="Project description here" \
  --data package_author_name="Author Name" \
  --data package_author_email="author@example.com" \
  --data package_github_org="github-org" \
  --skip-git
```

## What Python Project Template Does it Use?

The [**simple-modern-uv**](https://github.com/jlevy/simple-modern-uv) template.
See that repo for full docs and
[this thread](https://x.com/ojoshe/status/1901380005084700793) for a bit more context.

The template includes:

- **uv** for project setup and dependencies

- **ruff** for modern linting and formatting

- **GitHub Actions** for CI and publishing workflows

- **Dynamic versioning** from git tags

- **PyPI publishing** workflows

- **BasedPyright** for type checking

- **Pytest** for tests

- **Codespell** for spell checking

If you prefer, you can use that template directly; uvtemplate is just a CLI wrapper.

If you have another copier-format template you want to use, specify it with
`--template`.

## Migrating an Existing Project

Use the `migrate` command to analyze an existing project and get migration
recommendations:

```bash
cd my-existing-project
uvx uvtemplate migrate
```

This will detect your current build system (Poetry, setuptools, Pipenv, etc.)
and provide a step-by-step guide for migrating to uv.
It analyzes your project and outputs recommendations—it does not automatically modify
any files.

The migrate command works well with AI agents, providing structured recommendations that
an agent can follow to perform the migration.

### Alternative: Manual Migration

You can also create a fresh template as a reference and manually copy what you need:

```bash
uvtemplate create --skip-git --destination .uvtemplate-ref
```

Then copy the relevant files (pyproject.toml structure, Makefile, workflows, etc.)
into your existing project.

## Updating a Project

Projects created with uvtemplate can be updated to the latest template version:

```bash
cd my-project
uvx uvtemplate update
```

This uses [copier](https://github.com/copier-org/copier) under the hood to apply
template updates while preserving your customizations.
The command will show you what changed and let you resolve any conflicts.

For non-interactive updates (useful for AI agents):

```bash
uvx uvtemplate update --yes
```

Note: The `update` command only works on projects that were created with uvtemplate (or
copier directly). If you migrated a project manually, use `uvtemplate migrate` to see
recommendations.

* * *

*This project was (of course) built using
[simple-modern-uv](https://github.com/jlevy/simple-modern-uv).*
