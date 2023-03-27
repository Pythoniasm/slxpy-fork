function setup_config(workdir)
% Setup config set for code generation
warning('off', 'JSimon:GetFullPath:NoMex')  % suppress GetFullPath's NoMex warning
C = slxpy.internal.constants; CSN = C.config_set_name; CIN = C.model_config_name;
workdir = slxpy.thirdparty.GetFullPath(workdir, 'lean');
cfg = slxpy.thirdparty.toml.read(fullfile(workdir, CIN));
model = cfg.model;
slxpy.try_load_model(model);
save_workdir_to_metadata(model, workdir)
slxpy_config_set = getConfigSet(model, CSN);
if isempty(slxpy_config_set)
    % setup config set, copy from active config set
    active_config_set = getActiveConfigSet(model);
    slxpy_config_set = active_config_set.copy();
    slxpy_config_set.set_param('Name', CSN);
    attachConfigSet(model, slxpy_config_set, false);
end
slxpy.tune_codegen_config(slxpy_config_set, cfg.simulink);
tune_code_mapping(model, cfg.cpp)
save_system(model)
end

function save_workdir_to_metadata(model, workdir)
C = slxpy.internal.constants; MWK = C.meta_workdir_key;
m = get_param(model, 'Metadata');
if isempty(m)
    m = struct;
end
m.(MWK) = workdir;
set_param(model, 'Metadata', m)
end

function tune_code_mapping(model, cpp_config)
% Control C++ codegen interface
C = slxpy.internal.constants; CSN = C.config_set_name;
original_configset = getActiveConfigSet(model);
original_configset_name = original_configset.Name;
setActiveConfigSet(model, CSN)
cs = getConfigSet(model, CSN);
if slxpy.compat.ver_lt('R2021a')
    tune_code_mapping_lt_R2021a(model, cpp_config, cs);
else
    tune_code_mapping_ge_R2021a(model, cpp_config, cs);
end
setActiveConfigSet(model, original_configset_name)
end

function tune_code_mapping_ge_R2021a(model, cpp_config, cs)
try
    cm = coder.mapping.api.get(model);
catch
    cm = coder.mapping.utils.create(model, cs);
end
cm.setClassName(cpp_config.class_name);
cm.setClassNamespace(cpp_config.namespace);
cm.setData('Inports', 'DataVisibility', 'public')
cm.setData('Outports', 'DataVisibility', 'public')
cm.setData('ModelParameters', 'DataVisibility', 'public')
cm.setData('ModelParameterArguments', 'DataVisibility', 'private')
cm.setData('InternalData', 'DataVisibility', 'public')
cm.setData('Inports', 'MemberAccessMethod', 'None')
cm.setData('Outports', 'MemberAccessMethod', 'None')
cm.setData('ModelParameters', 'MemberAccessMethod', 'None')
cm.setData('ModelParameterArguments', 'MemberAccessMethod', 'None')
cm.setData('InternalData', 'MemberAccessMethod', 'None')
end

function tune_code_mapping_lt_R2021a(model, cpp_config, cs)
import slxpy.compat.cs_set_param_skip
mcdc = RTW.ModelCPPDefaultClass;
mcdc.attachToModel(model);
mcdc.getDefaultConf();
mcdc.setClassName(cpp_config.class_name);
mcdc.setNamespace(cpp_config.namespace);
cs.set_param('ParameterMemberVisibility', 'public');
cs_set_param_skip(cs, 'ExternalIOMemberVisibility', 'public', 'Supported since R2020a');
cs.set_param('GenerateParameterAccessMethods', 'none');
cs.set_param('GenerateExternalIOAccessMethods', 'none');
end
