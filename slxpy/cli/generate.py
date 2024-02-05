import textwrap
from pathlib import Path

import click

from slxpy.cli.utils import ensure_slxpy_project, get_plat_specifier, is_debug


@click.command()
@click.pass_context
def frontend(ctx: click.Context):
    """
    Execute slxpy frontend.
    Transform simulink metadata and user config into IR.
    """
    workdir: Path = ctx.obj["workdir"]
    ensure_slxpy_project(workdir)

    click.echo("Execute frontend.", nl=False)
    from slxpy.frontend.frontend import adapt_metadata

    adapt_metadata(workdir)
    click.secho(" SUCCESS", fg="green")


@click.command()
@click.pass_context
def backend(ctx: click.Context):
    """
    Execute slxpy backend.
    Transform IR into binding code and build scripts.
    """
    workdir: Path = ctx.obj["workdir"]
    ensure_slxpy_project(workdir)

    click.echo("Execute backend.", nl=False)
    from slxpy.backend.renderer import render

    render(workdir, is_debug())
    click.secho(" SUCCESS", fg="green")


@click.command()
@click.option("--build", is_flag=True, help="Also build the project.")
@click.pass_context
def generate(ctx: click.Context, build: bool):
    """
    Execute slxpy frontend and backend.
    Produce a self-contained, portable source project.
    """
    workdir: Path = ctx.obj["workdir"]
    ensure_slxpy_project(workdir)

    ctx.invoke(frontend)
    ctx.invoke(backend)
    if build:
        import subprocess
        import sys

        args = [sys.executable, "setup.py", "build"]
        click.echo(f"Run \"{' '.join(args)}\" to build extension.")
        cp = subprocess.run(args, cwd=workdir)
        cp.check_returncode()
        plat_specifier = get_plat_specifier()
        libdir = workdir / "build" / f"lib{plat_specifier}"
        click.echo(f"\nBuild successful. Check {libdir} for output.")
    else:
        output_text = textwrap.dedent(
            f"""\
        To build the extension, run in command line:
            > cd "{workdir}"
            > python setup.py build
        """
        ).strip()
        click.echo(output_text)
