#pragma once
#include <array>
#include <algorithm>
#include <optional>
#include <fmt/core.h>
#include <fmt/ranges.h>
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <pybind11/operators.h>
using namespace pybind11::literals;

namespace slxpy::env::space
{
    // NOTE: Gym-like, but sampling not implemented
    // This is deprecated, but kept for reference
    // Use slxpy::env::gym_space instead

    class Discrete
    {
    public:
        using value_type = size_t;
        size_t n;
    public:
        Discrete(size_t n): n(n) {}
        bool contains(size_t x) {
            return x < n;
        }
        std::string repr() {
            return fmt::format("Discrete({})", n);
        }
    };
    bool operator==(const Discrete& lhs, const Discrete& rhs){
        return lhs.n == rhs.n;
    }

    class MultiDiscrete
    {
    public:
        using value_type = size_t;
        using container_type = std::vector<size_t>;
        container_type nvec;
    public:
        MultiDiscrete(container_type nvec): nvec(nvec) {}
        bool contains(container_type x) {
            if (x.size() != nvec.size()) {
                return false;
            }
            for (size_t i = 0; i < nvec.size(); i++)
            {
                if (x[i] >= nvec[i]) {
                    return false;
                }
            }
            return true;
        }
        std::string repr() {
            return fmt::format("MultiDiscrete({})", nvec);
        }
    };
    bool operator==(const MultiDiscrete& lhs, const MultiDiscrete& rhs){
        return lhs.nvec.size() == rhs.nvec.size() &&
            std::equal(lhs.nvec.begin(), lhs.nvec.end(), rhs.nvec.begin());
    }

    class MultiBinary
    {
    public:
        using value_type = bool;
        using container_type = std::vector<size_t>;
        size_t n;
    public:
        MultiBinary(size_t n): n(n) {}
        bool contains(container_type x) {
            if (x.size() != n) {
                return false;
            }
            for (size_t i = 0; i < n; i++)
            {
                if (x[i] >= 2) {
                    return false;
                }
            }
            return true;
        }
        std::string repr() {
            return fmt::format("MultiBinary({})", n);
        }
        bool operator==(const MultiBinary& other){
            return n == other.n;
        }
    };
    bool operator==(const MultiBinary& lhs, const MultiBinary& rhs){
        return lhs.n == rhs.n;
    }

    template <typename T>
    class Box
    {
    public:
        using value_type = T;
        using shape_type = std::vector<size_t>;
        using container_type = std::vector<T>;
        container_type low;
        container_type high;
        shape_type shape;
        size_t size;
    private:
        static size_t get_size(const shape_type& shape) {
            return std::accumulate(shape.begin(), shape.end(), 1ULL, std::multiplies<size_t>());
        }
        static container_type full(T value, const shape_type& shape) {
            return container_type(get_size(shape), value);
        }
    public:
        Box(T low, T high, shape_type shape): Box(full(low, shape), full(high, shape), shape) {}
        Box(container_type low, T high, shape_type shape): Box(low, full(high, shape), shape) {}
        Box(T low, container_type high, shape_type shape): Box(full(low, shape), high, shape) {}
        Box(container_type low, container_type high, shape_type shape): low(low), high(high), shape(shape) {
            size = get_size(shape);
            if (low.size() != size || high.size() != size) {
                throw std::runtime_error("Shape mismatch");
            }
        }

        bool contains(T* x/* , size_t length */) {
            // if (length != size) {
            //     return false;
            // }
            for (size_t i = 0; i < size; i++)
            {
                if (x[i] < low[i] || x[i] > high[i]) {
                    return false;
                }
            }
            return true;
        }
        std::string repr() {
            T min = *std::min_element(low.begin(), low.end());
            T max = *std::max_element(high.begin(), high.end());
            return fmt::format("Box({}, {}, {})", min, max, shape);
        }
    };
    template <typename T>
    bool operator==(const Box<T>& lhs, const Box<T>& rhs){
            return std::equal(lhs.shape.begin(), lhs.shape.end(), rhs.shape.begin()) &&
                std::equal(lhs.low.begin(), lhs.low.end(), rhs.low.begin()) &&
                std::equal(lhs.high.begin(), lhs.high.end(), rhs.high.begin());
    }

