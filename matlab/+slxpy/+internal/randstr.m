function str = randstr(len)
symbols = ['a':'z' 'A':'Z' '0':'9'];
nums = randi(numel(symbols),[1 len]);
str = symbols(nums);
end

