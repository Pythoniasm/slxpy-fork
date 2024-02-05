from dataclasses import dataclass, fields
from typing import ClassVar, Dict, List, Literal, Tuple, Type, Union

import numpy as np

from slxpy.common.formatter import format_sequence, format_sequence_or_scalar
from slxpy.common.mapping import dtype_mapping


@dataclass
class SpaceConfig:
    type: Literal["Box", "Discrete", "MultiDiscrete", "MultiBinary"]

    init_name: ClassVar[str] = ""
    mapping: ClassVar[Dict[str, Type["SpaceConfig"]]] = {}

    def __init_subclass__(cls):
        SpaceConfig.mapping[cls.init_name] = cls

    @staticmethod
    def reconstruct(d: dict):
        type = d["type"]
        cls = SpaceConfig.mapping[type]
        return cls.reconstruct(d)

    def asdict(self, dict_filter):
        d = {"type": self.type}
        assert len(d) == len(fields(self))  # Ensure no left-out
        return dict_filter(d)

    @staticmethod
    def unique(inits: List["SpaceConfig"]):
        return list(set(type(init) for init in inits))

    @staticmethod
    def default():
        return BoxSpaceConfig("Box", 0.0, 1.0, (2, 2), np.dtype("float64"))


@dataclass
class BoxSpaceConfig(SpaceConfig):
    low: Union[List[float], float]
    high: Union[List[float], float]
    shape: Tuple[int, ...]
    dtype: np.dtype
    init_name: ClassVar[str] = "Box"

    @staticmethod
    def reconstruct(d: dict):
        return BoxSpaceConfig(
            type=d["type"], low=d["low"], high=d["high"], shape=tuple(d["shape"]), dtype=np.dtype(d["dtype"])
        )

    def asdict(self, dict_filter):
        d = {"type": self.type, "low": self.low, "high": self.high, "shape": self.shape, "dtype": self.dtype.name}
        assert len(d) == len(fields(self))  # Ensure no left-out
        return dict_filter(d)

    @property
    def ctype(self):
        return dtype_mapping[self.dtype.name]

    @property
    def initializer(self):
        return f"{format_sequence_or_scalar(self.low, self.dtype)}, {format_sequence_or_scalar(self.high, self.dtype)}, {format_sequence(self.shape, np.dtype(np.int64))}"

    @property
    def func(self):
        return f"make_box<{dtype_mapping[self.dtype.name]}>"


@dataclass
class DiscreteSpaceConfig(SpaceConfig):
    n: int
    init_name: ClassVar[str] = "Discrete"
    func: ClassVar[str] = "make_discrete"
    ctype: ClassVar[str] = "int64_t"

    @staticmethod
    def reconstruct(d: dict):
        return DiscreteSpaceConfig(type=d["type"], n=d["n"])

    def asdict(self, dict_filter):
        d = {"type": self.type, "n": self.n}
        assert len(d) == len(fields(self))  # Ensure no left-out
        return dict_filter(d)

    @property
    def initializer(self):
        return f"{self.n}"


@dataclass
class MultiDiscreteSpaceConfig(SpaceConfig):
    nvec: List[int]
    init_name: ClassVar[str] = "MultiDiscrete"
    func: ClassVar[str] = "make_multi_discrete"
    ctype: ClassVar[str] = "int64_t"

    @staticmethod
    def reconstruct(d: dict):
        return MultiDiscreteSpaceConfig(type=d["type"], nvec=d["nvec"])

    def asdict(self, dict_filter):
        d = {"type": self.type, "nvec": self.nvec}
        assert len(d) == len(fields(self))  # Ensure no left-out
        return dict_filter(d)

    @property
    def initializer(self):
        return format_sequence(self.nvec)


@dataclass
class MultiBinarySpaceConfig(SpaceConfig):
    n: int
    init_name: ClassVar[str] = "MultiBinary"
    func: ClassVar[str] = "make_multi_binary"
    ctype: ClassVar[str] = "int8_t"

    @staticmethod
    def reconstruct(d: dict):
        return MultiBinarySpaceConfig(type=d["type"], n=d["n"])

    def asdict(self, dict_filter):
        d = {"type": self.type, "n": self.n}
        assert len(d) == len(fields(self))  # Ensure no left-out
        return dict_filter(d)

    @property
    def initializer(self):
        return f"{self.n}"
