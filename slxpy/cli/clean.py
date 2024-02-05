from pathlib import Path
from typing import List

import click

import slxpy.common.constants as C
from slxpy.cli.utils import ensure_slxpy_project


@click.command()
@click.option("--all", is_flag=True, help="Complete cleanup, keeping config files only.")
@click.pass_context
def clean(ctx: click.Context, all: bool):
    """
    Clean up working directory.
    """
    workdir: Path = ctx.obj["workdir"]
    ensure_slxpy_project(workdir)

    import shutil

    def rmdir(dir: Path):
        if dir.exists():
            assert dir.is_dir()
            shutil.rmtree(dir)
            click.echo(f"Remove folder: {dir.relative_to(workdir)}")
        else:
            click.echo(f"Skip folder:   {dir.relative_to(workdir)}")

    def rmfile(file: Path):
        if file.exists():
            assert file.is_file()
            file.unlink()
            click.echo(f"Remove file:   {file.relative_to(workdir)}")
        else:
            click.echo(f"Skip file:     {file.relative_to(workdir)}")

    rmdir(workdir / "build")
    rmdir(workdir / "include")

    from slxpy.backend.renderer import assets

    generated_files: List[str] = [asset.name for asset in assets] + [C.project_ir_name]
    for f in generated_files:
        rmfile(workdir / f)

    if all:
        rmdir(workdir / "model")
        rmfile(workdir / C.metadata_name)
