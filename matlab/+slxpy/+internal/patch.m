% NOTE: consider splitting into a package
function sources = patch(sources, patches, metadata)
patch_def = struct( ...
   'class_access', @patch_class_access,         ...
   'class_instP', @patch_class_instP,           ...
   'class_type_alias', @patch_class_type_alias,	...
   'data_instP', @patch_data_instP,             ...
   'instP_location', @patch_instP_location,     ...
   'rtw_bool', @patch_rtw_bool                  ...
);
if ischar(patches)
    patches = { patches };
end
assert(iscellstr(patches));
for i = 1:length(patches)
    patch = patches{i};
    patch_func = patch_def.(patch);
    if isscalar(sources)
        source = sources{1};
        source = patch_func(source, metadata);
        sources = {source};
    else
        sources = patch_func(sources, metadata);
    end
end
end

function source = patch_class_access(source, ~)
expression = '(?m)^( *)private:(\r?)$';
replace = '$1public:$2';
source = regexprep_checked(source, expression, replace, 1);
end
function source = patch_class_instP(source, metadata)
instP_name = metadata.model_class.field_mapping.instance_parameters;
instP_type = metadata.model_class.type_mapping.instance_parameters;
expression = sprintf('(?m)^( *)static (%s) (%s);(\r?)$', instP_type, instP_name);
replace = '$1static $2 $3_shared; $2 $3 { $3_shared };$4';
source = regexprep_checked(source, expression, replace, 1);
end
function source = patch_class_type_alias(source, metadata)
model_class_name = metadata.model_class.name;
type_mapping = metadata.model_class.type_mapping;
type_mapping_keys = fieldnames(type_mapping);
type_count = length(type_mapping_keys);
expression = sprintf('(?m)^( *)class %s {(\r?)$', model_class_name);
replace_parts = cell(1, 2 + type_count);
replace_parts{1} = sprintf('$1class %s {$2', model_class_name);
replace_parts{2} = '$1 public:$2';
for i = 1:type_count
    key = type_mapping_keys{i};
    type_name = type_mapping.(key);
    replace_parts{i+2} = sprintf('$1  using %s = ::%s;$2', type_name, type_name);
end
replace = join(replace_parts, newline);
source = regexprep_checked(source, expression, replace, 1);
end
function source = patch_data_instP(source, metadata)
model_class_ident = metadata.model_class.identifier;
instP_name = metadata.model_class.field_mapping.instance_parameters;
instP_type = metadata.model_class.type_mapping.instance_parameters;
% NOTE: either "{"    (C++ 11 aggregate initialization cppreference case 2)
%       or     " = {" (C++ 03 aggregate initialization cppreference case 1)
% NOTE: (?:(%s)::)? due to pre-R2020a IncludeModelTypesInModelClass compatibility
expression = sprintf('(?m)^(?:%s::)?(%s) (%s)::(%s)({| = {)(\r?)$',    ...
    model_class_ident, instP_type, model_class_ident, instP_name    ...
);
replace = '$2::$1 $2::$3_shared$4$5';
source = regexprep_checked(source, expression, replace, 1);
end
function source = patch_rtw_bool(source, ~)
expression = '(?m)^typedef unsigned char boolean_T;(\r?)$';
replace = 'typedef bool boolean_T;$1';
% count 2 due to ifdef PORTABLE_WORDSIZES guard
source = regexprep_checked(source, expression, replace, 2);
% NOTE: fix compat for .c code
expression = '(?m)^#if \(!defined\(__cplusplus\)\)(\r?)$';
replace = [                                 ...
    '#if (!defined(__cplusplus))$1' newline ...
    '#ifndef bool$1' newline                ...
    '#define bool unsigned char$1' newline  ...
    '#endif$1' newline                      ...
];
source = regexprep_checked(source, expression, replace, 1);
end
function sources = patch_instP_location(sources, metadata)
model_header = sources{1}; data_source = sources{2};
% Move instP to data source file
%
% {modelName}.h
% InstP_{modelName}_T {modelName}_InstP{
%   // initializer
% };
% ----------------
% static const InstP_{modelName}_T {modelName}_InitInstP;
% InstP_{modelName}_T {modelName}_InstP = {modelName}_InitInstP;
%
% {modelName}_data.cpp
% ----------------
% const {modelClass}::InstP_{modelName}_T {modelClass}::{modelName}_InitInstP{
%   // initializer
% };
model_class_name = metadata.model_class.name;
model_name = metadata.name;
instP_name = metadata.model_class.field_mapping.instance_parameters;
instP_type = metadata.model_class.type_mapping.instance_parameters;
[~, ending, full_ending] = detect_line_ending(model_header);

% NOTE: extern at end of header cannot be used, as it leads to non-trivial
% forward declaration conflict. Use static field instead.
% extern_expression = sprintf('(?m)^#endif +\\/\\* RTW_HEADER_%s_h_ \\*\\/%s$', model_name, ending);  % See rtw\c\tlc\mw\customstoragelib.tlc#SLibGenerateIncludeGuardMacro
% extern_replace = sprintf('extern const %s::InstP_%s_T %s_InitInstP;%s$0', model_class_name, model_name, model_name, full_ending);
% model_header = regexprep_checked(model_header, extern_expression, extern_replace, 1);

instP_expression = sprintf('(?m)^( *)%s %s(?={%s$)', instP_type, instP_name, ending);
regexp_exact(model_header, instP_expression, 1);
[match, tokens, split] = regexp(model_header, instP_expression, 'match', 'tokens', 'split');
match = match{1};
indent = tokens{1}{1};
pre_match = split{1};
post_match = split{2};
initializer_expression = sprintf('(?m)^%s};(?=%s$)', indent, ending); % NOTE: rely on well-formated (esp. indented) code
initializer_end = regexp(post_match, initializer_expression, 'end', 'once');
initializer = [indent post_match(1:initializer_end)]; % make indent uniform
initializer = dedent(initializer, length(indent), ending);
post_match = post_match(initializer_end+1:end);
model_header = sprintf('%s%sstatic const InstP_%s_T %s_InitInstP;%s%s{ %s_InitInstP };%s%s', pre_match, indent, model_name, model_name, full_ending, match, model_name, full_ending, post_match);
data_source = sprintf('%s%sconst %s::InstP_%s_T %s::%s_InitInstP%s%s', data_source, full_ending, model_class_name, model_name, model_class_name, model_name, initializer, full_ending);
sources = {model_header data_source};
end

function str = regexprep_checked(str, expression, replace, expect_match_count)
    regexp_exact(str, expression, expect_match_count);
    str = regexprep(str, expression, replace);
end

function regexp_exact(str, expression, expect_match_count)
start = regexp(str, expression, 'all');
if length(start) ~= expect_match_count
    error('Unexpected regexp match, expected %d, got %d', expect_match_count, length(start))
end
end

function [is_crlf, ending, full_ending] = detect_line_ending(str)
cr = char(13);
lines = split(str, newline);
assert(~endsWith(lines(end), cr), 'Bad last line ending')
lines = lines(1:end-1);
is_crlf = unique(endsWith(lines, cr));
assert(isscalar(is_crlf), 'Inconsistent line ending')
if is_crlf
    ending = cr;
else
    ending = '';
end
full_ending = [ending newline];
end

function source = dedent(source, n, ending)
indent = repmat(' ', 1, n);
lines = split(source, newline);
mask = startsWith(lines, indent);
empty_lines = lines(~mask);
assert(all(strcmp(empty_lines, ending)), 'Inconsistent indent');
lines(mask) = extractAfter(lines(mask), n);
source = join(lines, newline);
source = source{1};
end
