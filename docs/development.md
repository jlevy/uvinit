# Development

## Setting Up uv

This project is set up to use [uv](https://docs.astral.sh/uv/) to manage Python and
dependencies. First, be sure you
[have uv installed](https://docs.astral.sh/uv/getting-started/installation/).

Then
[fork the jlevy/uvtemplate repo](https://github.com/jlevy/uvtemplate/fork)
(having your own fork will make it easier to contribute) and
[clone it](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository).

## Basic Developer Workflows

The `Makefile` simply offers shortcuts to `uv` commands for developer convenience.
(For clarity, GitHub Actions don’t use the Makefile and just call `uv` directly.)

```shell
# First, install all dependencies and set up your virtual environment.
# This simply runs `uv sync --all-extras` to install all packages,
# including dev dependencies and optional dependencies.
make install

# Run uv sync, lint, tests, and dependency audit:
make

# Build wheel:
make build

# Linting (auto-fixes formatting and lint issues):
make lint

# Linting in check-only mode, matching CI (fails on issues, does not modify files):
make lint-check

# Run tests:
make test

# Audit dependencies for known vulnerabilities:
make audit

# Verify the checked-in lockfile installs without re-resolving:
make sync-frozen

# Delete all the build artifacts:
make clean

# Upgrade dependencies to compatible versions with the 14-day cool-off window:
make upgrade

# To run tests by hand:
uv run pytest   # all tests
uv run pytest -s src/module/some_file.py  # one test, showing outputs

# Build and install current dev executables, to let you use your dev copies
# as local tools:
uv tool install --editable .

# Dependency management directly with uv:
# Add a new dependency:
uv add package_name
# Add a development dependency:
uv add --dev package_name
# Update to latest compatible versions (including dependencies on git repos).
# Use a cutoff date at least 14 days in the past.
uv lock --upgrade --exclude-newer YYYY-MM-DD
uv sync
# Update a specific package:
uv lock --upgrade-package package_name
# Update a package deliberately after vetting the target release:
uv add package_name==X.Y.Z

# Run a shell within the Python environment:
uv venv
source .venv/bin/activate
```

See [uv docs](https://docs.astral.sh/uv/) for details.

## IDE setup

If you use VSCode or a fork like Cursor or Windsurf, you can install the following
extensions:

- [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)

- [Based Pyright](https://marketplace.visualstudio.com/items?itemName=detachhead.basedpyright)
  for type checking. Note that this extension works with non-Microsoft VSCode forks like
  Cursor.

## Supply Chain Hardening

Dependencies are an attack surface. Before adding or upgrading any dependency, follow
[**supply-chain-hardening**](https://github.com/jlevy/supply-chain-hardening), a concise
cross-ecosystem guide on installing dependencies safely. Its key defaults:

- **Cool-off period:** Don't install or upgrade to a release less than 14 days old
  (absent a documented exception)—most malicious publishes are caught within days. For
  uv, set `UV_EXCLUDE_NEWER` to a cutoff date a couple weeks back (uv takes a date, not a
  duration); this project's CI workflows set it automatically.

- **Vet before adding:** Confirm the package is actually needed and its name is spelled
  correctly (typosquats are common), and prefer a little first-party code over a new
  dependency.

- **Pin, lock, and audit:** Commit your `uv.lock`, pin GitHub Actions to a commit SHA,
  install from the lockfile with `uv sync --frozen` in CI, and run `make audit` after
  dependency changes.

## Publishing Releases

See [publishing.md](publishing.md) for instructions on publishing to PyPI.

## Documentation

- [uv docs](https://docs.astral.sh/uv/)

- [basedpyright docs](https://docs.basedpyright.com/latest/)

* * *

*This file was built with
[simple-modern-uv](https://github.com/jlevy/simple-modern-uv).*
