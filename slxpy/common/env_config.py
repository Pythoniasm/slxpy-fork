import textwrap
from dataclasses import dataclass, fields
from typing import TYPE_CHECKING, BinaryIO, ClassVar, Dict, List, Optional, Tuple, Union

import numpy as np
import tomli

import slxpy.common.constants as C
from slxpy.common.formatter import format_float
from slxpy.common.init_config import InitConfig
from slxpy.common.mapping import dtype_mapping
from slxpy.common.space_config import SpaceConfig

if TYPE_CHECKING:
    from slxpy.common.context import Module


@dataclass
class GymConfig:
    action_key: Optional[str]
    observation_key: Optional[str]
    reward_key: Optional[str]
    done_key: Optional[str]
    info: Union[bool, List[str]]

    action_space: SpaceConfig
    observation_space: SpaceConfig
    reward_range: Tuple[Union[float, str], Union[float, str]]
    type_coercion: bool

    @staticmethod
    def reconstruct(d: dict):
        reward_range = tuple(d["reward_range"])
        assert len(reward_range) == 2 and all(
            isinstance(r, (float, str)) for r in reward_range
        ), "reward_range must be a tuple of two floats or +/-inf, not ints"
        return GymConfig(
            action_key=d.get("action_key", None),
            observation_key=d.get("observation_key", None),
            reward_key=d.get("reward_key", None),
            done_key=d.get("done_key", None),
            info=d["info"],
            action_space=SpaceConfig.reconstruct(d["action_space"]),
            observation_space=SpaceConfig.reconstruct(d["observation_space"]),
            reward_range=reward_range,
            type_coercion=d.get("type_coercion", False),
        )

    def asdict(self, dict_filter):
        d = {
            "action_key": self.action_key,
            "observation_key": self.observation_key,
            "reward_key": self.reward_key,
            "done_key": self.done_key,
            "info": self.info,
            "action_space": self.action_space.asdict(dict_filter),
            "observation_space": self.observation_space.asdict(dict_filter),
            "reward_range": self.reward_range,
            "type_coercion": self.type_coercion,
        }
        assert len(d) == len(fields(self))  # Ensure no left-out
        return dict_filter(d)

    @property
    def reward_initializer(self):
        dtype = np.dtype(np.float64)
        return f"{format_float(self.reward_range[0], dtype)}, {format_float(self.reward_range[1], dtype)}"

    @property
    def unique_boxes(self):
        s = set()
        if self.action_space.type == "Box":
            s.add(self.action_space.dtype)
        if self.observation_space.type == "Box":
            s.add(self.observation_space.dtype)
        return [dtype_mapping[x.name] for x in s]

    @staticmethod
    def default():
        return GymConfig(
            None, None, None, None, True, SpaceConfig.default(), SpaceConfig.default(), ("-inf", "inf"), True
        )


@dataclass
class ResetConfig:
    first_step: bool
    input: Optional[str]
    output: Optional[str]

    @staticmethod
    def reconstruct(d: dict):
        first_step = d["first_step"]
        input = d.get("input", None)
        output = d.get("output", None)
        # Consider warn on two conditions below
        if first_step and output is not None:
            output = None
        elif not first_step and input is not None:
            input = None
        return ResetConfig(first_step=d["first_step"], input=input, output=output)

    def asdict(self, dict_filter):
        d = {
            "first_step": self.first_step,
            "input": self.input,
            "output": self.output,
        }
        assert len(d) == len(fields(self))  # Ensure no left-out
        return dict_filter(d)

    @staticmethod
    def default():
        return ResetConfig(True, None, None)


