function cs_set_param_ver_lt(target_version, cs, name, if_value, else_value)
if slxpy.compat.ver_lt(target_version)
    cs.set_param(name, if_value);
else
    cs.set_param(name, else_value);
end
end
