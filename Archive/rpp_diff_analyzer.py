#!/usr/bin/env python3
"""
RPP File Difference Analyzer

This script analyzes and summarizes differences between REAPER project files (.RPP).
It compares file structure, timestamps, and specific parameter values.
"""

import os
import re
from datetime import datetime
from typing import Dict, List, Tuple, Any
from collections import defaultdict
import argparse


class RPPAnalyzer:
    """Analyzes REAPER project files and finds differences between them."""

    def __init__(self):
        self.files_data = {}
        self.common_structure = set()
        self.differences = defaultdict(dict)

    def parse_rpp_file(self, file_path: str) -> Dict[str, Any]:
        """Parse an RPP file and extract key-value pairs and structure."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        data = {
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "lines": [],
            "parameters": {},
            "structure": [],
            "timestamp": None,
            "version": None,
        }

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        data["lines"] = [line.rstrip() for line in lines]

        # Parse header line for version and timestamp
        if lines:
            header_match = re.match(
                r'<REAPER_PROJECT ([\d.]+) "([^"]*)" (\d+)', lines[0]
            )
            if header_match:
                data["version"] = header_match.group(2)
                data["timestamp"] = int(header_match.group(3))

        # Extract parameters and structure
        for i, line in enumerate(data["lines"]):
            line = line.strip()
            if not line or line.startswith("<") and line.endswith(">"):
                continue

            # Track structure elements
            if line.startswith("<") or line.startswith(">"):
                data["structure"].append(line)
            else:
                # Extract parameter lines
                parts = line.split(" ", 1)
                if len(parts) >= 1:
                    param_name = parts[0]
                    param_value = parts[1] if len(parts) > 1 else ""
                    data["parameters"][param_name] = param_value

        return data

    def analyze_files(self, file_paths: List[str]) -> None:
        """Analyze multiple RPP files and identify differences."""
        print(f"Analyzing {len(file_paths)} RPP files...")

        # Parse all files
        for file_path in file_paths:
            try:
                data = self.parse_rpp_file(file_path)
                self.files_data[data["file_name"]] = data
                print(f"✓ Parsed {data['file_name']}")
            except Exception as e:
                print(f"✗ Error parsing {file_path}: {e}")
                continue

        if len(self.files_data) < 2:
            print("Need at least 2 valid files to compare")
            return

        # Find common structure
        all_params = set()
        for data in self.files_data.values():
            all_params.update(data["parameters"].keys())
        self.common_structure = all_params

        # Identify differences
        self._find_differences()

    def _find_differences(self) -> None:
        """Find differences between files."""
        file_names = list(self.files_data.keys())

        # Compare timestamps
        timestamps = {}
        for name, data in self.files_data.items():
            if data["timestamp"]:
                timestamps[name] = data["timestamp"]

        if len(set(timestamps.values())) > 1:
            self.differences["timestamps"] = timestamps

        # Compare versions
        versions = {}
        for name, data in self.files_data.items():
            if data["version"]:
                versions[name] = data["version"]

        if len(set(versions.values())) > 1:
            self.differences["versions"] = versions

        # Compare parameters
        param_diffs = defaultdict(dict)
        for param in self.common_structure:
            values = {}
            for name, data in self.files_data.items():
                values[name] = data["parameters"].get(param, "<missing>")

            # Check if all values are the same
            unique_values = set(values.values())
            if len(unique_values) > 1:
                param_diffs[param] = values

        if param_diffs:
            self.differences["parameters"] = dict(param_diffs)

        # Compare file sizes and line counts
        file_stats = {}
        for name, data in self.files_data.items():
            file_stats[name] = {
                "lines": len(data["lines"]),
                "size_bytes": os.path.getsize(data["file_path"]),
                "parameters": len(data["parameters"]),
            }
        self.differences["file_stats"] = file_stats

    def format_timestamp(self, timestamp: int) -> str:
        """Convert Unix timestamp to readable format."""
        try:
            return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        except:
            return str(timestamp)

    def print_summary(self) -> None:
        """Print a comprehensive summary of the analysis."""
        print("\n" + "=" * 80)
        print("RPP FILE DIFFERENCE ANALYSIS SUMMARY")
        print("=" * 80)

        # File overview
        print(f"\nFiles analyzed: {len(self.files_data)}")
        for name, data in self.files_data.items():
            print(
                f"  • {name} ({data['version'] if data['version'] else 'unknown version'})"
            )

        # File statistics
        if "file_stats" in self.differences:
            print(f"\nFILE STATISTICS:")
            stats = self.differences["file_stats"]
            print(f"{'File':<15} {'Lines':<8} {'Size (bytes)':<12} {'Parameters':<12}")
            print("-" * 50)
            for name, stat in stats.items():
                print(
                    f"{name:<15} {stat['lines']:<8} {stat['size_bytes']:<12} {stat['parameters']:<12}"
                )

        # Timestamp differences
        if "timestamps" in self.differences:
            print(f"\nTIMESTAMP DIFFERENCES:")
            for name, timestamp in self.differences["timestamps"].items():
                print(
                    f"  {name}: {self.format_timestamp(timestamp)} (raw: {timestamp})"
                )

        # Version differences
        if "versions" in self.differences:
            print(f"\nVERSION DIFFERENCES:")
            for name, version in self.differences["versions"].items():
                print(f"  {name}: {version}")

        # Parameter differences
        if "parameters" in self.differences:
            param_count = len(self.differences["parameters"])
            print(f"\nPARAMETER DIFFERENCES: {param_count} parameters differ")

            if param_count <= 20:  # Show all if reasonable number
                for param, values in self.differences["parameters"].items():
                    print(f"\n  {param}:")
                    for name, value in values.items():
                        print(f"    {name}: {value}")
            else:
                print("  (Too many to display - showing first 10)")
                for i, (param, values) in enumerate(
                    self.differences["parameters"].items()
                ):
                    if i >= 10:
                        break
                    print(f"\n  {param}:")
                    for name, value in values.items():
                        print(f"    {name}: {value}")

        # Summary
        total_diffs = sum(
            [
                1 if "timestamps" in self.differences else 0,
                1 if "versions" in self.differences else 0,
                len(self.differences.get("parameters", {})),
            ]
        )

        print(f"\n" + "-" * 80)
        if total_diffs == 0:
            print("RESULT: Files are identical (excluding timestamps)")
        else:
            print(f"RESULT: Found {total_diffs} differences between files")

    def save_detailed_report(self, output_file: str) -> None:
        """Save a detailed report to a file."""
        with open(output_file, "w") as f:
            f.write("RPP FILE DIFFERENCE ANALYSIS - DETAILED REPORT\n")
            f.write("=" * 60 + "\n\n")

            # Write all differences in detail
            for diff_type, diff_data in self.differences.items():
                f.write(f"{diff_type.upper()}:\n")
                if isinstance(diff_data, dict):
                    for key, value in diff_data.items():
                        f.write(f"  {key}: {value}\n")
                f.write("\n")

        print(f"Detailed report saved to: {output_file}")


def main():
    """Main function to run the RPP analyzer."""
    parser = argparse.ArgumentParser(
        description="Analyze differences between REAPER project files"
    )
    parser.add_argument("files", nargs="+", help="RPP files to compare")
    parser.add_argument("--output", "-o", help="Save detailed report to file")
    parser.add_argument("--quiet", "-q", action="store_true", help="Minimal output")

    args = parser.parse_args()

    if len(args.files) < 2:
        print("Error: Need at least 2 files to compare")
        return 1

    analyzer = RPPAnalyzer()

    try:
        analyzer.analyze_files(args.files)

        if not args.quiet:
            analyzer.print_summary()

        if args.output:
            analyzer.save_detailed_report(args.output)

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    # If run directly, analyze the empty RPP files in the data directory
    import sys

    if len(sys.argv) == 1:
        # Default behavior - analyze the empty files
        data_dir = "data"
        files = [
            os.path.join(data_dir, "empty0.RPP"),
            os.path.join(data_dir, "empty1.RPP"),
            os.path.join(data_dir, "empty2.RPP"),
        ]

        print("No arguments provided. Analyzing default empty RPP files...")
        analyzer = RPPAnalyzer()
        analyzer.analyze_files(files)
        analyzer.print_summary()
    else:
        exit(main())
