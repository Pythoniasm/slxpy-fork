import collections.abc
import numbers

import numpy as np

from slxpy.common.mapping import dtype_mapping, suffix_mapping


def is_nonstr_sequence(x):
    """Check if x is a sequence, but not a string."""
    return isinstance(x, collections.abc.Sequence) and not isinstance(x, str)


def format_integer(x, dtype: np.dtype):
    iinfo = np.iinfo(dtype)
    if iinfo.min <= x <= iinfo.max:
        return str(x)
    else:
        raise ValueError(f"Integer value {x} out of range for dtype {dtype}")


def format_float(x, dtype: np.dtype):
    ctype = dtype_mapping[dtype.name]
    special = {
        "inf": f"std::numeric_limits<{ctype}>::infinity()",
        "-inf": f"-std::numeric_limits<{ctype}>::infinity()",
    }
    if isinstance(x, str):
        return special[x]
    else:
        suffix = suffix_mapping[dtype.name]
        return f"{x}{suffix}"


def format_number(x, dtype: np.dtype):
    if issubclass(dtype.type, numbers.Integral):
        return format_integer(x, dtype)
    elif issubclass(dtype.type, numbers.Real):
        return format_float(x, dtype)
    else:
        raise ValueError(f"Unexpected dtype: {dtype}")


def format_sequence(x, dtype: np.dtype):
    return f"{{ {', '.join(format_number(y, dtype) for y in x)} }}"


def format_sequence_or_scalar(x, dtype: np.dtype):
    return format_sequence(x, dtype) if is_nonstr_sequence(x) else format_number(x, dtype)
