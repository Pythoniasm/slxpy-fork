#pragma once
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include "rtwtypes.h"

// TODO: better complex support with is_complex, format_descriptor and is_fmt_numeric
// TODO: avoid macro with partial specialization?

namespace pybind11::detail {
    #define BIND_COMPLEX(T, V)                                                              \
    template <> struct type_caster<T> {                                                     \
    public:                                                                                 \
        PYBIND11_TYPE_CASTER(T, _("complex"));                                              \
        bool load(handle src, bool convert) {                                               \
            if (!src)                                                                       \
                return false;                                                               \
            if (!convert && !PyComplex_Check(src.ptr()))                                    \
                return false;                                                               \
            Py_complex result = PyComplex_AsCComplex(src.ptr());                            \
            if (result.real == -1.0 && PyErr_Occurred()) {                                  \
                PyErr_Clear();                                                              \
                return false;                                                               \
            }                                                                               \
            value = T{(V)result.real, (V)result.imag};                                      \
            return true;                                                                    \
        }                                                                                   \
        static handle cast(T src, return_value_policy /* policy */, handle /* parent */) {  \
            return PyComplex_FromDoubles((double)src.re, (double)src.im);                   \
        }                                                                                   \
    };

    #ifdef CREAL_T
        BIND_COMPLEX(creal32_T, real32_T)
        BIND_COMPLEX(creal64_T, real64_T)
        BIND_COMPLEX(creal_T  , real_T  )
    #endif
    #ifdef CINT8_T
        BIND_COMPLEX(cint8_T  , int8_T  )
    #endif
    #ifdef CUINT8_T
        BIND_COMPLEX(cuint8_T , uint8_T )
    #endif
    #ifdef CINT16_T
        BIND_COMPLEX(cint16_T , int16_T )
    #endif
    #ifdef CUINT16_T
        BIND_COMPLEX(cuint16_T, uint16_T)
    #endif
    #ifdef CINT32_T
        BIND_COMPLEX(cint32_T , int32_T )
    #endif
    #ifdef CUINT32_T
        BIND_COMPLEX(cuint32_T, uint32_T)
    #endif
    #ifdef CINT64_T
        BIND_COMPLEX(cint64_T , int64_T )
    #endif
    #ifdef CUINT64_T
        BIND_COMPLEX(cuint64_T, uint64_t)
    #endif
    #undef BIND_COMPLEX
}

void slxpy_init_complex() {
    #ifdef CREAL_T
        PYBIND11_NUMPY_DTYPE(creal32_T, re, im);
        PYBIND11_NUMPY_DTYPE(creal64_T, re, im);
        PYBIND11_NUMPY_DTYPE(creal_T  , re, im);
    #endif
    #ifdef CINT8_T
        PYBIND11_NUMPY_DTYPE(cint8_T  , re, im);
    #endif
    #ifdef CUINT8_T
        PYBIND11_NUMPY_DTYPE(cuint8_T , re, im);
    #endif
    #ifdef CINT16_T
        PYBIND11_NUMPY_DTYPE(cint16_T , re, im);
    #endif
    #ifdef CUINT16_T
        PYBIND11_NUMPY_DTYPE(cuint16_T, re, im);
    #endif
    #ifdef CINT32_T
        PYBIND11_NUMPY_DTYPE(cint32_T , re, im);
    #endif
    #ifdef CUINT32_T
        PYBIND11_NUMPY_DTYPE(cuint32_T, re, im);
    #endif
    #ifdef CINT64_T
        PYBIND11_NUMPY_DTYPE(cint64_T , re, im);
    #endif
    #ifdef CUINT64_T
        PYBIND11_NUMPY_DTYPE(cuint64_T, re, im);
    #endif
}

#ifdef USE_SLXPY_JSON
    #include <nlohmann/json.hpp>
    #ifdef CREAL_T
        NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(creal32_T, re, im)
        NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(creal64_T, re, im)
        NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(creal_T  , re, im)
    #endif
    #ifdef CINT8_T
        NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(cint8_T  , re, im)
    #endif
    #ifdef CUINT8_T
        NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(cuint8_T , re, im)
    #endif
    #ifdef CINT16_T
        NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(cint16_T , re, im)
    #endif
    #ifdef CUINT16_T
        NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(cuint16_T, re, im)
    #endif
    #ifdef CINT32_T
        NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(cint32_T , re, im)
    #endif
    #ifdef CUINT32_T
        NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(cuint32_T, re, im)
    #endif
    #ifdef CINT64_T
        NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(cint64_T , re, im)
    #endif
    #ifdef CUINT64_T
        NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(cuint64_T, re, im)
    #endif
#endif

#ifdef USE_FMT
    #include<fmt/core.h>

    #define FMT_FORMATTER_COMPLEX(T)                                                \
    template <> struct fmt::formatter<T> {                                          \
        constexpr auto parse(format_parse_context& ctx) -> decltype(ctx.begin()) {  \
            return ctx.begin();                                                     \
        }                                                                           \
        template <typename FormatContext>                                           \
        auto format(const T& p, FormatContext& ctx) -> decltype(ctx.out()) {        \
            return format_to(ctx.out(), "({}+{}j)", p.re, p.im);                    \
        }                                                                           \
    };
    #ifdef CREAL_T
        FMT_FORMATTER_COMPLEX(creal32_T)
        FMT_FORMATTER_COMPLEX(creal64_T)
        FMT_FORMATTER_COMPLEX(creal_T  )
    #endif
    #ifdef CINT8_T
        FMT_FORMATTER_COMPLEX(cint8_T  )
    #endif
    #ifdef CUINT8_T
        FMT_FORMATTER_COMPLEX(cuint8_T )
    #endif
    #ifdef CINT16_T
        FMT_FORMATTER_COMPLEX(cint16_T )
    #endif
    #ifdef CUINT16_T
        FMT_FORMATTER_COMPLEX(cuint16_T)
    #endif
    #ifdef CINT32_T
        FMT_FORMATTER_COMPLEX(cint32_T )
    #endif
    #ifdef CUINT32_T
        FMT_FORMATTER_COMPLEX(cuint32_T)
    #endif
    #ifdef CINT64_T
        FMT_FORMATTER_COMPLEX(cint64_T )
    #endif
    #ifdef CUINT64_T
        FMT_FORMATTER_COMPLEX(cuint64_T)
    #endif
#endif
