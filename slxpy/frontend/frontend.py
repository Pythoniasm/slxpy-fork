import glob
import json
import os
from pathlib import Path

import slxpy.common.constants as C
from slxpy.common.context import Context, Enumerator, Field, FieldMode, Method, ModelClass, Module, Type, TypeContainer
from slxpy.common.env_config import Config as EnvConfig
from slxpy.common.model_config import Config as ModelConfig
from slxpy.common.model_config import InfoConfig


def adapt_metadata(workdir: Path):
    modeldir = workdir / C.model_dir

    with (workdir / C.model_config_name).open("rb") as f:
        model_config = ModelConfig.load(f)
    with (workdir / C.env_config_name).open("rb") as f:
        env_config = EnvConfig.load(f)

    metadata = json.loads((workdir / C.metadata_name).read_text())
    assert metadata["__version__"] == Context.VERSION, "Metadata version incompatible"

    # TODO: Also check metadata["features"]
    name, model_class, structs = metadata["name"], metadata["model_class"], metadata["structs"]
    doc = metadata["description"] if model_config.info.description == InfoConfig.AUTO else model_config.info.description
    author = metadata["author"] if model_config.info.author == InfoConfig.AUTO else model_config.info.author
    version = metadata["version"] if model_config.info.version == InfoConfig.AUTO else model_config.info.version
    license = "" if model_config.info.license == InfoConfig.NO_LICENSE else model_config.info.license

    model_class_ctx = ModelClass(
        name=model_class["name"],
        doc=doc,
        namespace=model_class["namespace"],
        identifier=model_class["identifier"],
        sample_time=metadata["sample_time"],
        methods=[Method(name=me["name"], doc="") for me in model_class["methods"]],
        fields=[make_field(fi, True) for fi in model_class["fields"]],
        field_mapping=model_class["field_mapping"],
        type_mapping=model_class["type_mapping"],
    )
    types = TypeContainer([make_type(st) for st in structs], model_class_ctx)
    module = Module(
        name=name,
        doc=doc,
        version=version,
        author=author,
        license=license,
        model_class=model_class_ctx,
        types=types,
        env=env_config,
    )
    module.env.check_basic_compatibility(module)
    module.env.expand_config(module)
    context = Context(
        sources=[
            # For nested model source in Simscape models
            os.path.relpath(x, modeldir).replace("\\", "/")
            for x in (
                glob.glob(str(modeldir / "*.cpp"))
                + glob.glob(str(modeldir / "*.c"))
                + glob.glob(str(modeldir / "*" / "*.c"))
            )
        ],
        headers=[f"{name}.h"],
        module=module,
    )
    with (workdir / C.project_ir_name).open("w") as f:
        context.dump(f, debug=False)


def make_type(st: dict):
    if st.get("is_enum", False):
        return Type(
            name=st["name"],
            doc="",
            location=st["location"],
            is_enum=True,
            fields=[make_enumerator(fi) for fi in st["fields"]],
        )
    else:
        return Type(
            name=st["name"],
            doc="",
            location=st["location"],
            is_enum=False,
            fields=[make_field(fi, False) for fi in st["fields"]],
        )


# Consider using Flag
field_mode_mapping = {
    ("model", False): FieldMode.MODEL,
    ("plain", False): FieldMode.PLAIN,
    ("plain", True): FieldMode.PLAIN_ARRAY,
    ("struct", False): FieldMode.STRUCT,
    ("struct", True): FieldMode.STRUCT_ARRAY,
    ("enum", False): FieldMode.ENUM,
    ("enum", True): FieldMode.ENUM_ARRAY,
    ("pointer", False): FieldMode.POINTER,
    ("pointer", True): FieldMode.POINTER_ARRAY,
}


def ensure_list(list_like):
    return list_like if isinstance(list_like, list) else [list_like]


def make_field(fi: dict, model: bool):
    mode = "model" if model else fi["mode"]
    is_array = fi.get("is_array", False)
    if mode == "std":
        raise NotImplementedError("No std class support yet.")
    if mode == "struct" or mode == "enum":
        type = fi["type"]
    elif mode == "pointer":
        type = fi["underlying"]
    else:
        type = None
    return Field(
        name=fi["name"],
        doc="",
        mode=field_mode_mapping[(mode, is_array)],
        raw_shape=ensure_list(fi["shape"]) if is_array else None,
        type=type,
    )


def make_enumerator(fi: dict):
    return Enumerator(name=fi["name"], doc="", value=fi["value"])
