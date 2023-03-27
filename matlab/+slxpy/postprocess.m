function postprocess(modelName, buildInfo)
assert(ischar(modelName) && isrow(modelName) && isa(buildInfo, 'RTW.BuildInfo'))
import slxpy.compat.ver_lt;
C = slxpy.internal.constants; MV = C.metadata_version;
MN = C.metadata_name; MD = C.model_dir; MWK = C.meta_workdir_key;
[~, MTT] = buildInfo.findBuildArg('MODELREF_TARGET_TYPE');
if strcmp(MTT, 'NONE')
    % Top model
    % Get code generation output directory like '*_ert_rtw'
    local_build_dir = buildInfo.getLocalBuildDir;
    % get workdir
    m = get_param(modelName, 'Metadata');
    if isempty(m) || ~isfield(m, MWK)
        error('Missing metadata, must run setup_config before code generation.')
    else
        workdir = m.(MWK);
        if ~exist(workdir, 'dir')
            error('Specified workdir %s not exist. Maybe workdir is moved or the model is used on another computer, locate workdir and rerun setup_config.')
        end
    end

    % Load codeInfo, transform and save to workdir
    codeInfo_file = fullfile(local_build_dir, 'codeInfo.mat');
    load(codeInfo_file, 'codeInfo');  % load variable 'codeInfo'
    codeInfo_tf = slxpy.transform_codeInfo(codeInfo);  % tf -> transformed
    author = get_param(modelName, 'Creator');
    version = get_param(modelName, 'ModelVersion');
    description = get_param(modelName, 'Description');
    metadata = struct(                        	...
        'f__version__', MV, 'name', modelName,  ...
        'author', author, 'version', version,   ...
        'description', description,             ...
        'sample_time', get_fundamental_sample_time(modelName), ...
        'model_class', codeInfo_tf.model_class,	...
        'structs', codeInfo_tf.structs,         ...
        'features', codeInfo_tf.features        ...
    );
    if ver_lt('R2021a')
        % Compat code for pre-R2020b which does not support instance parameters
        assert(~isfield(metadata.model_class.field_mapping, 'instance_parameters'))
        need_parameter_patch = isfield(metadata.model_class.field_mapping, 'parameters');
        if need_parameter_patch
            % NOTE: Uses undocumented but seemingly formal function renameStructField
            metadata.model_class.field_mapping = renameStructField(metadata.model_class.field_mapping, 'parameters', 'instance_parameters');
            metadata.model_class.type_mapping = renameStructField(metadata.model_class.type_mapping, 'parameters', 'instance_parameters');
        end
        if ver_lt('R2019a')
            % Before R2019a, static modifier does not exist, very unexpected, so no further source patch is needed
            need_parameter_patch = false;
        end
    else
        need_parameter_patch = false;
    end
    metadata_str = jsonencode(metadata);
    metadata_str = replace(metadata_str, '"f__version__":"', '"__version__":"');  % patch invalid MATLAB identifier
    fid = fopen(fullfile(workdir, MN), 'w');
    fprintf(fid, '%s', metadata_str);
    fclose(fid);
    % Pack and remove unnecessary files
    fclose(fopen(fullfile(local_build_dir, 'defines.txt'), 'w'));  % HACKY: fix defines.txt nonexistent during PCG command
    % Absolute path supported since R2018b
    % See: https://www.mathworks.com/help/releases/R2018b/ecoder/ref/packngo.html
    need_packNGo_relative = ver_lt('R2018b');
    if need_packNGo_relative
        packNGo_filename = [modelName '-' slxpy.internal.randstr(4) '.zip'];
    else
        packNGo_filename = fullfile(workdir, [modelName '.zip']);
    end
    packNGo(                                                    ...
        buildInfo, 'fileName', packNGo_filename,                ...
        'minimalHeaders', true, 'includeReport', false,         ...
        'ignoreParseError', false, 'ignoreFileMissing', false,  ...
        'packType', 'flat', 'nestedZipFiles', false             ...
    );
    if need_packNGo_relative
        % For pre-R2018a, absolute path is not supported, so generate and copy to target location
        % packNGo_filename generates relative to CodegenFolder and should be local_build_dir/..
        packNGo_temppath = fullfile(local_build_dir, '..', packNGo_filename);
        packNGo_filename = fullfile(workdir, [modelName '.zip']);
        movefile(packNGo_temppath, packNGo_filename);
    end
    pack_dir = fullfile(workdir, MD);
    if exist(pack_dir, 'dir')
        rmdir(pack_dir, 's')
    end
    unzip(packNGo_filename, pack_dir);
    % Patch header: {modelName}.h private -> public & static P to instance P
    class_header_path = fullfile(pack_dir, [modelName '.h']);
    class_header_patch = {'class_access'};
    if need_parameter_patch
        class_header_patch{end+1} = 'class_instP';
    end
    % Pre-2020a do not support IncludeModelTypesInModelClass, consider checking this param instead
    need_alias_patch = ver_lt('R2020a');
    if need_alias_patch
        class_header_patch{end+1} = 'class_type_alias';
    end
    read_patch_write({class_header_path}, class_header_patch, metadata);
    % Patch static definition in data file
    if need_parameter_patch
        % {modelName}_data.cpp must exist, since field_mapping contains 'parameter'
        data_source_path = fullfile(pack_dir, [modelName '_data.cpp']);
        data_header_patch = {'data_instP'};
        read_patch_write({data_source_path}, data_header_patch, metadata);
    end
    % Patch header: rtwtypes.h use native bool type
    rtwtypes_header_path = fullfile(pack_dir, 'rtwtypes.h');
    rtwtypes_header_patch = {'rtw_bool'};
    read_patch_write({rtwtypes_header_path}, rtwtypes_header_patch, metadata);
    % Patch source: {modelName}.h and {modelName}_data.cpp, avoid bloat
    % inline class member, only when model has tunable parameters
    if ~ver_lt('R2021b') && isfield(metadata.model_class.field_mapping, 'instance_parameters')
        % Instance parameter currently defines initial value in {modelName}.h
        % leading to very slow compilation and bloat binary size
        % if InstP size is large (e.g. a timeseries)
        data_source_path = fullfile(pack_dir, [modelName '_data.cpp']);
        if ~exist(data_source_path, 'file')
            % {modelName}_data.cpp not exist, giving a default template
            data_source = sprintf('/* Generated with slxpy */\n#include "%s.h"\n\n', modelName);
            filewrite(data_source_path, data_source);
        end
        read_patch_write({class_header_path data_source_path}, {'instP_location'}, metadata);
    end
    % Remove unnecessary files
    delete(packNGo_filename, fullfile(pack_dir, 'buildInfo.mat'), ...
        fullfile(pack_dir, 'ext_work.h'), fullfile(pack_dir, 'rt_logging.h'), ...
        fullfile(pack_dir, 'rt_cppclass_main.cpp') ...
    )
    if exist(fullfile(pack_dir, 'defines.txt'), 'file')
        % defines.txt may not exist on first run
        delete(fullfile(pack_dir, 'defines.txt'));
    end
    % Post-2022a Simscape management
    if is_simscape_used(buildInfo)
        manage_simscape_deps(pack_dir)
    end
