function try_load_model(sys)
% Check if model 'sys' is loaded, and load the model if not in memory
if ~bdIsLoaded(sys)
    fprintf('System %s not loaded. Loading may take a while.\nMake sure the model is on search path.\n', sys)
    load_system(sys)
end
end
