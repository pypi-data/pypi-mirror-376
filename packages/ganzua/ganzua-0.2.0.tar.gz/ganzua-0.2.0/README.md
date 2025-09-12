Ganzua
======

A tool for picking dependency information from Python lockfiles,
and manipulating the version constraints in `pyproject.toml` files.

For example, we can summarize the differences between two `uv.lock` files.
Ganzua is designed for scripting, so by default we get JSON output:

```console
$ ganzua diff tests/{old,new}-uv-project/uv.lock
{
  "stat": {
    "total": 2,
    "added": 1,
    "removed": 0,
    "updated": 1
  },
  "packages": {
    "annotated-types": {
      "old": null,
      "new": {
        "version": "0.7.0"
      }
    },
    "typing-extensions": {
      "old": {
        "version": "3.10.0.2"
      },
      "new": {
        "version": "4.14.1"
      }
    }
  }
}
```

We can also opt in to Markdown (GFM) output, which will produce a summary and a table:

```console
$ ganzua diff --format=markdown tests/{old,new}-uv-project/uv.lock
2 changed packages (1 added, 1 updated)
<BLANKLINE>
| package           | old      | new    |
|-------------------|----------|--------|
| annotated-types   | -        | 0.7.0  |
| typing-extensions | 3.10.0.2 | 4.14.1 |
```

Aside from inspecting or diffing lockfiles,
we can extract and manipulate constraints from `pyproject.toml` files:

```console
$ ganzua constraints inspect --format=markdown tests/new-uv-project/pyproject.toml
| package           | version |
|-------------------|---------|
| annotated-types   | >=0.7.0 |
| typing-extensions | >=4     |
```

## Installation

Ganzua is available on PyPI: <https://pypi.org/project/ganzua/>