elseif strcmp(MTT, 'RTW')
    % Model reference, currently just pass
else
    error('Unexpected MODELREF_TARGET_TYPE value: "%s"', MTT)
end
end

function filewrite(path, str)
file = fopen(path, 'w');
fprintf(file, '%s', str);
fclose(file);
end
function read_patch_write(paths, patches, metadata)
sources = cellfun(@(path) fileread(path), paths, 'UniformOutput', false);
sources = slxpy.internal.patch(sources, patches, metadata);
for i = 1:length(sources)
    filewrite(paths{i}, sources{i});
end
end
function ts = get_fundamental_sample_time(modelName)
h = get_param(modelName, 'Handle');
fs = strtrim(get_param(h, 'FixedStep'));
if strcmp(fs, 'auto')
    warning('Using auto sample time is discouraged for code generation. Set a fixed sample time literal or variable instead.')
end
tss = Simulink.BlockDiagram.getSampleTimes(h);
% See https://www.mathworks.com/help/simulink/ug/how-to-specify-the-sample-time.html
% D1 is expected to be the fundamental sample time
mask = strcmp({tss.Annotation}, 'D1');
fst = tss(mask);
assert(isscalar(fst))
if fst.Value(2) ~= 0
    warning('Sample time with offset is not well tested.')
end
ts = fst.Value(1);
end

% ----------------------------------------------------------------------- %
% Manage Simscape dependencies since R2022a
function flag = is_simscape_used(buildInfo)
simscape_prefix = fullfile('$(MATLAB_ROOT)', 'toolbox', 'physmod');
include_paths = buildInfo.getIncludePaths(false);
flag = any(startsWith(include_paths, simscape_prefix));
end

function manage_simscape_deps(pack_dir)
% Move cryptic simscape sources to subfolder
C = slxpy.internal.constants; SSP = C.simscape_source_prefix;
listing = dir(fullfile(pack_dir, '*.c'));
sources = {listing.name};
prefix_count = length(SSP);
for i = 1:prefix_count
    prefix = SSP{i};
    pattern = slxpy.internal.make_ssp(prefix);
    match = ~cellfun(@isempty, regexp(sources, pattern));
    if any(match)
        % pack_dir contains this pattern
        sub_dir = fullfile(pack_dir, prefix);
        mkdir(sub_dir);
        sources_match = sources(match);
        match_count = length(sources_match);
        for j = 1:match_count
            name = sources_match{j};
            src = fullfile(pack_dir, name);
            dst = fullfile(sub_dir, name);
            movefile(src, dst);
        end
        sources = sources(~match);
    end
end
pattern = slxpy.internal.make_ssp('.*');
match = ~cellfun(@isempty, regexp(sources, pattern));
assert(~any(match));  % Cryptic *.c sources shall have been consumed
end
