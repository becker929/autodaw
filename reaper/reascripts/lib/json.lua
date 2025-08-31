-- json.lua - JSON handling for ReaScripts
local json = {}

-- Function to convert Lua table to JSON string
function json.encode(tbl, level)
    level = level or 0
    local indent = string.rep("  ", level)
    local json_str = "{"

    local pairs_list = {}
    for k, v in pairs(tbl) do
        table.insert(pairs_list, k)
    end
    table.sort(pairs_list)

    local first = true
    for _, k in ipairs(pairs_list) do
        local v = tbl[k]
        if not first then
            json_str = json_str .. ","
        end
        first = false

        json_str = json_str .. "\n" .. indent .. "  "

        -- Key formatting
        if type(k) == "number" then
            json_str = json_str .. "\"" .. tostring(k) .. "\""
        else
            json_str = json_str .. "\"" .. tostring(k) .. "\""
        end

        json_str = json_str .. ": "

        -- Value formatting
        if type(v) == "table" then
            json_str = json_str .. json.encode(v, level + 1)
        elseif type(v) == "string" then
            json_str = json_str .. "\"" .. v:gsub("\\", "\\\\"):gsub("\"", "\\\""):gsub("\n", "\\n") .. "\""
        elseif type(v) == "number" or type(v) == "boolean" then
            json_str = json_str .. tostring(v)
        else
            json_str = json_str .. "\"" .. tostring(v) .. "\""
        end
    end

    if first then
        json_str = json_str .. "}"
    else
        json_str = json_str .. "\n" .. indent .. "}"
    end

    return json_str
end

-- Function to parse parameter changes from JSON string
function json.parse_param_changes(json_str)
    -- Simple JSON parser for our specific needs
    -- This is not a full JSON parser, but works for our simple case

    -- First, let's define our parsed result
    local result = {}

    -- Look for the paramChanges array
    local param_changes_str = json_str:match('"paramChanges"%s*:%s*%[(.-)%]')
    if not param_changes_str then
        return nil
    end

    -- Initialize the paramChanges array
    result.paramChanges = {}

    -- Find all parameter change objects
    for param_obj_str in param_changes_str:gmatch('{(.-)}') do
        local param_change = {}

        -- Extract track
        local track = param_obj_str:match('"track"%s*:%s*"?([^",}]+)"?')
        if track then param_change.track = track end

        -- Extract fx
        local fx = param_obj_str:match('"fx"%s*:%s*"?([^",}]+)"?')
        if fx then param_change.fx = fx end

        -- Extract param
        local param = param_obj_str:match('"param"%s*:%s*"?([^",}]+)"?')
        if param then param_change.param = param end

        -- Extract value
        local value_str = param_obj_str:match('"value"%s*:%s*"?([^",}]+)"?')
        if value_str then
            -- Convert to number if possible
            local num_value = tonumber(value_str)
            param_change.value = num_value or value_str
        end

        -- Add this parameter change to our result if it has all required fields
        if param_change.track and param_change.fx and param_change.param and param_change.value ~= nil then
            table.insert(result.paramChanges, param_change)
        end
    end

    return result
end

