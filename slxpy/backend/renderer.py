import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List

import importlib_resources

import slxpy.common.constants as C
from slxpy.backend.filter import add_filters
from slxpy.common.context import Context, FieldMode
from slxpy.common.jinja import create_jinja_env


@dataclass
class AssetInfo:
    name: str
    template: str
    condition: Callable[[Context], bool] = lambda _: True
    overwrite: bool = True


assets: List[AssetInfo] = [
    AssetInfo(name="module.cc", template="module.cc.jinja"),
    AssetInfo(name="setup.py", template="setup.py.jinja"),
    AssetInfo(name="pyproject.toml", template="pyproject.toml.jinja"),
    AssetInfo(name="raw_env.h", template="raw_env.h.jinja", condition=lambda context: context.module.env.use_raw),
    AssetInfo(
        name="common_env.h",
        template="common_env.h.jinja",
        condition=lambda context: context.module.env.use_raw or context.module.env.use_gym,
    ),
    AssetInfo(name="gym_env.h", template="gym_env.h.jinja", condition=lambda context: context.module.env.use_gym),
    AssetInfo(name="CMakeLists.txt", template="CMakeLists.txt.jinja"),
    AssetInfo(name="test_extension.py", template="test_extension.py.jinja", overwrite=False),
]

includes = ["common.h", "bind.h", "complex.h", "data.h", "simulink_builtin.h", "env.h"]


def render(workdir: Path, debug: bool = False):
    context_path = workdir / C.project_ir_name
    with context_path.open() as f:
        context = Context.load(f)

    if debug:
        context_debug_path = workdir / f"{context_path.stem}.debug.json"
        with context_debug_path.open("w") as f:
            context.dump(f, debug=True)

    env = create_jinja_env("backend")
    add_filters(env)
    env.globals["FieldMode"] = FieldMode

    active_assets = [asset for asset in assets if asset.condition(context)]
    optional_headers = [asset.name for asset in active_assets if asset.name.endswith(".h")]
    for asset in active_assets:
        asset_name, template = asset.name, asset.template
        asset_path = workdir / asset_name
        if asset.overwrite or not asset_path.exists():
            text = env.get_template(template).render(
                C=context, slxpy_headers=includes, optional_headers=optional_headers
            )
            asset_path.write_text(text)

    include_src = importlib_resources.files("slxpy.include")
    include_dst = workdir / "include"
    include_dst.mkdir(exist_ok=True)

    include_slxpy_dst = include_dst / "slxpy"
    include_slxpy_dst.mkdir(exist_ok=True)
    for inc in includes:
        inc_src = include_src / inc
        inc_dst = include_slxpy_dst / inc
        shutil.copyfile(inc_src, inc_dst)

    include_thirdparty = include_src / "third-party"
    shutil.copytree(include_thirdparty / "nlohmann", include_dst / "nlohmann", dirs_exist_ok=True)
    shutil.copytree(include_thirdparty / "fmt", include_dst / "fmt", dirs_exist_ok=True)
