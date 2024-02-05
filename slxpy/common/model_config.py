from dataclasses import dataclass
from typing import BinaryIO, ClassVar, Literal

import tomli

import slxpy.common.constants as C


@dataclass
class SimulinkConfig:
    solver: Literal["FixedStepAuto", "FixedStepDiscrete", "ode8", "ode5", "ode4", "ode3", "ode2", "ode1", "ode14x"] = (
        "FixedStepAuto"
    )
    absolute_time: bool = False
    integer_code: bool = False
    non_finite: bool = False
    complex: bool = False
    continuous_time: bool = False
    variable_size_signal: bool = False
    non_inlined_sfcn: bool = False

    @staticmethod
    def reconstruct(d: dict):
        return SimulinkConfig(
            solver=d["solver"],
            absolute_time=d["absolute_time"],
            integer_code=d["integer_code"],
            non_finite=d["non_finite"],
            complex=d["complex"],
            continuous_time=d["continuous_time"],
            variable_size_signal=d["variable_size_signal"],
            non_inlined_sfcn=d["non_inlined_sfcn"],
        )


@dataclass
class CppConfig:
    class_name: str
    namespace: str

    @staticmethod
    def reconstruct(d: dict):
        return CppConfig(class_name=d["class_name"], namespace=d["namespace"])


@dataclass
class InfoConfig:
    AUTO: ClassVar[str] = "<auto>"
    NO_LICENSE: ClassVar[str] = "<no-license>"
    description: str = AUTO
    version: str = AUTO
    author: str = AUTO
    license: str = NO_LICENSE

    @staticmethod
    def reconstruct(d: dict):
        return InfoConfig(description=d["description"], version=d["version"], author=d["author"], license=d["license"])


@dataclass
class Config:
    model: str
    simulink: SimulinkConfig
    cpp: CppConfig
    info: InfoConfig
    VERSION: ClassVar[str] = C.metadata_version

    @staticmethod
    def reconstruct(d: dict):
        return Config(
            model=d["model"],
            simulink=SimulinkConfig.reconstruct(d["simulink"]),
            cpp=CppConfig.reconstruct(d["cpp"]),
            info=InfoConfig.reconstruct(d["info"]),
        )

    @staticmethod
    def load(fp: BinaryIO):
        cfg = tomli.load(fp)
        assert cfg["__version__"] == Config.VERSION
        return Config.reconstruct(cfg)

    @staticmethod
    def default(model: str, class_name: str, namespace: str):
        return Config(
            model=model,
            simulink=SimulinkConfig(),
            cpp=CppConfig(class_name=class_name, namespace=namespace),
            info=InfoConfig(),
        )
