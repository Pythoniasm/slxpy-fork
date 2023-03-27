#pragma once

#include <algorithm>
#include "common.h"

template <typename S, typename T>
void copy_n_with_coercion(const S* src, size_t n, T* dst) {
    if constexpr (std::is_same_v<S, T>) {
        std::copy_n(src, n, dst);
    } else {
        // STATIC_WARNING(false, "Type coercion happens here.");
        for (size_t i = 0; i < n; ++i) {
            dst[i] = static_cast<T>(src[i]);
        }
    }
}