@dataclass
class Config:
    use_raw: bool
    use_gym: bool
    use_rng: bool
    use_vec: bool
    vec_parallel: bool
    gym: Optional[GymConfig]
    reset: Optional[ResetConfig]
    parameter: Dict[str, InitConfig]

    VERSION: ClassVar[str] = C.metadata_version

    @staticmethod
    def reconstruct(d: dict):
        use_gym = d["use_gym"]
        gym_dict = d.get("gym", None)
        # Consider warn on two conditions below
        if use_gym:
            gym_config = GymConfig.default() if gym_dict is None else GymConfig.reconstruct(gym_dict)
        else:
            gym_config = None
        if "reset" in d:
            reset_config = ResetConfig.reconstruct(d["reset"])
        else:
            reset_config = ResetConfig.default()
        parameter_dict = d.get("parameter", {})
        return Config(
            use_raw=d["use_raw"],
            use_gym=use_gym,
            use_rng=d["use_rng"],
            use_vec=d["use_vec"],
            vec_parallel=d["vec_parallel"],
            gym=gym_config,
            reset=reset_config,
            parameter={k: InitConfig.reconstruct(v) for k, v in parameter_dict.items()},
        )

    def asdict(self, dict_filter):
        d = {
            "use_raw": self.use_raw,
            "use_gym": self.use_gym,
            "use_rng": self.use_rng,
            "use_vec": self.use_vec,
            "vec_parallel": self.vec_parallel,
            "gym": self.gym.asdict(dict_filter) if self.use_gym else None,
            "reset": self.reset.asdict(dict_filter),
            "parameter": {k: v.asdict(dict_filter) for k, v in self.parameter.items()},
        }
        assert len(d) == len(fields(self))  # Ensure no left-out
        return dict_filter(d)

    @staticmethod
    def load(fp: BinaryIO):
        cfg = tomli.load(fp)
        assert cfg["__version__"] == Config.VERSION
        return Config.reconstruct(cfg)

    @staticmethod
    def default():
        return Config(
            use_raw=True,
            use_gym=True,
            use_rng=True,
            use_vec=True,
            vec_parallel=False,
            gym=GymConfig.default(),
            reset=ResetConfig.default(),
            parameter={},
        )

    def check_basic_compatibility(self, module: "Module"):
        if not self.use_gym and not self.use_raw:
            return

        # NOTE: The following 3 checks are technically unnecessary
        # But they are here to make sure that the user is aware of
        # correctness of environment configuration.
        # No external input -> Uncontrollable
        # No external output -> Unobservable
        # No parameters -> No randomness, totally deterministic
        #   (even with Simulink Random block, as the seed is fixed)
        if "external_inputs" not in module.model_class.type_mapping:
            raise ValueError("Model must have at least one inport.")
        if "external_outputs" not in module.model_class.type_mapping:
            raise ValueError("Model must have at least one outport.")
        if "instance_parameters" not in module.model_class.type_mapping:
            raise ValueError(
                textwrap.dedent(
                    """
                Model must have at least one parameter.
                Environemt without parameters is most likely a modeling mistake.
                Make sure that your tunable parameters are
                    1. in model workspace
                    2. of Simulink Parameter type
                    3. with Argument checkbox checked
                For more information, see documentation.
                """
                ).strip()
            )

        if self.use_gym:
            # Gym compatibility check
            act_type = module.types.lookup(module.model_class.type_mapping["external_inputs"])
            obs_type = module.types.lookup(module.model_class.type_mapping["external_outputs"])

            assert self.gym.action_key is None or self.gym.action_key in act_type.field_dict
            assert len(obs_type.fields) >= 3
            assert self.gym.observation_key is None or self.gym.observation_key in obs_type.field_dict
            assert self.gym.reward_key is None or self.gym.reward_key in obs_type.field_dict
            assert self.gym.done_key is None or self.gym.done_key in obs_type.field_dict

            if isinstance(self.gym.info, list):
                for s in self.gym.info:
                    assert s in obs_type.field_dict

        param_type = module.types.lookup(module.model_class.type_mapping["instance_parameters"])

        for k, p in self.parameter.items():
            if k.startswith("@"):
                assert p.type == "custom"
            if p.type == "custom":
                continue
            if k not in param_type.field_dict:
                raise KeyError(f"Environment init parameter '{k}' not found in {param_type.name}")
            field = param_type.field_dict[k]
            p.check_basic_compatibility(field)

    def expand_config(self, module: "Module"):
        if self.use_gym:
            act_type = module.types.lookup(module.model_class.type_mapping["external_inputs"])
            obs_type = module.types.lookup(module.model_class.type_mapping["external_outputs"])
            if self.gym.action_key is None:
                self.gym.action_key = act_type.fields[0].name
            if self.gym.observation_key is None:
                self.gym.observation_key = obs_type.fields[0].name
            if self.gym.reward_key is None:
                self.gym.reward_key = obs_type.fields[1].name
            if self.gym.done_key is None:
                self.gym.done_key = obs_type.fields[2].name
            if self.gym.info:
                used_fields = (self.gym.observation_key, self.gym.reward_key, self.gym.done_key)
                self.gym.info = [field.name for field in obs_type.fields if field.name not in used_fields]
            elif not self.gym.info:
                self.gym.info = []
