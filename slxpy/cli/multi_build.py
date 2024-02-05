import shutil
from pathlib import Path
from typing import Tuple

import click

from slxpy.cli.conda import (
    check_conda_installation,
    create_conda_env,
    get_conda_env_set,
    remove_conda_env,
    run_in_conda_env,
)
from slxpy.cli.utils import ensure_slxpy_project, get_plat_name, get_plat_specifier

# Python 3.7 & Setuptools 62.0.0 leads to a bug about EXT_SUFFIX on windows
# So, remove this version from default list
# See: https://github.com/pypa/setuptools/issues/3219
DEFAULT_PYTHON_VERSIONS = ["3.8", "3.9", "3.10"]


@click.group()
@click.pass_context
def multi_build(ctx: click.Context):
    """
    Build project for multiple Python versions.
    """


@multi_build.command()
@click.option(
    "--versions",
    "-v",
    multiple=True,
    default=DEFAULT_PYTHON_VERSIONS,
    show_default=True,
    help="Python version to setup conda environment with.",
)
def setup(versions: Tuple[str, ...]):
    """
    Setup builder environment with conda.
    """
    versions = tuple(map(_validate_python_version, versions))
    click.secho("Setup builder environment with conda.", fg="green")
    check_conda_installation()
    envs = get_conda_env_set()
    for version in versions:
        env_name = _get_env_name(version)
        if env_name not in envs:
            click.secho(f"Creating {env_name}.", fg="green")
            create_conda_env(env_name, [f"python={version}", "pybind11", "pybind11-stubgen", "numpy", "gymnasium"])
        else:
            click.secho(f"{env_name} already exists. Skipping.", fg="yellow")


@multi_build.command()
@click.option(
    "--versions",
    "-v",
    multiple=True,
    default=DEFAULT_PYTHON_VERSIONS,
    show_default=True,
    help="Python version to remove conda environment with.",
)
def clean(versions: Tuple[str, ...]):
    """
    Remove builder environment.
    """
    versions = tuple(map(_validate_python_version, versions))
    click.secho("Remove builder environment.", fg="green")
    check_conda_installation()
    envs = get_conda_env_set()
    for version in versions:
        env_name = _get_env_name(version)
        if env_name in envs:
            click.secho(f"Creating {env_name}.", fg="green")
            remove_conda_env(env_name)
        else:
            click.secho(f"{env_name} not exists. Skipping.", fg="yellow")
    click.secho("You may need to delete conda env folders manually.", fg="yellow")


@multi_build.command()
@click.option(
    "--versions",
    "-v",
    multiple=True,
    default=DEFAULT_PYTHON_VERSIONS,
    show_default=True,
    help="Python version to build project with.",
)
@click.option(
    "--aggregate-output",
    "-a",
    default=None,
    type=click.Path(file_okay=False, resolve_path=True, path_type=Path),
    help="Folder to aggregate build results into. [default: {workdir}/build/slxpy{plat}]",
)
@click.option("--aggregate/--no-aggregate", default=True, show_default=True, help="Aggregate build results or not.")
@click.pass_context
def run(ctx: click.Context, versions: Tuple[str, ...], aggregate_output: Path, aggregate: bool):
    """
    Build project for multiple Python versions.
    """
    workdir: Path = ctx.obj["workdir"]
    ensure_slxpy_project(workdir)
    versions = tuple(map(_validate_python_version, versions))
    click.secho("Setup builder environment with conda.", fg="green")
    check_conda_installation()
    envs = get_conda_env_set()
    target_envs = set(map(_get_env_name, versions))
    if not target_envs.issubset(envs):
        raise click.BadParameter(
            f'Missing environments: {target_envs - envs}, please run "slxpy multi-build setup" first.'
        )
    for version in versions:  # Not using target_envs as set is not ordered.
        env_name = _get_env_name(version)
        click.secho(f"Building project in {env_name}.", fg="green")
        run_in_conda_env(env_name, workdir, ["python", "setup.py", "build_ext"])

    if aggregate:
        if aggregate_output is None:
            aggregate_output = workdir / "build" / f"slxpy.{get_plat_name()}"
        aggregate_output = aggregate_output.absolute()
        aggregate_output.mkdir(exist_ok=True, parents=False)

        click.secho(f"Aggregate build results to {aggregate_output}.", fg="green")
        for version in versions:
            plat_specifier = get_plat_specifier(version)
            build_dir = workdir / "build" / f"lib{plat_specifier}"
            shutil.copytree(build_dir, aggregate_output, dirs_exist_ok=True)


def _validate_python_version(version_str: str):
    from packaging.version import Version
    from packaging.version import parse as parse_version

    version = parse_version(version_str)
    if version.major != 3:
        raise click.BadParameter("Only Python 3.x is supported.")
    elif version.minor < 7:
        raise click.BadParameter("Only Python 3.7 and above is supported.")
    else:
        major_minor: Version = parse_version(f"{version.major}.{version.minor}")
        if version != major_minor:
            click.secho(f"Warning: micro will be ignored, {version.base_version} -> {major_minor}", fg="yellow")
        return str(major_minor)


def _get_env_name(version: str):
    return f"slxpy-builder-{version}"
