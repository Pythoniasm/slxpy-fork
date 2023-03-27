function pat = make_ssp(prefix)
%MAKE_SSP Make Simscape source pattern
pat = ['^' prefix '_[0-9a-f]{8}.c$'];
end