    void slxpy_bind_space(::pybind11::module_& s) {
        pybind11::class_<Discrete> Discrete_PB(s, "Discrete", pybind11::module_local());
        Discrete_PB
            .def_readonly("n", &Discrete::n)
            .def("contains", &Discrete::contains)
            .def("__contains__", &Discrete::contains)
            .def("__repr__", &Discrete::repr)
            .def(pybind11::self == pybind11::self)
            .def(pybind11::pickle(
                [](const Discrete& self) { return pybind11::make_tuple(self.n); },
                [](pybind11::tuple t) {
                    if (t.size() != 1) throw std::runtime_error("Invalid state!");
                    return Discrete(t[0].cast<size_t>());
                }
            ));
        Discrete_PB.attr("dtype") = pybind11::dtype::of<Discrete::value_type>();

        pybind11::class_<MultiDiscrete> MultiDiscrete_PB(s, "MultiDiscrete", pybind11::module_local());
        MultiDiscrete_PB
            .def_readonly("nvec", &MultiDiscrete::nvec)
            .def("contains", &MultiDiscrete::contains)
            .def("__contains__", &MultiDiscrete::contains)
            .def("__repr__", &MultiDiscrete::repr)
            .def(pybind11::self == pybind11::self)
            .def(pybind11::pickle(
                [](const MultiDiscrete& self) { return pybind11::make_tuple(self.nvec); },
                [](pybind11::tuple t) {
                    if (t.size() != 1) throw std::runtime_error("Invalid state!");
                    return MultiDiscrete(t[0].cast<typename MultiDiscrete::container_type>());
                }
            ));
        MultiDiscrete_PB.attr("dtype") = pybind11::dtype::of<MultiDiscrete::value_type>();

        pybind11::class_<MultiBinary> MultiBinary_PB(s, "MultiBinary", pybind11::module_local());
        MultiBinary_PB
            .def_readonly("n", &MultiBinary::n)
            .def("contains", &MultiBinary::contains)
            .def("__contains__", &MultiBinary::contains)
            .def("__repr__", &MultiBinary::repr)
            .def(pybind11::self == pybind11::self)
            .def(pybind11::pickle(
                [](const MultiBinary& self) { return pybind11::make_tuple(self.n); },
                [](pybind11::tuple t) {
                    if (t.size() != 1) throw std::runtime_error("Invalid state!");
                    return MultiBinary(t[0].cast<size_t>());
                }
            ));
        MultiBinary_PB.attr("dtype") = pybind11::dtype::of<MultiBinary::value_type>();
    }

    template <typename T>
    constexpr const char* slxpy_get_box_typename() {
        #define Compare(Tx, Nx) if constexpr (std::is_same_v<T, Tx>) { return #Nx; }
        Compare(uint8_t , BoxUint8  )
        Compare(int8_t  , BoxInt8   )
        Compare(uint16_t, BoxUint16 )
        Compare(int16_t , BoxInt16  )
        Compare(uint32_t, BoxUint32 )
        Compare(int32_t , BoxInt32  )
        Compare(uint64_t, BoxUint64 )
        Compare(int64_t , BoxInt64  )
        Compare(float   , BoxFloat32)
        Compare(double  , BoxFloat64)
        #undef Compare
    }

