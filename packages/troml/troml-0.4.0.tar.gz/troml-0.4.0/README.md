# troml 🥁

`troml` provides a list of potential classifiers that could be added to a Python package.

It supports modern Python packages that use the [`pyproject.toml`](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) standard (aka [PEP 621](https://peps.python.org/pep-0621/) and [PEP 639](https://peps.python.org/pep-0639/)). `troml` also follows [PEP 561](https://peps.python.org/pep-0561/) to determine whether a package should be considered typed or not.

![Screenshot of troml in action](https://github.com/adamghill/troml/blob/main/troml.png?raw=true)

## Usage

### `uvx`

`uv` is an extremely fast Python package and project manager, written in Rust. Self-contained library using `uv`. `uvx` is an alias for [`uv tool run ...`](https://docs.astral.sh/uv/concepts/tools/).

1. Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/)
2. Go to a directory with source code for a Python package
3. `uvx troml`

### `pipx`

`pipx` is a way to run install and run Python applications in isolated environments.

1. Install [`pipx`](https://pipx.pypa.io/latest/installation/)
2. `pipx install troml`
3. Go to a directory with source code for a Python package
4. `troml`

### `pip --user`

Install `troml` to the Python user install directory. More details [in the docs](https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-user).

1. `pip install --user troml`
2. Go to a directory with source code for a Python package
3. `troml`

## CLI arguments

### path

`troml` optionally accepts a path as the first argument. Defaults to `.` for the current directory.

`uvx troml /path/to/pypyproject.toml`

### suggest

Provides an output of suggested classifiers. The default if no other command is used.

`uvx troml suggest /path/to/pypyproject.toml`

#### fix

Automatically add classifiers in the `pyproject.toml` based on the suggestions. Will not remove existing classifiers.

`uvx troml suggest --fix /path/to/pypyproject.toml`

#### no-multiline

Output the classifiers in a single-line. No-op if used without `--fix`.

`uvx troml suggest --fix --multiline /path/to/pypyproject.toml`

### check

Exits with an error code if there are any suggested classifiers. Useful for `pre-commit`, CI/CD, etc.

`uvx troml check /path/to/pypyproject.toml`

## Supported classifiers

### Python version

`troml` will read `project.python-requires` and suggest classifiers based on it.

### Legacy license

`troml` will suggest removing the legacy license classifiers.

### Dependencies

`troml` will suggest classifiers based on the dependencies in `project.dependencies`, `project.dependency-groups`, and `tool.uv.constraint-dependencies`.

### Typing

`troml` will suggest the "Typing :: Typed" classifier based on the existence of the `py.typed` file in the same directory as the `pyproject.toml` file.

## FAQ

### Does this add classifiers interactively?

Nope and it's not something I would add in. Take a look at https://codeberg.org/kfdm/add-classifiers or https://github.com/jvllmr/trove-setup if that's what you are looking for.

## What's with the name?

- The classifiers for Python are called ["Trove classifiers"](https://pypi.org/classifiers/)
- Modern Python packages use TOML for configuration

"trove" 🤝 "TOML"

In a happy coincidence, "trommel" in Dutch means "drum".

## Development

1. Install `just`: https://just.systems/man/en/packages.html
2. `just fetch`

### Run from source

`uv run troml [PATH-TO-PYPROJECT-TOML]`

### Commands

- unit tests (via `pytest`): `just test`
- linting (via `ruff`): `just lint`
- type checking (via `mypy`): `just type`
- unit test coverage (via `coverage.py`): `just coverage`
- run 'em all: `just dev`

## Inspiration

- https://indieweb.social/@adamghill/115174743670090084
- another approach from @kfdm: https://codeberg.org/kfdm/add-classifiers
- post about `add-classifers`: https://paultraylor.net/blog/2025/add-classifiers/
- https://github.com/jvllmr/trove-setup
- https://pypi.org/project/typer/ for creating the CLI
