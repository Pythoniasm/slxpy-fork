import jinja2


def create_jinja_env(package_path: str):
    # Import namespace package is broken in Jinja2 < 3.0
    # See: https://github.com/pallets/jinja/issues/1097
    # To avoid obscure errors, we check the version early.
    _check_jinja_version()
    loader = jinja2.PackageLoader(package_name="slxpy.templates", package_path=package_path, encoding="utf-8")
    env = jinja2.Environment(
        # extensions=['jinja2.ext.debug'],
        loader=loader,
        auto_reload=False,
        autoescape=False,
        keep_trailing_newline=True,
        # trim_blocks=True,
    )
    env.policies["json.dumps_kwargs"] = {"indent": 4, "sort_keys": True, "ensure_ascii": False}
    return env


def _check_jinja_version():
    from packaging.version import parse as parse_version

    actual = parse_version(jinja2.__version__)
    required = parse_version("3.0")
    if actual < required:
        raise RuntimeError(f"jinja2 version {actual} is too old. " f"Please upgrade to {required} or later.")