-- Function to parse FX parameter mapping from JSON
function json.parse_fx_mapping(json_str)
    if not json_str then
        error("Cannot parse nil JSON string")
    end

    if type(json_str) ~= "string" then
        error("Expected string input, got " .. type(json_str))
    end

    if json_str == "" then
        error("Empty JSON string")
    end

    local fx_data = {}

    -- Extract FX data section
    local fx_data_str = json_str:match('"fx_data":%s*({.+})')
    if not fx_data_str then
        error("JSON format error: Could not find 'fx_data' section in JSON. Check the file format.")
    end

    -- Check if we have at least one FX block
    local has_fx_blocks = fx_data_str:match('"[^"]+":%s*{')
    if not has_fx_blocks then
        error("JSON format error: No FX blocks found in 'fx_data' section")
    end

    -- Extract each FX block - we need a more sophisticated approach for nested braces
    local fx_count = 0

        -- Find all FX keys by looking for blocks that contain both "name" and "param_count" fields
    -- This distinguishes FX blocks from other objects like "project" or "parameters"
    local fx_keys = {}

    -- Look for pattern: "key": { ... "name": ... "param_count": ... }
    for fx_key in fx_data_str:gmatch('"([^"]+)":%s*{[^}]*"name"[^}]*"param_count"') do
        table.insert(fx_keys, fx_key)
    end

    -- Alternative: look for "param_count" first then "name"
    if #fx_keys == 0 then
        for fx_key in fx_data_str:gmatch('"([^"]+)":%s*{[^}]*"param_count"[^}]*"name"') do
            table.insert(fx_keys, fx_key)
        end
    end

    for _, fx_key in ipairs(fx_keys) do
        -- Extract the FX block by finding the matching braces
        local start_pattern = '"' .. fx_key:gsub("([%(%)%.%+%-%*%?%[%]%^%$%%])", "%%%1") .. '":%s*{'
        local start_pos = fx_data_str:find(start_pattern)

        if start_pos then
            local brace_count = 0
            local fx_block_start = fx_data_str:find('{', start_pos)
            local fx_block_end = fx_block_start

            for i = fx_block_start, #fx_data_str do
                local char = fx_data_str:sub(i, i)
                if char == '{' then
                    brace_count = brace_count + 1
                elseif char == '}' then
                    brace_count = brace_count - 1
                    if brace_count == 0 then
                        fx_block_end = i
                        break
                    end
                end
            end

            local fx_block = fx_data_str:sub(fx_block_start, fx_block_end)

            local fx_info = {}
            fx_count = fx_count + 1

            -- Extract FX name
            fx_info.name = fx_block:match('"name":%s*"([^"]+)"')
            if not fx_info.name then
                error("Missing 'name' field in FX block: " .. fx_key)
            end

            -- Extract param_count
            fx_info.param_count = tonumber(fx_block:match('"param_count":%s*([%d]+)'))

            -- Extract parameters
            fx_info.parameters = {}

            -- Find parameters section
            local params_section = fx_block:match('"parameters":%s*({.+})')
            if params_section then
                -- Extract each parameter - the keys are sequential numbers starting from 1
                local param_count = 0
                for param_key, param_block in params_section:gmatch('"(%d+)":%s*({.-})') do
                    local param_info = {}
                    param_count = param_count + 1

                    -- The parameter key is 1-based in the JSON, convert to 0-based for REAPER API
                    param_info.index = tonumber(param_key) - 1
                    param_info.name = param_block:match('"name":%s*"([^"]+)"')

                    if not param_info.name then
                        error("Missing parameter name in FX block: " .. fx_key .. ", param key: " .. param_key)
                    end

                    -- Store by name for quick lookup
                    fx_info.parameters[param_info.name] = param_info
                end

                if param_count == 0 then
                    error("No parameters found in FX block: " .. fx_key)
                end
            else
                error("Missing 'parameters' section in FX block: " .. fx_key)
            end

            fx_data[fx_key] = fx_info

            -- Also store by FX name for easier lookup
            fx_data[fx_info.name] = fx_info
        end
    end

    if fx_count == 0 then
        error("No valid FX blocks parsed from JSON")
    end

    return fx_data
end

-- Function to read JSON from a file
function json.read_file(file_path)
    local file = io.open(file_path, "r")
    if not file then
        return nil, "Could not open file: " .. file_path
    end

    local content = file:read("*all")
    file:close()

    return content
end

-- Function to write JSON to a file
function json.write_file(file_path, data)
    local file = io.open(file_path, "w")
    if not file then
        return false, "Could not open file for writing: " .. file_path
    end

    local json_str = json.encode(data)
    file:write(json_str)
    file:close()

    return true
end

return json
