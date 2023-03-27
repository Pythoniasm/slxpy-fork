function cs_set_param_skip(cs, name, value, reason)
try
    cs.set_param(name, value)
catch ME
    switch ME.identifier
        case 'configset:diagnostics:PropNotExist'
            warning('slxpy:compat:SkipConfigParam', 'Skip setting %s parameter: %s', name, reason)
        case 'SL_SERVICES:udd:EnumUnrecognized'
            warning('slxpy:compat:SkipConfigParam', 'Skip setting %s parameter, value %s unrecognized: %s', name, value, reason)
        otherwise
            rethrow(ME)
    end
end
end