    template <typename T>
    void slxpy_bind_space_box(::pybind11::module_& s) {
        using Box = slxpy::env::space::Box<T>;
        using npa = pybind11::array_t<T, pybind11::array::c_style | pybind11::array::forcecast>;

        pybind11::class_<Box> Box_PB(s, slxpy_get_box_typename<T>(), pybind11::module_local());
        auto contains = [](Box& self, npa array) {
            if (static_cast<size_t>(array.ndim()) != self.shape.size()) {
                return false;
            }
            if (!std::equal(self.shape.begin(), self.shape.end(), array.shape())) {
                return false;
            }
            T* ptr = static_cast<T*>(array.request(false).ptr);
            return self.contains(ptr);
        };
        Box_PB
            .def_property_readonly("shape", [] (Box& self) {
                return pybind11::tuple(pybind11::cast(self.shape));
            })
            .def_property_readonly("low", [] (pybind11::object& obj) {
                Box& self = obj.cast<Box&>();
                npa arr { self.shape, {}, self.low.data(), obj};
                reinterpret_cast<pybind11::detail::PyArray_Proxy*>(arr.ptr())->flags &= ~pybind11::detail::npy_api::NPY_ARRAY_WRITEABLE_;
                return arr;
            })
            .def_property_readonly("high", [] (pybind11::object& obj) {
                Box& self = obj.cast<Box&>();
                npa arr { self.shape, {}, self.high.data(), obj};
                reinterpret_cast<pybind11::detail::PyArray_Proxy*>(arr.ptr())->flags &= ~pybind11::detail::npy_api::NPY_ARRAY_WRITEABLE_;
                return arr;
            })
            .def("contains", contains)
            .def("__contains__", contains)
            .def("__repr__", &Box::repr)
            .def(pybind11::self == pybind11::self)
            .def(pybind11::pickle(
                [](const Box& self) { return pybind11::make_tuple(self.low, self.high, self.shape); },
                [](pybind11::tuple t) {
                    if (t.size() != 3) throw std::runtime_error("Invalid state!");
                    return Box(t[0].cast<typename Box::container_type>(), t[1].cast<typename Box::container_type>(), t[2].cast<typename Box::shape_type>());
                }
            ));
        Box_PB.attr("dtype") = pybind11::dtype::of<typename Box::value_type>();
    }
}

namespace slxpy::env::gym_spaces {
    template <typename T = float>
    pybind11::array_t<T, pybind11::array::c_style | pybind11::array::forcecast> _make_owned_array(const std::vector<T>& vec) {
        pybind11::array_t<T, pybind11::array::c_style | pybind11::array::forcecast> array_np { static_cast<pybind11::ssize_t>(vec.size()) };
        T* ptr = static_cast<T*>(array_np.request(true).ptr);
        std::copy(vec.begin(), vec.end(), ptr);
        reinterpret_cast<pybind11::detail::PyArray_Proxy*>(array_np.ptr())->flags &= ~pybind11::detail::npy_api::NPY_ARRAY_WRITEABLE_;
        return array_np;
    }

    template <typename T = float>
    pybind11::array_t<T, pybind11::array::c_style | pybind11::array::forcecast> _make_owned_array(const std::vector<T>& vec, const std::vector<pybind11::ssize_t>& shape) {
        pybind11::ssize_t numel = std::accumulate(shape.begin(), shape.end(), 1LL, std::multiplies<pybind11::ssize_t>());
        if (numel != static_cast<pybind11::ssize_t>(vec.size())) {
            throw std::runtime_error("Invalid shape!");
        }
        pybind11::array_t<T, pybind11::array::c_style | pybind11::array::forcecast> array_np { shape };
        T* ptr = static_cast<T*>(array_np.request(true).ptr);
        std::copy(vec.begin(), vec.end(), ptr);
        reinterpret_cast<pybind11::detail::PyArray_Proxy*>(array_np.ptr())->flags &= ~pybind11::detail::npy_api::NPY_ARRAY_WRITEABLE_;
        return array_np;
    }

    template <typename T = float>
    pybind11::object make_box(T low, T high, const std::vector<pybind11::ssize_t>& shape) {
        auto gym_spaces = pybind11::module::import("gymnasium.spaces");
        auto BoxClass = gym_spaces.attr("Box");
        pybind11::tuple shape_tuple = pybind11::cast(shape);
        auto dtype = pybind11::dtype::of<T>();
        return BoxClass(low, high, shape_tuple, dtype);
    }

