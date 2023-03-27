#pragma once
// this should be included by module.cc, after include <model>.h
// TODO: refine types, rtw_continuous.h and rtw_solver.h
#include <pybind11/pybind11.h>
using namespace pybind11::literals;

void slxpy_init_simulink(::pybind11::module_ &m) {
    auto sl = m.def_submodule("_sl", "Binding for simulink types, for int values, most have uint8 data type.");

    #define BIND_INT_VALUE(x) sl.attr(#x) = pybind11::int_(x)
    #define BIND_FLOAT_VALUE(x) sl.attr(#x) = pybind11::float_(x)

    #ifdef RTWTYPES_H
        // From rtwtypes.h
    #endif

    #ifdef ZERO_CROSSING_TYPES_H
        // From zero_crossing_types.h
        auto ZCDirection_pb = pybind11::enum_<ZCDirection>(sl, "ZCDirection", "Trigger directions: falling, either, and rising", pybind11::module_local());
        auto ZCEventType_pb = pybind11::enum_<ZCEventType>(sl, "ZCEventType", "Current state of a trigger signal", pybind11::module_local());
        ZCDirection_pb
            .value("FALLING_ZERO_CROSSING", FALLING_ZERO_CROSSING)
            .value("ANY_ZERO_CROSSING", ANY_ZERO_CROSSING)
            .value("RISING_ZERO_CROSSING", RISING_ZERO_CROSSING);
        ZCEventType_pb
            .value("FALLING_ZCEVENT", FALLING_ZCEVENT)
            .value("NO_ZCEVENT", NO_ZCEVENT)
            .value("RISING_ZCEVENT", RISING_ZCEVENT);
        BIND_INT_VALUE(UNINITIALIZED_ZCSIG); // Initial value of a trigger zero crossing signal
        BIND_INT_VALUE(NEG_ZCSIG);
        BIND_INT_VALUE(POS_ZCSIG);
        BIND_INT_VALUE(ZERO_ZCSIG);
    #endif

    #ifdef RTW_CONTINUOUS_H__
        // From rtw_continuous.h
    #endif

    #ifdef RTW_SOLVER_H__
        // From rtw_solver.h
    #endif

    #ifdef RTW_HEADER_rtGetInf_h_
        // From rtGetInf.h
        sl.def("rtGetInf", rtGetInf);
        sl.def("rtGetInfF", rtGetInfF);
        sl.def("rtGetMinusInf", rtGetMinusInf);
        sl.def("rtGetMinusInfF", rtGetMinusInfF);
    #endif

    #ifdef RTW_HEADER_rt_nonfinite_h_
        // From rt_nonfinite.h
        BIND_FLOAT_VALUE(rtInf);
        BIND_FLOAT_VALUE(rtMinusInf);
        BIND_FLOAT_VALUE(rtNaN);
        BIND_FLOAT_VALUE(rtInfF);
        BIND_FLOAT_VALUE(rtMinusInfF);
        BIND_FLOAT_VALUE(rtNaNF);
        sl.def("rt_InitInfAndNaN", rt_InitInfAndNaN, "realSize"_a);
        sl.def("rtIsInf", rtIsInf, "value"_a);
        sl.def("rtIsInfF", rtIsInfF, "value"_a);
        sl.def("rtIsNaN", rtIsNaN, "value"_a);
        sl.def("rtIsNaNF", rtIsNaNF, "value"_a);

        using BigEndianIEEEDouble_words_T = decltype(BigEndianIEEEDouble::words);
        pybind11::class_<BigEndianIEEEDouble> BigEndianIEEEDouble_pb (sl, "BigEndianIEEEDouble", pybind11::module_local());
        pybind11::class_<BigEndianIEEEDouble_words_T> BigEndianIEEEDouble_words_T_pb (BigEndianIEEEDouble_pb, "BigEndianIEEEDouble_words_T", pybind11::module_local());
        BigEndianIEEEDouble_pb.def_readwrite("words", &BigEndianIEEEDouble::words);
        BigEndianIEEEDouble_words_T_pb.def_readwrite("wordH", &BigEndianIEEEDouble_words_T::wordH).def_readwrite("wordL", &BigEndianIEEEDouble_words_T::wordL);

        using LittleEndianIEEEDouble_words_T = decltype(LittleEndianIEEEDouble::words);
        pybind11::class_<LittleEndianIEEEDouble> LittleEndianIEEEDouble_pb (sl, "LittleEndianIEEEDouble", pybind11::module_local());
        pybind11::class_<LittleEndianIEEEDouble_words_T> LittleEndianIEEEDouble_words_T_pb (LittleEndianIEEEDouble_pb, "LittleEndianIEEEDouble_words_T", pybind11::module_local());
        LittleEndianIEEEDouble_pb.def_readwrite("words", &LittleEndianIEEEDouble::words);
        LittleEndianIEEEDouble_words_T_pb.def_readwrite("wordH", &LittleEndianIEEEDouble_words_T::wordH).def_readwrite("wordL", &LittleEndianIEEEDouble_words_T::wordL);

        using IEEESingle_words_T = decltype(IEEESingle::wordL);
        pybind11::class_<IEEESingle> IEEESingle_pb (sl, "IEEESingle", pybind11::module_local());
        pybind11::class_<IEEESingle_words_T> IEEESingle_words_T_pb (IEEESingle_pb, "IEEESingle_words_T", pybind11::module_local());
        IEEESingle_pb.def_readwrite("words", &IEEESingle::wordL);
        IEEESingle_words_T_pb.def_readwrite("wordLreal", &IEEESingle_words_T::wordLreal).def_readwrite("wordLuint", &IEEESingle_words_T::wordLuint);
    #endif

    #ifdef RTW_HEADER_rt_zcfcn_h_
        // From rt_zcfcn.h
        sl.def("rt_ZCFcn", rt_ZCFcn, "Detect zero crossings events.", "zcDir"_a, "prevZc"_a, "currValue"_a);
        sl.def("slZcHadEvent", [](ZCEventType ev, ZCDirection zcsDir){ return slZcHadEvent(ev, zcsDir); }, "ev"_a, "zcsDir"_a);
        sl.def("slZcUnAliasEvents", [](ZCEventType evL, ZCEventType evR){ return slZcUnAliasEvents(evL, evR); }, "evL"_a, "evR"_a);
    #endif

    #ifdef solver_zc_hpp_
        // From solver_zc.h
        auto slZcSignalType_pb = pybind11::enum_<slZcSignalType>(sl, "slZcSignalType", "slZcSignalType", pybind11::module_local());
        slZcSignalType_pb
            .value("SL_ZCS_TYPE_CONT", SL_ZCS_TYPE_CONT)
            .value("SL_ZCS_TYPE_DISC", SL_ZCS_TYPE_DISC)
            .value("SL_ZCS_TYPE_HYBRID", SL_ZCS_TYPE_HYBRID);
        BIND_INT_VALUE(SL_ZCS_EVENT_NUL);
        BIND_INT_VALUE(SL_ZCS_EVENT_N2P);
        BIND_INT_VALUE(SL_ZCS_EVENT_N2Z);
        BIND_INT_VALUE(SL_ZCS_EVENT_Z2P);
        BIND_INT_VALUE(SL_ZCS_EVENT_P2N);
        BIND_INT_VALUE(SL_ZCS_EVENT_P2Z);
        BIND_INT_VALUE(SL_ZCS_EVENT_Z2N);
        BIND_INT_VALUE(SL_ZCS_EVENT_ALL_UP);
        BIND_INT_VALUE(SL_ZCS_EVENT_ALL_DN);
        BIND_INT_VALUE(SL_ZCS_EVENT_ALL);

        sl.def("slZcSignalGetNeedsSolverReset", [](uint8_T a){ return slZcSignalGetNeedsSolverReset(a); }, "a"_a);
        sl.def("slZcSignalSetNeedsSolverReset", [](uint8_T a, bool v){ return slZcSignalSetNeedsSolverReset(a, v); }, "a"_a, "v"_a);
        sl.def("slZcSignalGetEventDirections", [](uint8_T a){ return slZcSignalGetEventDirections(a); }, "a"_a);
        sl.def("slZcSignalSetEventDirections", [](uint8_T a, ZCDirection d){ return slZcSignalSetEventDirections(a, d); }, "a"_a, "d"_a);
        sl.def("slZcSignalGetIsDiscrete", [](uint8_T a){ return slZcSignalGetIsDiscrete(a); }, "a"_a);
        sl.def("slZcSignalSetIsDiscrete", [](uint8_T a, bool v){ return slZcSignalSetIsDiscrete(a, v); }, "a"_a, "v"_a);
        sl.def("slZcSignalGetNeedsEventNotification", [](uint8_T a){ return slZcSignalGetNeedsEventNotification(a); }, "a"_a);
        sl.def("slZcSignalSetNeedsEventNotification", [](uint8_T a, bool v){ return slZcSignalSetNeedsEventNotification(a, v); }, "a"_a, "v"_a);

        BIND_INT_VALUE(SL_ZCS_SIGN_ZERO);
        BIND_INT_VALUE(SL_ZCS_SIGN_POS);
        BIND_INT_VALUE(SL_ZCS_SIGN_NEG);
        BIND_INT_VALUE(SL_ZCS_SIGN_UNKNOWN);
    #endif

    #undef BIND_INT_VALUE
    #undef BIND_FLOAT_VALUE
}
