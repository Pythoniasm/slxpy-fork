function codeinfo_tf = transform_codeInfo(codeInfo)
% Transform codeInfo to slxpy-compliant format, tf means transform(ed)
% NOTE: Some assumptions may be invalid outside simulink built-in data class
% Most 'Unsupported' errors are actually due to lack of code generation results to test against
[structs, model_class] = get_structs_and_model_class(codeInfo);
% NOTE: The following two line order important! InstP is patched in
% transform_structs then used in transform_model_class > create_mapping
structs_tf = transform_structs(structs, [model_class.Identifier '::']);
model_class_tf = transform_model_class(model_class, codeInfo.Name);
features_tf = get_coder_features();
codeinfo_tf = struct(               ...
    'model_class', model_class_tf,  ...
    'structs', structs_tf,          ...
    'features', features_tf         ...
);
end

function features_tf = get_coder_features()
import slxpy.compat.ver_lt;
features_tf = struct(               ...
    'scoped_enum', ~ver_lt('R2022a')...  % Scoped enum classes in Embedded Coder Version 7.8 (R2022a)
);
end

% ----------------------------------------------------------------------- %

function [structs, model_class] = get_structs_and_model_class(codeInfo)
    % Split model classes and structs from codeInfo.Types
    types = codeInfo.Types;
    len_types = length(types);
    % Mask for data structs (struct or union), should be POD
    mask = zeros([len_types 1], 'logical');
    % Mask for model class, use a mask to ensure only one 'candidate'
    mask2 = zeros([len_types 1], 'logical');
    for i = 1:len_types
        tp = types(i);
        % Filter out Struct but not Class, also Enum
        mask(i) = (isa(tp, 'coder.types.Struct') && ~isa(tp, 'coder.types.Class')) || isa(tp, 'coder.types.Enum');
        % Filter out Class and workaround for std::string class (not sure if it's the only case)
        mask2(i) = isa(tp, 'coder.types.Class') && ~strcmp(tp.Identifier, 'std::string');
    end
    structs = types(mask);
    model_class = types(mask2);
    assert(isscalar(model_class), 'Unexpected codeInfo, more than one candidate for model class')
end

% ----------------------------------------------------------------------- %

function model_class_tf = transform_model_class(model_class, model_name)
    % Transform model class, model_name is used for workarounds and mapping creation
    model_class_identifier = model_class.Identifier;
    if contains(model_class_identifier, '::')
        % Within namespace
        parts = split(model_class_identifier, '::');
        model_class_name = parts{end};
        % Use 'join' to support nested namespace definition (e.g. A::B::C), requires C++17
        % but simulink seems to forbid such namespace, thus 'join' is actually no-op
        model_class_namespace = join(parts(1:end-1), '::');
        model_class_namespace = model_class_namespace{1};
    else
        % Root namespace
        model_class_name = model_class_identifier;
        model_class_namespace = missing;
    end
    % Workaround for wrong instP codeInfo, strict check for code generation correctness
    % Element '{model_name}_self' of struct type 'RT_MODEL_*', and only one field which is the actual field
    % Make a patch if conditions meet
    for i = 1:length(model_class.Elements)
        el = model_class.Elements(i);
        if strcmp(el.Identifier, [model_name, '_self'])
            assert(startsWith(el.Type.Name, 'RT_MODEL_') && isscalar(el.Type.Elements) && strcmp(el.Type.Elements(1).Identifier, [model_name, '_InstP']))
            el.Identifier = el.Type.Elements(1).Identifier;
            el.Type = el.Type.Elements(1).Type;
        end
    end
    model_class_methods = transform_model_class_methods(model_class.Methods, model_class_identifier);
    model_class_fields = transform_model_class_fields(model_class.Elements);
    [field_mapping, type_mapping] = create_mapping(model_class.Elements, model_name);
    model_class_tf = struct(                    ...
        'name', model_class_name,               ...
        'namespace', model_class_namespace,     ...
        'identifier', model_class_identifier,   ...
        'methods', model_class_methods,         ...
        'fields', model_class_fields,           ...
        'field_mapping', field_mapping,         ...
        'type_mapping', type_mapping            ...
    );
end

function model_class_methods = transform_model_class_methods(methods, model_class_identifier)
    % Transform methods, model_class_identifier is used to exclude constructor
    EXPECTED_METHODS = {'initialize' 'step' 'terminate'};
    model_class_methods = struct('name', { methods.Name });
    len_methods = length(methods);
    mask = ones([len_methods 1], 'logical'); % To exclude methods
    for i = 1:len_methods
        me = methods(i);
        if strcmp(me.Name, model_class_identifier)
            % Exclude constructor
            mask(i) = 0;
        else
            % Keep other methods
            % Sanity check: one of EXPECTED_METHODS, no arguments, no return value
            assert(isempty(me.Arguments) && isempty(me.Type) && any(strcmp(me.Name, EXPECTED_METHODS)), 'Unexpected model class method: %s', me.Name)
        end
    end
    model_class_methods = model_class_methods(mask);
end

function model_class_fields = transform_model_class_fields(fields)
    % Transform fields, model class fields need no extra information (contrary to struct fields)
    % Already patched in 'transform_model_class', thus every field shall be valid
    len_fields = length(fields);
    for i = 1:len_fields
        field = fields(i);
        % Sanity check: all model class fields should have struct type
        % Explicitly check type equality, exclude subclasses like Class and Union
        assert(strcmp(class(field.Type), 'coder.types.Struct'))  %#ok<STISA>
    end
    model_class_fields = struct('name', { fields.Identifier });
end

function [field_mapping, type_mapping] = create_mapping(fields, model_name)
    % Create method and field mapping, currently method mapping is hard-coded
    field_mapping = struct(   ...
        'initialize', 'initialize', ...
        'step', 'step',             ...
        'terminate', 'terminate'    ...
    );
    type_mapping = struct;
    MP = slxpy.mapping_prototype;
    expected_identifiers = strcat(model_name, '_', MP(:, 2));
    for i = 1:length(fields)
        field = fields(i);
        idx = find(strcmp(field.Identifier, expected_identifiers));
        assert(isscalar(idx))  % should be exactly one
        field_mapping.(MP{idx, 1}) = field.Identifier;
        type_mapping.(MP{idx, 1}) = field.Type.Name;
    end
end

% ----------------------------------------------------------------------- %

function structs_tf = transform_structs(structs, model_class_prefix)
    % Transform structs, use model_class_prefix to partition global and class-inner structs
    % Patch alias
    need_alias_patch = slxpy.compat.ver_lt('R2020a');
    % Exclude duplicates and fix wrong InstP codeInfo
    len_structs = length(structs);
    mask = ones([len_structs 1], 'logical');
    for i = 1:len_structs
        if mask(i) == 0
            continue  % Skip as already excluded
        end
        st = structs(i);
        rest = structs(i+1:end);

        identifier_mask = strcmp(st.Identifier, {rest.Identifier});  % Find types with same identifier

        % Special case: Enum
        if isa(st, 'coder.types.Enum')
            assert(strcmp(st.Identifier, st.Name));  % Expect identifier same as name
            mask(find(identifier_mask) + i) = 0;  % Offset by i
            continue;
        end

        checksum = st.Checksum;
        if isequal(size(checksum), [1 0])
            % Special case: For complex models (in VDBS for example), some
            % identifiers seem to lack the model_class_prefix. So patch
            % with a regex check. These identifiers seem to have the
            % pattern of being referenced by other model structs.
            has_simulink_pattern = ~isempty(regexp(st.Identifier, '^(DW|X|B)_\w+_T$', 'once'));
            if need_alias_patch || has_simulink_pattern
                % Consider safer patch?
                st.Identifier = [model_class_prefix st.Identifier];
                identifier_mask = strcmp(st.Identifier, {rest.Identifier});  % Recompute since identifier changed
            else
                % Expect only class member structs do not have checksum
                assert(startsWith(st.Identifier, model_class_prefix), 'Unexpected global type without checksum %s', st.Name)
            end
            no_duplicate = all(~identifier_mask);
            if has_simulink_pattern
                if ~no_duplicate
                    % Special case: Contains duplicate after identifier patch
                    % For VDBS vehicle14dof model, two DW_detectLockup_vehicle14dof_T types are generated
                    % One at the beginning of the list, one at normal position
                    % So we hypothetically assert all such unexpected duplicate occurance shall
                    % happen at the beginning of the list contiguously and apply a mask
                    assert(~any(mask(1:i-1)))
                    mask(i) = 0;
                end
            else
                assert(no_duplicate, 'Unexpected duplicate within class member structs')
            end
        else
            % Global struct (bus type) shall have checksum
            assert(isequal(size(checksum), [1 4]), 'Unexpected checksum length')
            checksum_mask = arrayfun(@(x) ~isa(x, 'coder.types.Enum') && isequal(checksum, x.Checksum), rest);
            assert(isequal(identifier_mask, checksum_mask), 'Identifier mask does not correspond to checksum mask')
            mask(find(identifier_mask) + i) = 0;  % Offset by i
        end
        if startsWith(st.Name, 'RT_MODEL_')
            mask(i) = 0;  % Workaround for wrong instP codeInfo
        end
        if startsWith(st.Identifier, model_class_prefix) && strcmp(st.Identifier, st.Name)
            % Workaround for wrong instP codeInfo
            % InstP_* currently has Name same as Identifier (with '::')
            assert(startsWith(st.Identifier, [model_class_prefix 'InstP_']))
            st.Name = st.Identifier(length(model_class_prefix)+1:end);
            assert(~contains(st.Name, '::'))  % Expect non-nested struct
        end
    end
    structs = structs(mask);
    % Do the transform
    len_structs = length(structs);
    structs_tf = struct('name', { structs.Name }, 'location', [], 'fields', [], 'is_enum', []);
    for i = 1:len_structs
        st = structs(i);
        identifier = st.Identifier;
        is_enum = isa(st, 'coder.types.Enum');
        is_InstP = startsWith(st.Name, 'InstP_');  % Scope info for array shape workaround. Safer check?
        structs_tf(i).is_enum = is_enum;
        % Determine struct location
        if is_enum
            % Special case: Enum, expect to be outside class, early return
            structs_tf(i).location = 'root';
            names = reshape(st.Strings, 1, []);
            values = reshape(num2cell(st.Values), 1, []);
            id_with_suffix = [identifier '::'];
            assert(all(startsWith(names, id_with_suffix)));
            names = extractAfter(names, length(id_with_suffix));
            structs_tf(i).fields = struct(  ...
                'name', names,              ...
                'value', values             ...
            );
            structs_tf(i).is_enum = true;
            structs_tf(i).default = st.DefaultMember - 1;  % Zero-based indicing
            % StorageType via std::underlying_type
            continue;
        elseif startsWith(identifier, model_class_prefix)
            % Within class, should be class member structs
            % Not sure whether nested structs exist in code interface (exclude RT_MODEL which is not part of public interface)
            assert(strcmp(identifier(length(model_class_prefix)+1:end), st.Name), 'Unsupported nested structs')
            structs_tf(i).location = 'model_class';
        else
            % Outside class
            % Not sure whether nested structs exist in code interface
            structs_tf(i).location = 'root';
        end
        % Transform struct fields
        elements = st.Elements;
        assert(isa(elements, 'coder.types.AggregateElement'))
        len_elements = length(elements);
        fields = cell([len_elements 1]);
        field_mask = ones([len_elements 1], 'logical');
        for j = 1:len_elements
            el = elements(j);
            field = struct('name', el.Identifier);
            if endsWith(el.Identifier, '_PWORK') || endsWith(el.Identifier, '_IWORK')  || endsWith(el.Identifier, '_RWORK')
                % Workaround for _P(Pointer)/I(Integer)/R(Real)WORK fields due to weird code interface
                % Currently filter these fields out. Also, el.Type seems not limited to coder.types.Matrix.

                % if isa(el.Type, 'coder.types.Matrix')
                field_mask(j) = false;
                continue;
                % end
            end
            if isa(el.Type, 'coder.types.Pointer')
                % Workaround for Simscape fields, including
                % _RtpManager/_Simulator/_SimData/_DiagMgr/_ZcLogger/_TsInfo
                % Supporting all of them is difficult, so disabling pointer codegen
                field_mask(j) = false;
                continue;
            end
            [field, valid] = transform_field_type(field, el.Type, false, is_InstP);
            fields{j} = field;
            field_mask(j) = valid;
        end
        fields = fields(field_mask);
        structs_tf(i).fields = fields;
    end
end

function [field, valid] = transform_field_type(field, tp, valid_only, under_InstP_scope)
    % Transform field type
    valid = true;  % Workaround for Mdlref* fields, see below
    if isa(tp, 'coder.types.Scalar') || isa(tp, 'coder.types.Complex')
        % Numeric(Half, Single, Double, Bool, Int), Char, Enum, Fixed | Complex
        if isa(tp, 'coder.types.Enum')
            field.mode = 'enum';
            field.type = tp.Identifier;
        else
            field.mode = 'plain';
            % Currently plain type don't need additional information
        end
    elseif isa(tp, 'coder.types.Matrix')
        % Workaround: InstP may generate strange [1 1] matrix, but reduced to scalar
        if under_InstP_scope
            if ~isequal(tp.Dimensions, [1 1]) && ~isequal(tp.Dimensions, 1)
                assert(prod(tp.Dimensions) > 1)
                field.is_array = true;
                field.shape = tp.Dimensions;
            end
        else
            % Workaround: Under other structs, the reduction seems not hold
            % e.g. X_CoreSubsys_vehicle14dof_aav1_T CoreSubsys_c2qo[1];
            assert(prod(tp.Dimensions) > 1 || isequal(tp.Dimensions, 1))
            field.is_array = true;
            field.shape = tp.Dimensions;
        end
        base = tp.BaseType;
        assert(~isa(base, 'coder.types.Matrix'))
        [field, ~] = transform_field_type(field, base, true, under_InstP_scope);
    elseif isa(tp, 'coder.types.Aggregate')
        % Struct, Class, ContainerClass, Union
        switch class(tp)
            case {'coder.types.Struct' 'coder.types.Union'}
                % However, Union is never seen before
                field.mode = 'struct';

                % Previously, struct fields with struct type are assumed to
                % be global struct only. This assumption seems to be broken
                % with complex VDBS 14dof models, thus relax the check.
                assert(endsWith(tp.Identifier, tp.Name))
                field.type = tp.Identifier;
            case {'coder.types.Class' 'coder.types.ContainerClass'}
                if strcmp(tp.Identifier, 'std::string')
                    % Workaround for string data type
                    field.mode = 'std';
                    field.type = 'std::string';
                    warning('Using string might break further binding as std::string is not POD.')
                else
                    report_unsupported_coder_type(tp)
                end
            otherwise
                % Should not happen, as above is comprehensive (except user-defined coder types)
                report_unsupported_coder_type(tp)
        end
    elseif isa(tp, 'coder.types.Pointer') || isa(tp, 'coder.types.Reference')
        % Pointer and reference are tricky to handle and no test case yet
        if isa(tp, 'coder.types.Pointer')
            % Temporary treat all pointer as void* pointer
            field.mode = 'pointer';
            field.underlying = 'void';
        else
            report_unsupported_coder_type(tp)
        end
    elseif isa(tp, 'coder.types.Void') || isa(tp, 'coder.types.Opaque')
        % Special types
        if isa(tp, 'coder.types.Opaque') && startsWith(tp.Name, 'Mdlref')
            % Temporary workaround to exclude Mdlref* fields, which in fact not exist in code
            valid = false;
        else
            report_unsupported_coder_type(tp)
        end
    else
        % Should not happen, as above is comprehensive (except user-defined coder types)
        report_unsupported_coder_type(tp)
    end
    if valid_only && ~valid
        error('Invalid type is not allowed.')
    end
end

function report_unsupported_coder_type(tp)
    error('Unsupported coder type: %s', class(tp))
end
