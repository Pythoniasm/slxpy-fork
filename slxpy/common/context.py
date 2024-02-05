import json
from collections.abc import Sequence
from dataclasses import dataclass, field, fields
from functools import cached_property
from typing import Any, Callable, ClassVar, Dict, List, Literal, Optional, TextIO, Tuple, Union

import numpy as np

import slxpy.common.constants as C
from slxpy.common.enum import FieldMode
from slxpy.common.env_config import Config as EnvConfig
from slxpy.common.tsort import tsort

# NOTE: Currently nested struct hierarchy is dropped, seeking use-case and better implementation.


@dataclass
class Field:
    name: str
    doc: str

    mode: FieldMode
    raw_shape: Optional[List[int]]  # Available when mode is *_ARRAY
    type: Optional[str]  # Available when mode is STRUCT or STRUCT_ARRAY

    @property
    def size(self):
        prod = 1
        if self.shape is not None:
            for el in self.shape:
                prod *= el
        return prod

    @property
    def shape(self):
        """
        NOTE: temporary patch for MATLAB limitation for row-major layout
        https://ww2.mathworks.cn/help/rtw/ug/code-generation-of-matrix-data-and-arrays.html
        In brief, lack of support for some fundemental blocks such as Integrator and Transfer Fcn,
        which is awkward and annoying.
        So, revert `UseRowMajorAlgorithm` to `off` and `ArrayLayout` to `Column-major`
        Transpose dimensions here to make a F-contiguous array C-contiguous.
        See also: tune_codegen_config.m
        """
        if self.raw_shape is None:
            return None
        if len(self.raw_shape) == 2 and (self.raw_shape[0] == 1 or self.raw_shape[1] == 1):
            # Workaround for 1-dimensional InstP array got generated as [x 1]
            # Consider put the logic here or MATLAB script postprocess.m
            # Check whether it is safe
            return [self.raw_shape[0] * self.raw_shape[1]]
        else:
            return self.raw_shape[::-1]

    @staticmethod
    def reconstruct(d: dict):
        mode = FieldMode(d["mode"])
        if mode == FieldMode.PLAIN or mode == FieldMode.MODEL:
            shape, type = None, None
        elif mode == FieldMode.PLAIN_ARRAY:
            shape, type = d["shape"], None
        elif mode == FieldMode.STRUCT:
            shape, type = None, d["type"]
        elif mode == FieldMode.STRUCT_ARRAY:
            shape, type = d["shape"], d["type"]
        elif mode == FieldMode.ENUM:
            shape, type = None, d["type"]
        elif mode == FieldMode.ENUM_ARRAY:
            shape, type = d["shape"], d["type"]
        elif mode == FieldMode.POINTER:
            shape, type = None, d["type"]
        elif mode == FieldMode.POINTER_ARRAY:
            shape, type = d["shape"], d["type"]
        else:
            raise ValueError(f"Unsupported field mode: {mode}")

        return Field(name=d["name"], doc=d.get("doc", ""), mode=mode, raw_shape=shape, type=type)

    def asdict(self, dict_filter):
        d = {"name": self.name, "doc": self.doc, "mode": self.mode.value, "shape": self.raw_shape, "type": self.type}
        assert len(d) == len(fields(self))  # Ensure no left-out
        return dict_filter(d)


@dataclass
class Enumerator:
    name: str
    doc: str
    value: int

    @staticmethod
    def reconstruct(d: dict):
        return Enumerator(name=d["name"], doc=d.get("doc", ""), value=d["value"])

    def asdict(self, dict_filter):
        d = {"name": self.name, "doc": self.doc, "value": self.value}
        assert len(d) == len(fields(self))  # Ensure no left-out
        return dict_filter(d)


