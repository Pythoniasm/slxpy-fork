simulink_mapping = [
    ("block_signals", "B", "Block signals of the system"),
    # ("external_inputs", "ExtU", "Block input data for root system"),
    # (
    #     "external_input_sizes",
    #     "ExtUSize",
    #     "Size of block input data for the root system "
    #     "(used when inputs are variable dimensions)",
    # ),
    # ("external_outputs", "ExtY", "Block output data for the root system"),
    # (
    #     "external_output_sizes",
    #     "ExtYSize",
    #     "Size of block output data for the root system",
    # ),
    ("external_inputs", "U", "Input data"),
    ("external_input_sizes", "USize", "Size of input data"),
    ("external_outputs", "Y", "Output data"),
    ("external_output_sizes", "YSize", "Size of output data"),
    ("parameters", "P", "Parameters for the system"),
    ("const_block_signals", "ConstB", "Block inputs and outputs that are constants"),
    ("machine_local_data", "MachLocal", "Used by ERT S-function targets"),
    ("const_parameters", "ConstP", "Constant parameters in the system"),
    (
        "const_parameters_with_init",
        "ConstInitP",
        "Initialization data for constant parameters in the system",
    ),
    ("discrete_states", "DW", "Block states in the system"),
    ("mass_matrix", "MassMatrix", "Used for physical modeling blocks"),
    ("zero_crossing_states", "PrevZCX", "Previous zero-crossing signal state"),
    ("continuous_states", "X", "Continuous states"),
    ("disabled_states", "XDis", "Status of an enabled subsystem"),
    ("state_derivatives", "XDot", "Derivatives of continuous states at each time step"),
    ("zero_crossing_signals", "ZCV", "Zero-crossing signals"),
    # ("default_parameters", "DefaultP", "Default parameters in the system"),
    # (
    #     "global_TID",
    #     "GlobalTID",
    #     "Used for sample time for states in referenced models"
    # ),
    # ("invariant_signals", "Invariant", "Invariant signals"),
    # ("n_stages", "NSTAGES", "Solver macro"),
    # (
    #     "object",
    #     "Obj",
    #     "Used by ERT C++ code generation to refer to referenced model objects",
    # ),
    # (
    #     "timing_bridge",
    #     "TimingBrdg",
    #     "Timing information stored in different data structures",
    # ),
    # (
    #     "shared_DSM",
    #     "SharedDSM",
    #     "Shared local data stores, which are Data Store Memory blocks "
    #     "with Share across model instances selected",
    # ),
    ("instance_parameters", "InstP", "Parameter arguments for the system"),
]

dtype_mapping = {
    "uint8": "uint8_t",
    "int8": "int8_t",
    "uint16": "uint16_t",
    "int16": "int16_t",
    "uint32": "uint32_t",
    "int32": "int32_t",
    "uint64": "uint64_t",
    "int64": "int64_t",
    "float32": "float",
    "float64": "double",
}

suffix_mapping = {
    "float32": "F",
    "float64": "",
}
