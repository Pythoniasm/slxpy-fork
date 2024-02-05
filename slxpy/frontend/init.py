import re
import textwrap
from pathlib import Path

import click

import slxpy.common.constants as C
from slxpy.common.env_config import Config as EnvConfig
from slxpy.common.fs import dir_empty
from slxpy.common.jinja import create_jinja_env
from slxpy.common.model_config import Config as ModelConfig


def check_valid_workspace(workdir: Path):
    """
    Either raise or return
    """
    if workdir.exists():
        if workdir.is_dir():
            if not dir_empty(workdir):
                if (workdir / C.model_config_name).is_file():
                    raise ValueError(
                        f"Folder {workdir} is already inited as a slxpy project. Choose another path instead."
                    )
                else:
                    raise ValueError(f"Folder {workdir} has content. Expect an empty folder")
            # else: OK
        else:
            raise NotADirectoryError("Expect workdir to be a directory")
    # else: OK


def init_interactive(workdir: Path, compact: bool = False):
    check_valid_workspace(workdir)
    model, class_name, namespace = get_info_interactive(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    model_cfg_path, env_cfg_path = init(workdir, model, class_name, namespace, compact=compact)

    output_text = textwrap.dedent(
        f"""\
        Working directory: {workdir}
        Initialize config files:
            {model_cfg_path.name:<12} - Basic Simulink code generation config.
            {' ' * (12 + 3)}Adjust [simulink] and other sections as needed.
            {env_cfg_path.name:<12} - Raw/gymnasium-like environment wrapper config.
    """
    ).strip()
    click.echo(output_text)


def get_info_interactive(workdir: Path):
    workdir_name = workdir.name
    if workdir_name.isidentifier():
        model_default, class_name_default = workdir_name, f"{workdir_name}ModelClass"
    else:
        model_default, class_name_default = None, None

    matlab_naming = re.compile("^[a-zA-Z][a-zA-Z0-9_]*$")
    cpp_naming = re.compile("^[a-zA-Z_][a-zA-Z0-9_]*$")

    model: str = click.prompt("Simulink model name", type=str, default=model_default)
    assert matlab_naming.match(model), "Simulink model name is not valid."
    class_name: str = click.prompt("Code generation C++ class name", type=str, default=class_name_default)
    assert cpp_naming.match(class_name), "C++ class name is not valid."
    namespace: str = click.prompt("Code generation C++ namespace", type=str, default="")
    assert namespace == "" or cpp_naming.match(namespace), "C++ namespace name is not valid."

    return model, class_name, namespace


def init(workdir: Path, model: str, class_name: str, namespace: str, compact: bool = False):
    env = create_jinja_env("frontend")
    env.filters["tf"] = lambda x: "true" if x else "false"

    model_config = ModelConfig.default(model, class_name, namespace)
    model_template_name = f"{C.model_config_name}.jinja"
    if compact:
        model_template_name = "compact-" + model_template_name
    model_cfg_text = env.get_template(model_template_name).render(config=model_config)
    model_cfg_path = workdir / C.model_config_name
    model_cfg_path.write_text(model_cfg_text)

    env_config = EnvConfig.default()
    env_template_name = f"{C.env_config_name}.jinja"
    if compact:
        env_template_name = "compact-" + env_template_name
    env_cfg_text = env.get_template(env_template_name).render(config=env_config)
    env_cfg_path = workdir / C.env_config_name
    env_cfg_path.write_text(env_cfg_text)

    return model_cfg_path, env_cfg_path
