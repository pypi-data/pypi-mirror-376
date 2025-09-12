"""The ganzua command-line interface."""

import contextlib
import enum
import functools
import pathlib
import shutil
import typing as t
from dataclasses import dataclass

import click
import pydantic
import rich
import tomlkit

import ganzua

from ._cli_help import App
from ._constraints import Requirements
from ._diff import Diff
from ._lockfile import Lockfile
from ._markdown import md_from_diff, md_from_lockfile, md_from_requirements
from ._utils import error_context

app = App(
    name="ganzua",
    help="""\
Inspect Python dependency lockfiles (uv and Poetry).

<!-- options -->

For more information, see the Ganzua website at "<https://github.com/latk/ganzua>".

Ganzua is licensed under the Apache-2.0 license.
""",
)


type _Jsonish = t.Mapping[str, t.Any]


class OutputFormat(enum.Enum):
    """Different output formats available for structured data."""

    JSON = enum.auto()
    MARKDOWN = enum.auto()


@dataclass
class _with_print_json[R]:  # noqa: N801  # invalid-name
    """Decorator for pretty-printing returned data from a Click command."""

    adapter: pydantic.TypeAdapter[R]
    markdown: t.Callable[[R], str]

    def __call__[**P](
        self, command: t.Callable[P, R]
    ) -> t.Callable[t.Concatenate[OutputFormat, P], None]:
        @functools.wraps(command)
        @click.option(
            "--format",
            type=click.Choice(OutputFormat, case_sensitive=False),
            default=OutputFormat.JSON,
            show_default=True,
            help="Choose the output format, e.g. Markdown. [default: json]",
        )
        def command_with_json_output(
            format: OutputFormat, *args: P.args, **kwargs: P.kwargs
        ) -> None:
            data = command(*args, **kwargs)
            match format:
                case OutputFormat.JSON:
                    rich.print_json(data=self.adapter.dump_python(data, mode="json"))
                case OutputFormat.MARKDOWN:
                    click.echo(self.markdown(data))
                case other:  # pragma: no cover
                    t.assert_never(other)

        return command_with_json_output


_ExistingFilePath = click.Path(
    exists=True, path_type=pathlib.Path, file_okay=True, dir_okay=False
)


@app.command()
@click.argument("lockfile", type=_ExistingFilePath)
@_with_print_json(ganzua.LOCKFILE_SCHEMA, md_from_lockfile)
def inspect(lockfile: pathlib.Path) -> Lockfile:
    """Inspect a lockfile."""
    return ganzua.lockfile_from(lockfile)


@app.command()
@click.argument("old", type=_ExistingFilePath)
@click.argument("new", type=_ExistingFilePath)
@_with_print_json(ganzua.DIFF_SCHEMA, md_from_diff)
def diff(old: pathlib.Path, new: pathlib.Path) -> Diff:
    """Compare two lockfiles."""
    return ganzua.diff(
        ganzua.lockfile_from(old),
        ganzua.lockfile_from(new),
    )


@app.group()
def constraints() -> None:
    """Work with `pyproject.toml` constraints."""


@constraints.command("inspect")
@click.argument("pyproject", type=_ExistingFilePath)
@_with_print_json(ganzua.REQUIREMENTS_SCHEMA, md_from_requirements)
def constraints_inspect(pyproject: pathlib.Path) -> Requirements:
    """List all constraints in the `pyproject.toml` file."""
    with error_context(f"while parsing {pyproject}"):
        doc = tomlkit.parse(pyproject.read_text())
    collector = ganzua.CollectRequirement([])
    ganzua.edit_pyproject(doc, collector)
    return Requirements(requirements=collector.reqs)


