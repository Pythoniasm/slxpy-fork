function codegen(workdir)
% TODO: find_mdlrefs
import slxpy.compat.ver_lt;
import slxpy.compat.TunableParameter;
C = slxpy.internal.constants; CSN = C.config_set_name; CIN = C.model_config_name;
cfg = slxpy.thirdparty.toml.read(fullfile(workdir, CIN));
model = cfg.model;
slxpy.try_load_model(model);
if ver_lt('R2021a')
    TunableParameter.compat(model)
end
original_configset = getActiveConfigSet(model);
original_configset_name = original_configset.Name;
setActiveConfigSet(model, CSN)
try
    slbuild(model)
catch ME
    if ver_lt('R2021a')
        TunableParameter.restore(model)
    end
    rethrow(ME)
end
if ver_lt('R2021a')
    TunableParameter.restore(model)
end
setActiveConfigSet(model, original_configset_name)
end
