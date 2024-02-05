from pathlib import Path

import click

import slxpy.common.constants as C
from slxpy.cli.utils import ensure_slxpy_project


@click.command()
@click.option("--build/--no-build", default=False, help="With build folder.")
@click.option("--asset/--no-asset", default=True, help="Without slxpy generated assets.")
@click.option("--model/--no-model", default=True, help="Without Simulink mdoel sources.")
@click.option(
    "--out",
    default=None,
    type=click.Path(dir_okay=False, resolve_path=True, path_type=Path),
    help="Output zip file name.",
)
@click.pass_context
def pack(ctx: click.Context, build: bool, asset: bool, model: bool, out: Path):
    """
    Pack assets for transfer.
    """
    workdir: Path = ctx.obj["workdir"]
    ensure_slxpy_project(workdir)

    if out is None:
        out = Path(f"{workdir.name}.zip")
    parentdir = workdir.parent
    import zipfile

    def writedir(z: zipfile.ZipFile, dir: Path):
        assert dir.exists(), f"Folder not exist: {dir.relative_to(workdir)}"
        assert dir.is_dir()
        for p in dir.glob("**/*"):
            if p.is_dir():
                continue
            z.write(p, arcname=p.relative_to(parentdir))
        click.echo(f"Add folder: {dir.relative_to(workdir)}")

    def writefile(z: zipfile.ZipFile, file: Path):
        assert file.exists(), f"File not exist: {file.relative_to(workdir)}"
        assert file.is_file()
        z.write(file, arcname=file.relative_to(parentdir))
        click.echo(f"Add file:   {file.relative_to(workdir)}")

    try:
        with zipfile.ZipFile(out, mode="w", compression=zipfile.ZIP_LZMA) as z:
            writefile(z, workdir / C.model_config_name)
            writefile(z, workdir / C.env_config_name)
            if model:
                writedir(z, workdir / C.model_dir)
            if asset:
                from slxpy.backend.renderer import assets

                writedir(z, workdir / "include")
                generated_files = [asset.name for asset in assets] + [C.project_ir_name]
                for f in generated_files:
                    writefile(z, workdir / f)
            if build:
                writedir(z, workdir / "build")
    except:
        out.unlink()
        raise
