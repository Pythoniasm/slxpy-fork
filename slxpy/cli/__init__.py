from pathlib import Path

import click

from slxpy.cli.utils import is_debug, set_debug


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug mode.")
@click.option(
    "--workdir",
    "-w",
    default=".",
    type=click.Path(file_okay=False, resolve_path=True, path_type=Path),
    help="Working directory, must be empty or nonexistent. (Default to cwd)",
)
@click.pass_context
def app(ctx: click.Context, workdir: Path, debug: bool):
    set_debug(debug)

    ctx.ensure_object(dict)
    ctx.obj["workdir"] = workdir
    click.echo(f"Working directory: {workdir}")


def entry_point():
    try:
        app()
    except Exception as e:
        click.secho(str(e), fg="red", err=True)
        if is_debug():
            raise
        else:
            exit(1)


def _register_cli_commands(app: click.Group):
    from slxpy.cli.clean import clean
    from slxpy.cli.generate import backend, frontend, generate
    from slxpy.cli.init import init
    from slxpy.cli.multi_build import multi_build
    from slxpy.cli.pack import pack

    app.add_command(init)
    app.add_command(frontend)
    app.add_command(backend)
    app.add_command(generate)
    app.add_command(multi_build)
    app.add_command(clean)
    app.add_command(pack)


_register_cli_commands(app)