    template <typename T = float>
    pybind11::object make_box(const std::vector<T>& low, const std::vector<T>& high) {
        if (low.size() != high.size()) {
            throw std::runtime_error("Invalid shape!");
        }
        auto gym_spaces = pybind11::module::import("gymnasium.spaces");
        auto BoxClass = gym_spaces.attr("Box");
        auto low_np = _make_owned_array(low);
        auto high_np = _make_owned_array(high);
        auto shape = pybind11::make_tuple(low.size());
        auto dtype = pybind11::dtype::of<T>();
        return BoxClass(low_np, high_np, shape, dtype);
    }

    template <typename T = float>
    pybind11::object make_box(const std::vector<T>& low, const std::vector<T>& high, const std::vector<pybind11::ssize_t>& shape) {
        if (low.size() != high.size()) {
            throw std::runtime_error("Invalid shape!");
        }
        auto gym_spaces = pybind11::module::import("gymnasium.spaces");
        auto BoxClass = gym_spaces.attr("Box");
        auto low_np = _make_owned_array(low, shape);
        auto high_np = _make_owned_array(high, shape);
        auto dtype = pybind11::dtype::of<T>();
        return BoxClass(low_np, high_np, shape, dtype);
    }

    pybind11::object make_discrete(pybind11::ssize_t n) {
        auto gym_spaces = pybind11::module::import("gymnasium.spaces");
        auto DiscreteClass = gym_spaces.attr("Discrete");
        return DiscreteClass(n);
    }

    pybind11::object make_multi_discrete(const std::vector<pybind11::ssize_t>& nvec) {
        auto gym_spaces = pybind11::module::import("gymnasium.spaces");
        auto MultiDiscreteClass = gym_spaces.attr("MultiDiscrete");
        auto nvec_np = _make_owned_array(nvec);
        return MultiDiscreteClass(nvec_np);
    }

    pybind11::object make_multi_binary(pybind11::ssize_t n) {
        auto gym_spaces = pybind11::module::import("gymnasium.spaces");
        auto MultiBinaryClass = gym_spaces.attr("MultiBinary");
        return MultiBinaryClass(n);
    }

    pybind11::object make_multi_binary(const std::vector<pybind11::ssize_t>& shape) {
        auto gym_spaces = pybind11::module::import("gymnasium.spaces");
        auto MultiBinaryClass = gym_spaces.attr("MultiBinary");
        auto shape_np = _make_owned_array(shape);
        return MultiBinaryClass(shape);
    }
}

// Better location for this?
template <typename T>
struct fmt::formatter<std::optional<T>>: fmt::formatter<T> {
    template <typename FormatContext>
    auto format(const std::optional<T>& p, FormatContext& ctx) -> decltype(ctx.out()) {
        if (p) {
            return fmt::formatter<T>::format(*p, ctx);
        } else {
            return format_to(ctx.out(), "<None>");
        }
    }
};

