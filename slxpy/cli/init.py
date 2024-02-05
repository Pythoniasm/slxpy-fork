from pathlib import Path

import click


@click.command()
@click.option("--compact", "-c", is_flag=True, help="Generate compact toml config.")
@click.pass_context
def init(ctx: click.Context, compact: bool):
    """
    Initialize slxpy working directory.
    """
    workdir: Path = ctx.obj["workdir"]

    from slxpy.frontend.init import init_interactive

    init_interactive(workdir, compact=compact)
