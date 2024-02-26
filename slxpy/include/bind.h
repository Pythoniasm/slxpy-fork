#pragma once
#include <array>
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

#include "common.h"

template<typename MemberType, size_t Rank, std::size_t... Is>
constexpr std::array<pybind11::ssize_t, Rank> get_all_extents(std::index_sequence<Is...>) {
    return { std::extent_v<MemberType, Is>... };
}
template <typename Class, typename MemberType, MemberType Class::* M, bool readonly, size_t... Shape>
void slxpy_bind_array_field_with_shape(pybind11::class_<Class>& pb, const char *name, const char *doc) {
    if constexpr (std::is_array_v<MemberType>) {
        using BaseType = std::remove_all_extents_t<MemberType>;
        pb.def_property(name, [](pybind11::object& obj) {
            Class& o = obj.cast<Class&>();
            pybind11::array_t<BaseType> arr { { Shape... }, {}, o.*M, obj};
            if constexpr (readonly) {
                // Credit to https://github.com/pybind/pybind11/issues/481
                reinterpret_cast<pybind11::detail::PyArray_Proxy*>(arr.ptr())->flags &= pybind11::detail::npy_api::NPY_ARRAY_WRITEABLE_;
            }
            return arr;
        },
        [](Class& obj, const pybind11::array_t<BaseType>& value) {
            // Setter logic here
            if (!readonly) {
                // Example: Set the value in obj based on the incoming array
                // Note: You might want to add additional validation or error handling here
                // Access the raw data pointer of the NumPy array
                const BaseType* data = value.data();

                // Perform the actual copy to the C++ array using std::memcpy
                std::memcpy(&(obj.*M), data, sizeof(BaseType) * value.size());
            } else {
                throw std::runtime_error("Trying to set a read-only property.");
            }
        },
        doc);
    } else if constexpr (std::is_class_v<MemberType> && std::is_standard_layout_v<MemberType>) {
        STATIC_WARNING(false, "Mismatch! Show readonly raw buffer instead.");
        pb.def_property_readonly(name, [](pybind11::object& obj) {
            Class& o = obj.cast<Class&>();
            return PyMemoryView_FromMemory(reinterpret_cast<char*>(&(o.*M)), sizeof(MemberType), PyBUF_READ);
        }, doc);
    }
}
template <typename Class, typename MemberType, MemberType Class::* M, bool readonly>
void slxpy_bind_scalar_field(pybind11::class_<Class>& pb, const char *name, const char *doc) {
    static_assert(!std::is_array_v<MemberType>);
    if constexpr (readonly) {
        pb.def_readonly(name, M, doc);
    } else {
        pb.def_readwrite(name, M, doc);
    }
}
template <typename Class, typename Func, Func M>
void slxpy_bind_method(pybind11::class_<Class>& pb, const char *name, const char *doc) {
    // NOTE: Since R2021b, ecoder mark empty methods with static, which breaks binding code.
    // Dev claims:
    //   This change was by design. For MISRA C++ compliance, we need to put the 'static' qualifier on empty class methods.
    // So, handle this with `is_member_function_pointer_v`
    if constexpr (std::is_member_function_pointer_v<Func>) {
        pb.def(name, M, doc);
    } else {
        pb.def_static(name, M, doc);
    }
}
#define BIND_SCALAR_FIELD(PB, T, F, NAME, DOC) slxpy_bind_scalar_field<T, decltype(std::declval<T>().F), &T::F, false>(PB, NAME, DOC)
#define BIND_ARRAY_FIELD(PB, T, F, NAME, DOC, ...) slxpy_bind_array_field_with_shape<T, decltype(std::declval<T>().F), &T::F, false, __VA_ARGS__>(PB, NAME, DOC)
#define BIND_METHOD(PB, T, F, NAME, DOC) slxpy_bind_method<T, decltype(&T::F), &T::F>(PB, NAME, DOC)
