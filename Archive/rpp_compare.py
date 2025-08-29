#!/usr/bin/env python3
"""
RPP File Comparison Tool

A simple tool to compare REAPER project files (.RPP) and identify differences.
"""

import os
import re
import sys
from datetime import datetime
from collections import defaultdict


def parse_rpp_file(file_path):
    """Parse an RPP file and extract key data."""
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return None

    file_data = {
        "name": os.path.basename(file_path),
        "timestamp": None,
        "version": None,
        "params": {},
        "size": os.path.getsize(file_path),
    }

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.split("\n")

        # Get header info (version and timestamp)
        if lines:
            header_match = re.match(r'<REAPER_PROJECT [\d.]+ "([^"]*)" (\d+)', lines[0])
            if header_match:
                file_data["version"] = header_match.group(1)
                file_data["timestamp"] = int(header_match.group(2))

        # Extract parameters
        for line in lines:
            line = line.strip()
            if not line or line.startswith("<") and line.endswith(">"):
                continue

            if not (line.startswith("<") or line.startswith(">")):
                parts = line.split(" ", 1)
                if len(parts) >= 1:
                    param_name = parts[0]
                    param_value = parts[1] if len(parts) > 1 else ""
                    file_data["params"][param_name] = param_value

        return file_data

    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return None


def compare_files(files_data):
    """Compare multiple RPP files and identify differences."""
    if len(files_data) < 2:
        print("Need at least 2 files to compare")
        return None

    differences = {}

    # Compare timestamps
    timestamps = {name: data["timestamp"] for name, data in files_data.items() if data["timestamp"]}
    if len(set(timestamps.values())) > 1:
        differences["timestamps"] = timestamps

    # Compare versions
    versions = {name: data["version"] for name, data in files_data.items() if data["version"]}
    if len(set(versions.values())) > 1:
        differences["versions"] = versions

    # Compare file sizes
    sizes = {name: data["size"] for name, data in files_data.items()}
    if len(set(sizes.values())) > 1:
        differences["sizes"] = sizes

    # Compare parameters
    all_params = set()
    for data in files_data.values():
        all_params.update(data["params"].keys())

    param_diffs = {}
    for param in all_params:
        values = {}
        for name, data in files_data.items():
            values[name] = data["params"].get(param, "<missing>")

        # Check if all values are the same
        unique_values = set(values.values())
        if len(unique_values) > 1:
            param_diffs[param] = values

    if param_diffs:
        differences["parameters"] = param_diffs

    return differences


def format_timestamp(timestamp):
    """Convert Unix timestamp to readable format."""
    try:
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return str(timestamp)


def print_summary(files_data, differences):
    """Print a summary of the differences."""
    print("\n" + "=" * 60)
    print("RPP FILE COMPARISON SUMMARY")
    print("=" * 60)

    # Basic file info
    print(f"\nFiles analyzed: {len(files_data)}")
    for name, data in files_data.items():
        print(f"• {name}: {data['version'] or 'unknown version'}")

    # File sizes
    print("\nFILE SIZES:")
    for name, data in files_data.items():
        print(f"  {name}: {data['size']} bytes")

    # Print differences
    if differences:
        print("\nDIFFERENCES FOUND:")

        if "timestamps" in differences:
            print("\n  Timestamps:")
            for name, ts in differences["timestamps"].items():
                print(f"    {name}: {format_timestamp(ts)}")

        if "versions" in differences:
            print("\n  Versions:")
            for name, version in differences["versions"].items():
                print(f"    {name}: {version}")

        if "parameters" in differences:
            param_count = len(differences["parameters"])
            print(f"\n  Parameters: {param_count} differences")

            # Show first 5 parameter differences as example
            count = 0
            for param, values in differences["parameters"].items():
                if count >= 5:
                    print(f"\n  ... and {param_count - 5} more parameter differences")
                    break

                print(f"\n    {param}:")
                for name, value in values.items():
                    print(f"      {name}: {value}")
                count += 1
    else:
        print("\nNo significant differences found!")

    # Summary
    print("\n" + "-" * 60)
    if differences and differences.get("parameters"):
        print(f"Result: Found differences in {len(differences.get('parameters', {}))} parameters")
    elif differences:
        print("Result: Files differ only in metadata (timestamps, versions)")
    else:
        print("Result: Files are identical")


def main():
    """Main function to run the comparison."""
    if len(sys.argv) < 2:
        # Default behavior - check data directory
        data_dir = "data"
        rpp_files = [f for f in os.listdir(data_dir) if f.lower().endswith(".rpp")]
        if not rpp_files:
            print("No RPP files found in 'data' directory")
            print("Usage: python rpp_compare.py file1.RPP file2.RPP [file3.RPP ...]")
            return 1

        files = [os.path.join(data_dir, f) for f in rpp_files]
        print(f"Found {len(files)} RPP files in data directory")
    else:
        files = sys.argv[1:]

    # Parse all files
    files_data = {}
    for file_path in files:
        data = parse_rpp_file(file_path)
        if data:
            files_data[data["name"]] = data
            print(f"Parsed: {data['name']}")

    # Compare files
    differences = compare_files(files_data)

    # Print results
    if differences is not None:
        print_summary(files_data, differences)

    return 0


if __name__ == "__main__":
    sys.exit(main())
