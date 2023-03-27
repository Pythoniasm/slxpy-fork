classdef TunableParameter
    methods(Static)
        % tp -> tunable parameter, mw -> model workspace, bw -> base workspace
        function check_consistent(model, expect_status, reason)
            % Check if model workspace naming is in consistent state
            import slxpy.compat.TunableParameter;
            if nargin == 1
                expect_status = [0 1];
                reason = 'Inconsistent model workspace arguments';
            end
            tp_name_csl = get_param(model,'ParameterArgumentNames');  % comma separated list
            if isempty(tp_name_csl)
                return
            end
            tp_names = strsplit(tp_name_csl, ',');
            status = TunableParameter.tp2status(tp_names);
            if ~any(status == expect_status)
                error('slxpy:compat:InconsistentParameter', reason)
            end
        end

        function compat(model)
            % Turn a R2021a like model to pre-R2020b compatible for tunable parameters
            import slxpy.compat.TunableParameter;
            TunableParameter.check_consistent(model);
            TunableParameter.rename_compat(model);
            TunableParameter.copy_to_bw(model);
        end

        function restore(model)
            % Restore model workspace changes
            import slxpy.compat.TunableParameter;
            TunableParameter.rename_restore(model);
        end

        function rename_restore(model)
            C = slxpy.internal.constants; TCS = C.tp_compat_suffix;
            tp_name_csl = get_param(model,'ParameterArgumentNames');
            if isempty(tp_name_csl)
                return
            end
            tp_names_all = strsplit(tp_name_csl, ',');

            tp_renamed_mask = endsWith(tp_names_all, TCS);
            if ~any(tp_renamed_mask)
                return
            end
            tp_names = tp_names_all(tp_renamed_mask);

            tp_name_ssl = join(tp_names, ' '); tp_name_ssl = tp_name_ssl{1};
            tp_rename = cellfun(@(name) name(1:end-length(TCS)), tp_names, 'UniformOutput', false);

            mw = get_param(model, 'ModelWorkspace');
            tp_rename_exist = cellfun(@(name) mw.hasVariable(name), tp_rename);
            if any(tp_rename_exist)
                error('slxpy:compat:InconsistentParameter', 'Parameter to restore already exists.')
            end
            for i = 1:length(tp_rename)
                mw.assignin(tp_rename{i}, mw.getVariable(tp_names{i}));
            end
            expr = sprintf('clear %s;', tp_name_ssl);
            mw.evalin(expr);

            tp_names_all(tp_renamed_mask) = tp_rename;
            tp_names_all_csl = join(tp_names_all, ','); tp_names_all_csl = tp_names_all_csl{1};
            set_param(model,'ParameterArgumentNames',tp_names_all_csl);
        end

        function copy_to_bw(model)
            C = slxpy.internal.constants; TCS = C.tp_compat_suffix;
            tp_name_csl = get_param(model,'ParameterArgumentNames');
            if isempty(tp_name_csl)
                return
            end
            tp_names = strsplit(tp_name_csl, ',');
            mw = get_param(model, 'ModelWorkspace');
            expr = sprintf('{%s}', tp_name_csl);
            parameters = mw.evalin(expr);
            parameters = cellfun(@(p) p.copy(), parameters, 'UniformOutput', false);
            for i = 1:length(tp_names)
                name = tp_names{i};
                p = parameters{i};
                p.CoderInfo.StorageClass = 'Model Default';
                if endsWith(name, TCS)
                    name = name(1:end-length(TCS));
                end
                assignin('base', name, p);
            end
        end
    end
    methods(Static,Access=private)
        % tp -> tunable parameter, mw -> model workspace
        function [status, mask] = tp2status(tp_names)
            % Status: 0 - consistent for post-R2021a, or empty
            %         1 - consistent for pre-R2020b
            %         2 - inconsistent
            C = slxpy.internal.constants; TCS = C.tp_compat_suffix;
            mask = endsWith(tp_names, TCS);
            if ~any(mask)
                % Empty falls into this category
                status = 0;
            elseif all(mask)
                status = 1;
            else
                status = 2;
            end
        end

        function rename_compat(model)
            C = slxpy.internal.constants; TCS = C.tp_compat_suffix;
            tp_name_csl = get_param(model,'ParameterArgumentNames');
            if isempty(tp_name_csl)
                return
            end
            tp_names_all = strsplit(tp_name_csl, ',');

            tp_renamed_mask = endsWith(tp_names_all, TCS);
            if all(tp_renamed_mask)
                return
            end
            tp_names = tp_names_all(~tp_renamed_mask);

            tp_name_ssl = join(tp_names, ' '); tp_name_ssl = tp_name_ssl{1};
            tp_rename = strcat(tp_names, TCS);

            mw = get_param(model, 'ModelWorkspace');
            tp_rename_exist = cellfun(@(name) mw.hasVariable(name), tp_rename);
            if any(tp_rename_exist)
                error('slxpy:compat:InconsistentParameter', 'Parameter to rename already exists.')
            end

            for i = 1:length(tp_rename)
                mw.assignin(tp_rename{i}, mw.getVariable(tp_names{i}));
            end
            expr = sprintf('clear %s;', tp_name_ssl);
            mw.evalin(expr);
            tp_names_all(~tp_renamed_mask) = tp_rename;
            tp_names_all_csl = join(tp_names_all, ','); tp_names_all_csl = tp_names_all_csl{1};
            set_param(model,'ParameterArgumentNames',tp_names_all_csl);
        end
    end
end
