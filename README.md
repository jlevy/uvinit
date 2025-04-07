<div align="center">

<!-- <img alt="Using uvinit"
src="https://github.com/user-attachments/assets/4325c251-26b7-4c4c-b46f-00759e53f7ae" /> -->
<img alt="Using uvinit" src="https://github.com/user-attachments/assets/8d048d1c-4fef-4c0c-aa9b-e05885ff4fbf" />


</div>

# uvinit

[![Documentation](https://img.shields.io/badge/documentation-go)](https://www.github.com/jlevy/simple-modern-uv)
[![CI status](https://github.com/jlevy/uvinit/actions/workflows/ci.yml/badge.svg)](https://github.com/jlevy/uvinit/actions/workflows/ci.yml?query=branch%3Amain)
[![image](https://img.shields.io/pypi/pyversions/uvinit.svg)](https://pypi.python.org/pypi/uvinit)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Copier](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/copier-org/copier/master/img/badge/badge-grayscale-border.json)](https://github.com/copier-org/copier)
[![X (formerly Twitter)
Follow](https://img.shields.io/twitter/follow/ojoshe)](https://x.com/ojoshe)

## Usage

Two words:

```
uvx uvinit
```

It will guide you!

## Do I Need uv?

Yes. You will need to [**have uv installed**](https://github.com/astral-sh/uv).
Read that page or my [template docs](https://github.com/jlevy/simple-modern-uv) for
background on why uv is such an improved package manager for Python.

## What is uvinit?

A time-saving CLI tool to quickly start new Python projects with
[**uv**](https://github.com/astral-sh/uv) using the
[**simple-modern-uv**](https://github.com/jlevy/simple-modern-uv) template and
[**copier**](https://github.com/copier-org/copier).

It's the tool I wish I'd had when setting up projects with uv.

**`uvx uvinit`** will clone a new project template and help you set up your GitHub repo.
The template tiny and sets up **uv**, **ruff** linting and formatting, **GitHub
Actions**, **publishing to PyPI**, **type checking**, and more.

## What Python Project Template Does it Use?

The [**simple-modern-uv**](https://github.com/jlevy/simple-modern-uv) template.
See that repo for full docs and
[this thread](https://x.com/ojoshe/status/1901380005084700793) for a bit more context.

If you prefer, you can use that template directly; uvinit is just a CLI wrapper for the
template.

If you have another copier-format template you want to use, however, you can specify it
with the `--template` argument.

## Can I Use it With an Existing Project?

Yes. Just cancel after the template is copied (skip the part that pushes to git) and
you'll have a new working tree with all the uv and tooling set up.
Then manually copy over all the parts you want into your existing project.

## By Chance Is There a Short URL I Can Remember for This Handy Tool?

Funny you should ask!

Type [**git.new/uvinit**](https://git.new/uvinit) into your browser.

Tell your friends!

* * *

*This project was (of course) built using
[simple-modern-uv](https://github.com/jlevy/simple-modern-uv).*