@dataclass
class Type:
    name: str
    doc: str
    location: Literal["root", "model_class"]
    is_enum: bool
    fields: Union[List[Field], List[Enumerator]]  # NOTE: Maybe bad design

    _id: int = field(init=False)
    _alias_name: str = field(init=False)
    _binding_name: str = field(init=False)
    _binding_identifier: str = field(init=False)

    def __post_init__(self):
        self._binding_name = self.name
        self._binding_identifier = f"{self._binding_name}_PB"

    def _assign_index(self, index: int):
        assert index >= 0
        self._id = index
        self._alias_name = f"SlxpyPodType_{index}"

    @cached_property
    def field_dict(self):
        return {field.name: field for field in self.fields}

    @staticmethod
    def reconstruct(d: dict):
        name = d["name"]
        location = d["location"]
        is_enum = d["is_enum"]
        FieldCls = Enumerator if is_enum else Field
        t = Type(
            name=name,
            doc=d.get("doc", ""),
            location=location,
            is_enum=is_enum,
            fields=[FieldCls.reconstruct(f) for f in d["fields"]],
        )
        return t

    def asdict(self, dict_filter):
        d = {
            "name": self.name,
            "doc": self.doc,
            "location": self.location,
            "is_enum": self.is_enum,
            "fields": [f.asdict(dict_filter) for f in self.fields],
            "_id": self._id,
            "_alias_name": self._alias_name,
            "_binding_name": self._binding_name,
            "_binding_identifier": self._binding_identifier,
        }
        assert len(d) == len(fields(self))  # Ensure no left-out
        return dict_filter(d)


class TypeContainer(Sequence):
    def __init__(self, types: List[Type], model_class: "ModelClass"):
        super().__init__()
        self._mc = model_class
        self._storage: List[Type] = []
        self._name_map: Dict[str, int] = {}
        for type in types:
            self._add(type)

    def _add(self, type: Type):
        if type.location == "model_class":
            identifier = f"{self._mc.identifier}::{type.name}"
        elif type.location == "root":
            identifier = type.name
        else:
            raise ValueError("Unexpected struct location.")
        index = len(self._storage)
        self._name_map[identifier] = index
        type._assign_index(index)
        self._storage.append(type)

    def lookup(self, name: str):
        for type in self._storage:
            if type.name == name:
                return type
        raise LookupError("Can't find type")

    @cached_property
    def dependency_order(self):
        return self.topo_sorted("dependency")

    @cached_property
    def hierarchy_order(self):
        return self.topo_sorted("hierarchy")

    @cached_property
    def in_root(self):
        return [type for type in self._storage if type.location == "root"]

    @cached_property
    def in_model_class(self):
        return [type for type in self._storage if type.location == "model_class"]

    def topo_sorted(self, order: Literal["dependency", "hierarchy"]):
        if order == "dependency":
            am = self._dependency_adjacency_matrix()
        elif order == "hierarchy":
            am = self._hierarchy_adjacency_matrix()
        else:
            raise ValueError("Unexpected sort order")
        indices = tsort(am)
        sorted_list = []
        for i in indices:
            sorted_list.append(self._storage[i])
        return sorted_list

    def _dependency_adjacency_matrix(self):
        verts = len(self._storage)
        am = np.zeros((verts, verts), dtype=np.bool_)
        for col, item in enumerate(self._storage):
            for this_field in item.fields:
                if isinstance(this_field, Field) and this_field.type is not None:
                    if this_field.type == "void":
                        continue
                    row = self._name_map[this_field.type]
                    am[row, col] = 1
        return am

    def _hierarchy_adjacency_matrix(self):
        raise NotImplementedError("Currently nested struct hierarchy is dropped")

    def __getitem__(self, index):
        return self._storage[index]

    def __len__(self):
        return len(self._storage)

    @staticmethod
    def reconstruct(ds: list, model_class: "ModelClass"):
        return TypeContainer([Type.reconstruct(d) for d in ds], model_class)

    def asdicts(self, dict_filter):
        return [t.asdict(dict_filter) for t in self._storage]


@dataclass
class Method:
    name: str
    doc: str
    # parameters, policy

    @staticmethod
    def reconstruct(d: dict):
        return Method(name=d["name"], doc=d.get("doc", ""))

    def asdict(self, dict_filter):
        d = {"name": self.name, "doc": self.doc}
        assert len(d) == len(fields(self))  # Ensure no left-out
        return dict_filter(d)