namespace slxpy::env::spec {
    enum class IndexingMode: uint8_t {
        PRESERVE_EMPTY = 0,
        PRESERVE_FILL,
        COMPRESS
    };
    enum class ActionRepeatMode: uint8_t {
        // Reward_Done
        SUM_BREAK = 0
    };
    static const char* IndexingModeNames[] = {
        "PRESERVE_EMPTY",
        "PRESERVE_FILL",
        "COMPRESS"
    };
    static const char* ActionRepeatModeNames[] = {
        "SUM_BREAK"
    };
    class EnvSpec
    {
    public:
        std::string id;
        std::optional<double> reward_threshold;
        std::optional<size_t> max_episode_steps;
        IndexingMode indexing_mode = IndexingMode::PRESERVE_EMPTY;
        bool nondeterministic = false;
        bool auto_reset = false;
        bool strict_reset = true;
        bool need_render = false; // here?
        size_t action_repeat = 0;
        ActionRepeatMode action_repeat_mode = ActionRepeatMode::SUM_BREAK;
        pybind11::dict kwargs;
    public:
        std::string repr() {
            return fmt::format(R"--(EnvSpec(
    id={},
    reward_threshold={},
    max_episode_steps={},
    indexing_mode=<IndexingMode.{}>,
    nondeterministic={},
    auto_reset={},
    strict_reset={},
    need_render={},
    action_repeat={},
    action_repeat_mode=<ActionRepeatMode.{}>,
    kwargs={}
))--", id, reward_threshold, max_episode_steps, IndexingModeNames[static_cast<uint8_t>(indexing_mode)], nondeterministic, auto_reset, strict_reset, need_render, action_repeat, ActionRepeatModeNames[static_cast<uint8_t>(action_repeat_mode)], std::string(pybind11::repr(kwargs)));
        }
    };

    void slxpy_bind_spec(::pybind11::module_& s) {
        pybind11::enum_<IndexingMode> IndexingMode_PB(s, "IndexingMode", pybind11::module_local());
        IndexingMode_PB
            .value("PRESERVE_EMPTY", IndexingMode::PRESERVE_EMPTY)
            .value("PRESERVE_FILL", IndexingMode::PRESERVE_FILL)
            .value("COMPRESS", IndexingMode::COMPRESS);

        pybind11::enum_<ActionRepeatMode> ActionRepeatMode_PB(s, "ActionRepeatMode", pybind11::module_local());
        ActionRepeatMode_PB
            .value("SUM_BREAK", ActionRepeatMode::SUM_BREAK);

        pybind11::class_<EnvSpec> EnvSpec_PB(s, "EnvSpec", pybind11::module_local());
        EnvSpec_PB
            .def(pybind11::init([] (
                    std::string id,
                    std::optional<double> reward_threshold,
                    std::optional<size_t> max_episode_steps,
                    IndexingMode indexing_mode,
                    bool nondeterministic,
                    bool auto_reset,
                    bool strict_reset,
                    bool need_render,
                    size_t action_repeat,
                    ActionRepeatMode action_repeat_mode,
                    pybind11::kwargs kwargs
                ) -> EnvSpec {
                    if (id.size() == 0) {
                        // Check against /^(?:[\w:-]+\/)?([\w:.-]+)-v(\d+)$/ ?
                        throw std::runtime_error("Empty string is not allowed!");
                    }
                    return {
                        id,
                        reward_threshold,
                        max_episode_steps,
                        indexing_mode,
                        nondeterministic,
                        auto_reset,
                        strict_reset,
                        need_render,
                        action_repeat,
                        action_repeat_mode,
                        kwargs
                    };
                }),
                "id"_a, "reward_threshold"_a=std::nullopt, "max_episode_steps"_a=std::nullopt,
                "indexing_mode"_a=IndexingMode::PRESERVE_EMPTY,
                "nondeterministic"_a=false, "auto_reset"_a=false, "strict_reset"_a=true, "need_render"_a=false,
                "action_repeat"_a=0, "action_repeat_mode"_a=ActionRepeatMode::SUM_BREAK
            )
            .def_readonly("id", &EnvSpec::id)
            .def_readonly("reward_threshold", &EnvSpec::reward_threshold)
            .def_readonly("max_episode_steps", &EnvSpec::max_episode_steps)
            .def_readonly("indexing_mode", &EnvSpec::indexing_mode)
            .def_readonly("nondeterministic", &EnvSpec::nondeterministic)
            .def_readonly("auto_reset", &EnvSpec::auto_reset)
            .def_readonly("strict_reset", &EnvSpec::strict_reset)
            .def_readonly("need_render", &EnvSpec::need_render)
            .def_readonly("action_repeat", &EnvSpec::action_repeat)
            .def_readonly("action_repeat_mode", &EnvSpec::action_repeat_mode)
            .def_readonly("kwargs", &EnvSpec::kwargs)
            .def("__repr__", &EnvSpec::repr);
    }
}

using slxpy::env::spec::slxpy_bind_spec;
