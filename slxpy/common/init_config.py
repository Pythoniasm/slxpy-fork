from dataclasses import dataclass, fields
from typing import TYPE_CHECKING, ClassVar, Dict, List, Literal, Type, Union

import numpy as np

from slxpy.common.enum import FieldMode

if TYPE_CHECKING:
    from slxpy.common.context import Field


def check_shape(array_like, shape: List[int]):
    size = np.prod(shape).item()
    array = np.array(array_like)
    if array.size != 1:
        assert array.ndim == 1, "Currently only support one dimensional vector."
        assert array.size == size, "Size inconsistency, broadcast is currently unsupported."


@dataclass
class InitConfig:
    type: Literal["seed", "constant", "uniform", "custom"]

    init_name: ClassVar[str] = ""
    mapping: ClassVar[Dict[str, Type["InitConfig"]]] = {}

    def __init_subclass__(cls):
        InitConfig.mapping[cls.init_name] = cls

    @staticmethod
    def reconstruct(d: dict):
        type = d["type"]
        cls = InitConfig.mapping[type]
        if len(fields(cls)) > 1:
            return cls.reconstruct(d)
        else:
            return cls(type=type)

    def asdict(self, dict_filter):
        d = {"type": self.type}
        assert len(d) == len(fields(self))  # Ensure no left-out
        return dict_filter(d)

    @staticmethod
    def unique(inits: List["InitConfig"]):
        return list(set(type(init) for init in inits))

    def check_basic_compatibility(self, field: "Field"):
        if field.mode in (FieldMode.STRUCT, FieldMode.STRUCT_ARRAY):
            raise ValueError('For struct parameters, use "custom" type initialization.')


@dataclass
class SeedInitConfig(InitConfig):
    init_name: ClassVar[str] = "seed"


@dataclass
class ConstantInitConfig(InitConfig):
    value: Union[float, str]
    init_name: ClassVar[str] = "constant"

    @staticmethod
    def reconstruct(d: dict):
        return ConstantInitConfig(type=d["type"], value=d["value"])

    def asdict(self, dict_filter):
        d = {"type": self.type, "value": self.value}
        assert len(d) == len(fields(self))  # Ensure no left-out
        return dict_filter(d)


@dataclass
class UniformInitConfig(InitConfig):
    low: Union[float, List[float]]
    high: Union[float, List[float]]
    init_name: ClassVar[str] = "uniform"

    @staticmethod
    def reconstruct(d: dict):
        return UniformInitConfig(type=d["type"], low=d["low"], high=d["high"])

    def asdict(self, dict_filter):
        d = {"type": self.type, "low": self.low, "high": self.high}
        assert len(d) == len(fields(self))  # Ensure no left-out
        return dict_filter(d)

    def check_basic_compatibility(self, field: "Field"):
        super().check_basic_compatibility(field)
        low, high = self.low, self.high
        if field.mode == FieldMode.PLAIN_ARRAY:
            check_shape(low, field.shape)
            check_shape(high, field.shape)
        else:
            assert isinstance(low, float) and isinstance(high, float)


@dataclass
class CustomInitConfig(InitConfig):
    code: str
    init_name: ClassVar[str] = "custom"

    @staticmethod
    def reconstruct(d: dict):
        return CustomInitConfig(type=d["type"], code=d["code"])

    def asdict(self, dict_filter):
        d = {"type": self.type, "code": self.code}
        assert len(d) == len(fields(self))  # Ensure no left-out
        return dict_filter(d)
