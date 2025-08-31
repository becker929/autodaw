#!/usr/bin/env lua

-- test_standalone.lua - Standalone test runner for command line testing
-- This allows us to test our modules outside of REAPER

-- Add current directory to path
local script_path = debug.getinfo(1, "S").source:match("@(.*/)")
if script_path then
    package.path = script_path .. "?.lua;" .. package.path
end

-- Run the tests
require("tests.run_tests")
