import json
import os
import subprocess
import textwrap
from pathlib import Path
from typing import List

import click


def check_conda_installation():
    try:
        get_conda_executable()
    except KeyError:
        raise click.ClickException(
            textwrap.dedent(
                """\
        Conda package is not installed in current environment.
        To use this command, you need to check three things:
            1. Ensure anaconda/miniconda is installed in your system.
            2. This command is run in a conda environment.
        """
            ).strip()
        )


def get_conda_env_set():
    def _postprocess(env: str):
        env_path = Path(env)
        return env_path.name

    args = ["env", "list"]
    env_text_list: List[str] = execute_conda_command(args)["envs"]
    return set(_postprocess(env) for env in env_text_list)


def create_conda_env(env_name: str, packages: str):
    args = ["create", "--name", env_name, "--channel", "conda-forge", "--override-channels", "--yes", *packages]
    run_conda_command(args)


def remove_conda_env(env_name: str):
    args = ["env", "remove", "--name", env_name, "--yes"]
    run_conda_command(args)


def run_in_conda_env(env_name: str, cwd: str, args: List[str]):
    args = ["run", "--name", env_name, "--no-capture-output", "--live-stream", "--cwd", cwd, *args]
    run_conda_command(args)


def get_conda_executable():
    return os.environ["CONDA_EXE"]


def execute_conda_command(args: List[str], json_output: bool = True):
    args = [get_conda_executable()] + args
    if json_output:
        args.append("--json")
    text = subprocess.check_output(args).decode("utf-8")
    if json_output:
        return json.loads(text)
    else:
        return text


def run_conda_command(args: List[str]):
    args = [get_conda_executable()] + args
    cp = subprocess.run(args)
    cp.check_returncode()