@constraints.command("bump")
@click.argument("pyproject", type=_ExistingFilePath)
@click.option(
    "--lockfile",
    type=_ExistingFilePath,
    required=True,
    help="Where to load versions from. Required.",
)
@click.option("--backup", type=click.Path(), help="Store a backup in this file.")
def constraints_bump(
    lockfile: pathlib.Path, pyproject: pathlib.Path, backup: pathlib.Path | None
) -> None:
    """Update `pyproject.toml` dependency constraints to match the lockfile.

    Of course, the lockfile should always be a valid solution for the constraints.
    But often, the constraints are somewhat relaxed.
    This tool will *increment* the constraints to match the currently locked versions.
    Specifically, the locked version becomes a lower bound for the constraint.

    This tool will try to be as granular as the original constraint.
    For example, given the old constraint `foo>=3.5` and the new version `4.7.2`,
    the constraint would be updated to `foo>=4.7`.
    """
    if backup is not None:
        shutil.copy(pyproject, backup)

    locked = ganzua.lockfile_from(lockfile)
    with _toml_edit_scope(pyproject) as doc:
        ganzua.edit_pyproject(doc, ganzua.UpdateRequirement(locked))


class ConstraintResetGoal(enum.Enum):
    """Intended result for `ganzua constraints reset` operations."""

    NONE = enum.auto()
    """Remove all constraints."""

    MINIMUM = enum.auto()
    """Set constraints constraints to the currently locked minimum, removing upper bounds."""


@constraints.command("reset")
@click.argument("pyproject", type=_ExistingFilePath)
@click.option("--backup", type=click.Path(), help="Store a backup in this file.")
@click.option(
    "--to",
    type=click.Choice(ConstraintResetGoal, case_sensitive=False),
    default=ConstraintResetGoal.NONE,
    help="""\
How to reset constraints.
* `none` (default): remove all constraints
* `minimum`: set constraints to the currently locked minimum, removing upper bounds
""",
)
@click.option(
    "--lockfile",
    type=_ExistingFilePath,
    required=False,
    help="Where to load current versions from (for `--to=minimum`).",
)
@click.pass_context
def constraints_reset(
    ctx: click.Context,
    pyproject: pathlib.Path,
    *,
    backup: pathlib.Path | None,
    lockfile: pathlib.Path | None,
    to: ConstraintResetGoal,
) -> None:
    """Remove or relax any dependency version constraints from the `pyproject.toml`.

    This can be useful for allowing uv/Poetry to update to the most recent versions,
    ignoring the previous constraints. Approximate recipe:

    ```bash
    ganzua constraints reset --backup=pyproject.toml.bak pyproject.toml
    uv lock --upgrade  # perform the upgrade
    mv pyproject.toml.bak pyproject.toml  # restore old constraints
    ganzua constraints bump --lockfile=uv.lock pyproject.toml
    uv lock
    ```
    """
    edit: ganzua.EditRequirement
    match to:
        case ConstraintResetGoal.NONE:
            edit = ganzua.UnconstrainRequirement()
        case ConstraintResetGoal.MINIMUM:
            if lockfile is None:
                ctx.fail("using `--to=minimum` requires a `--lockfile`")
            edit = ganzua.SetMinimumRequirement(ganzua.lockfile_from(lockfile))
        case other:  # pragma: no cover
            t.assert_never(other)

    if backup is not None:
        shutil.copy(pyproject, backup)

    with _toml_edit_scope(pyproject) as doc:
        ganzua.edit_pyproject(doc, edit)


@contextlib.contextmanager
def _toml_edit_scope(path: pathlib.Path) -> t.Iterator[tomlkit.TOMLDocument]:
    """Load the TOML file and write it back afterwards."""
    with error_context(f"while parsing {path}"):
        old_contents = path.read_text()
        doc = tomlkit.parse(old_contents)

    yield doc

    new_contents = doc.as_string()
    if new_contents != old_contents:
        path.write_text(new_contents)


SchemaName = t.Literal["inspect", "diff", "constraints-inspect"]


@app.command()
@click.argument("command", type=click.Choice(t.get_args(SchemaName)))
def schema(command: SchemaName) -> None:
    """Show the JSON schema for the output of the given command."""
    adapter: pydantic.TypeAdapter[t.Any]
    match command:
        case "inspect":
            adapter = ganzua.LOCKFILE_SCHEMA
        case "diff":
            adapter = ganzua.DIFF_SCHEMA
        case "constraints-inspect":
            adapter = ganzua.REQUIREMENTS_SCHEMA
        case other:  # pragma: no cover
            t.assert_never(other)
    schema = adapter.json_schema(mode="serialization")
    rich.print_json(data=schema)
