import sys
from pathlib import Path
from typing import Optional

import slxpy.common.constants as C

DEBUG = False


def set_debug(debug: bool):
    global DEBUG
    DEBUG = debug


def is_debug():
    return DEBUG


def ensure_slxpy_project(workdir: Path):
    # Safe check except init subcommand
    if not (workdir / C.model_config_name).exists() or not (workdir / C.env_config_name).exists():
        raise Exception("Not a slxpy project directory.")


def get_plat_name():
    import distutils.util

    return distutils.util.get_platform()


def get_plat_specifier(version: Optional[str] = None) -> str:
    # Ported from setuptools/_distutils/command/build.py
    import setuptools
    from packaging.version import parse as parse_version

    actual = parse_version(setuptools.__version__)
    changed = parse_version("62.1.0")
    if actual < changed:
        # Old behavior
        if version is None:
            version = f"{sys.version_info.major}.{sys.version_info.minor}"
        plat_name = get_plat_name()
        return f".{plat_name}-{version}"
    else:
        # New behavior, since 62.1.0
        tag = sys.implementation.cache_tag
        if version is not None:
            version = version.replace(".", "")
            current = f"{sys.version_info.major}{sys.version_info.minor}"
            assert tag.endswith(current)
            tag = tag[: -len(current)] + version
        plat_name = get_plat_name()
        return f".{plat_name}-{tag}"