Recommended: run or install via the [`uv` package manager](https://docs.astral.sh/uv/):

* `uv tool run ganzua` to try Ganzua without installation
* `uv tool install ganzua` to install Ganzua on your machine

Alternative: run or install via the [`pipx` tool](https://pipx.pypa.io/):

* `pipx run ganzua` to try Ganzua without installation
* `pipx install ganzua` to install Ganzua on your machine

Because Ganzua is an ordinary Python package, you can also install it into an existing virtual environment (venv).
You can use your usual Python dependency management tools like uv, Poetry, or pip for this.
However, it is recommended that you use `uv tool` or `pipx` to install Ganzua into its own venv, which prevents version conflicts.

To preview a bleeding-edge version without waiting for a PyPI release, you can install directly from the Ganzua repository on GitHub. For example:

* `uv tool run git+https://github.com/latk/ganzua.git`
* `pipx run --spec git+https://github.com/latk/ganzua.git ganzua`

## Usage

<!-- begin usage -->

Usage: `ganzua [OPTIONS] COMMAND [ARGS]...`

Inspect Python dependency lockfiles (uv and Poetry).

**Options:**

* `--help`
  Show this help message and exit.

**Commands:**

* [`help`](#ganzua-help)
  Show help for the application or a specific subcommand.
* [`inspect`](#ganzua-inspect)
  Inspect a lockfile.
* [`diff`](#ganzua-diff)
  Compare two lockfiles.
* [`constraints`](#ganzua-constraints)
  Work with `pyproject.toml` constraints.
* [`schema`](#ganzua-schema)
  Show the JSON schema for the output of the given command.

For more information, see the Ganzua website at "<https://github.com/latk/ganzua>".

Ganzua is licensed under the Apache-2.0 license.


### ganzua help<a id="ganzua-help"></a>

Usage: `ganzua help [OPTIONS] [SUBCOMMAND]...`

Show help for the application or a specific subcommand.

**Options:**

* `--all`
  Also show help for all subcommands.
* `--markdown`
  Output help in Markdown format.


### ganzua inspect<a id="ganzua-inspect"></a>

Usage: `ganzua inspect [OPTIONS] LOCKFILE`

Inspect a lockfile.

**Options:**

* `--format [json|markdown]`
  Choose the output format, e.g. Markdown. [default: json]
* `--help`
  Show this help message and exit.


### ganzua diff<a id="ganzua-diff"></a>

Usage: `ganzua diff [OPTIONS] OLD NEW`

Compare two lockfiles.

**Options:**

* `--format [json|markdown]`
  Choose the output format, e.g. Markdown. [default: json]
* `--help`
  Show this help message and exit.


### ganzua constraints<a id="ganzua-constraints"></a>

Usage: `ganzua constraints [OPTIONS] COMMAND [ARGS]...`

Work with `pyproject.toml` constraints.

**Options:**

* `--help`
  Show this help message and exit.

**Commands:**

* [`inspect`](#ganzua-constraints-inspect)
  List all constraints in the `pyproject.toml` file.
* [`bump`](#ganzua-constraints-bump)
  Update `pyproject.toml` dependency constraints to match the lockfile.
* [`reset`](#ganzua-constraints-reset)
  Remove or relax any dependency version constraints from the `pyproject.toml`.


### ganzua constraints inspect<a id="ganzua-constraints-inspect"></a>

Usage: `ganzua constraints inspect [OPTIONS] PYPROJECT`

List all constraints in the `pyproject.toml` file.

**Options:**

* `--format [json|markdown]`
  Choose the output format, e.g. Markdown. [default: json]
* `--help`
  Show this help message and exit.


### ganzua constraints bump<a id="ganzua-constraints-bump"></a>

Usage: `ganzua constraints bump [OPTIONS] PYPROJECT`

Update `pyproject.toml` dependency constraints to match the lockfile.

Of course, the lockfile should always be a valid solution for the constraints.
But often, the constraints are somewhat relaxed.
This tool will *increment* the constraints to match the currently locked versions.
Specifically, the locked version becomes a lower bound for the constraint.

This tool will try to be as granular as the original constraint.
For example, given the old constraint `foo>=3.5` and the new version `4.7.2`,
the constraint would be updated to `foo>=4.7`.

**Options:**

* `--lockfile FILE`
  Where to load versions from. Required.
* `--backup PATH`
  Store a backup in this file.
* `--help`
  Show this help message and exit.


### ganzua constraints reset<a id="ganzua-constraints-reset"></a>

Usage: `ganzua constraints reset [OPTIONS] PYPROJECT`

Remove or relax any dependency version constraints from the `pyproject.toml`.

This can be useful for allowing uv/Poetry to update to the most recent versions,
ignoring the previous constraints. Approximate recipe:

```bash
ganzua constraints reset --backup=pyproject.toml.bak pyproject.toml
uv lock --upgrade  # perform the upgrade
mv pyproject.toml.bak pyproject.toml  # restore old constraints
ganzua constraints bump --lockfile=uv.lock pyproject.toml
uv lock
```

**Options:**

* `--backup PATH`
  Store a backup in this file.
* `--to [none|minimum]`
  How to reset constraints.
  * `none` (default): remove all constraints
  * `minimum`: set constraints to the currently locked minimum, removing upper bounds
* `--lockfile FILE`
  Where to load current versions from (for `--to=minimum`).
* `--help`
  Show this help message and exit.


### ganzua schema<a id="ganzua-schema"></a>

Usage: `ganzua schema [OPTIONS] {inspect|diff|constraints-inspect}`

Show the JSON schema for the output of the given command.

**Options:**

* `--help`
  Show this help message and exit.

<!-- end usage -->

## Support

Ganzua is Open Source software, provided to you free of charge and on an "as is" basis.
You are not entitled to support, help, or bugfixes of any kind.

Nevertheless, the Ganzua project may occasionally offer help.

* If you have questions about using Ganzua, you may search existing posts at <https://github.com/latk/ganzua/discussions> and start a new discussion if necessary.
* If you have discovered a bug in Ganzua, please report it at <https://github.com/latk/ganzua/issues>.

Ganzua intends to maintain a backwards-compatible command line interface, and intends to use SemVer version numbers.

Only those parts of the CLI that are relevant for scripting are covered by this stability policy:

* commands that inspect or modify files
* machine-readable output, e.g. the schema of JSON output

For example, Ganzua might increment the "minor" version number if a new field is added to JSON output or if new command line options are added, and increment the "major" version if output fields are removed or new required command line arguments are added.

Out of scope are:

* interacting with the `ganzua` Python module
* Python versions or dependency versions used by Ganzua
* formatting of human-readable output (e.g. Markdown)
* formatting of error messages
* commands and flags that relate to help messages

##  What does Ganzua mean?

The Spanish term *ganzúa* means lockpick. It is pronounced *gan-THU-a*.

This `ganzua` tool for interacting with Python dependency lockfiles
is unrelated to the [2004 cryptoanalysis tool of the same name](https://ganzua.sourceforge.net/en/index.html).

## License

Copyright 2025 Lukas Atkinson

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