@dataclass
class ModelClass:
    name: str
    doc: str
    namespace: str
    identifier: str
    sample_time: float
    methods: List[Method]
    fields: List[Field]
    field_mapping: Dict[str, str]
    type_mapping: Dict[str, str]

    _alias_name: str = "SlxpyExtensionModelClass"
    _binding_name: str = field(init=False)
    _binding_identifier: str = field(init=False)

    def __post_init__(self):
        self._binding_name = self.name
        self._binding_identifier = f"{self._binding_name}_PB"

    @staticmethod
    def reconstruct(d: dict):
        return ModelClass(
            name=d["name"],
            doc=d.get("doc", ""),
            namespace=d.get("namespace", ""),
            identifier=d["identifier"],
            sample_time=d["sample_time"],
            methods=[Method.reconstruct(f) for f in d["methods"]],
            fields=[Field.reconstruct(f) for f in d["fields"]],
            field_mapping=d["field_mapping"],
            type_mapping=d["type_mapping"],
        )

    def asdict(self, dict_filter):
        d = {
            "name": self.name,
            "doc": self.doc,
            "namespace": self.namespace,
            "identifier": self.identifier,
            "sample_time": self.sample_time,
            "methods": [m.asdict(dict_filter) for m in self.methods],
            "fields": [f.asdict(dict_filter) for f in self.fields],
            "field_mapping": self.field_mapping,
            "type_mapping": self.type_mapping,
            "_alias_name": self._alias_name,
            "_binding_name": self._binding_name,
            "_binding_identifier": self._binding_identifier,
        }
        assert len(d) == len(fields(self))  # Ensure no left-out
        return dict_filter(d)


@dataclass
class Module:
    name: str
    doc: str
    version: str
    author: str
    license: str
    model_class: ModelClass
    types: TypeContainer
    env: EnvConfig

    @staticmethod
    def reconstruct(d: dict):
        model_class = ModelClass.reconstruct(d["model_class"])
        types = TypeContainer.reconstruct(d["types"], model_class)
        return Module(
            name=d["name"],
            doc=d.get("doc", ""),
            version=d["version"],
            author=d["author"],
            license=d["license"],
            model_class=model_class,
            types=types,
            env=EnvConfig.reconstruct(d["env"]),
        )

    def asdict(self, dict_filter):
        d = {
            "name": self.name,
            "doc": self.doc,
            "version": self.version,
            "author": self.author,
            "license": self.license,
            "model_class": self.model_class.asdict(dict_filter),
            "types": self.types.asdicts(dict_filter),
            "env": self.env.asdict(dict_filter),
        }
        assert len(d) == len(fields(self))  # Ensure no left-out
        return dict_filter(d)


@dataclass
class Context:
    sources: List[str]
    headers: List[str]
    module: Module
    VERSION: ClassVar[str] = C.metadata_version

    @staticmethod
    def load(fp: TextIO):
        d = json.load(fp)
        assert d["__version__"] == Context.VERSION, "Context version incompatible"
        return Context.reconstruct(d)

    def dump(self, fp: TextIO, debug: bool = False):
        if debug:
            dict_filter = lambda x: x
        else:

            def _concise_predicate(pair: Tuple[str, Any]):
                k, v = pair
                return not k.startswith("_") and v is not None and (k != "doc" or v != "")

            dict_filter: Callable[[dict], dict] = lambda x: {k: v for k, v in x.items() if _concise_predicate((k, v))}
        d = {"__version__": Context.VERSION, **self.asdict(dict_filter)}
        json.dump(d, fp, indent=4, sort_keys=True)

    @staticmethod
    def reconstruct(d: dict):
        return Context(sources=d["sources"], headers=d["headers"], module=Module.reconstruct(d["module"]))

    def asdict(self, dict_filter):
        d = {"sources": self.sources, "headers": self.headers, "module": self.module.asdict(dict_filter)}
        assert len(d) == len(fields(self))  # Ensure no left-out
        return dict_filter(d)

    def refresh(self):
        return Context.reconstruct(self.asdict())
