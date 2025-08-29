#!/usr/bin/env python3
"""
Script to analyze differences between VST data files
Focuses on detecting changes in binary data patterns
"""

import base64
import json
import difflib
from typing import Dict, List, Tuple, Optional
import sys
import os

def decode_base64_line(line: str) -> Tuple[bytes, str]:
    """Decode a base64 line and return both raw bytes and hex representation"""
    line = line.strip().strip("'")
    try:
        raw_bytes = base64.b64decode(line)
        hex_repr = raw_bytes.hex()
        return raw_bytes, hex_repr
    except Exception as e:
        return b'', f"ERROR: {e}"

def analyze_vst_file(filepath: str) -> Dict:
    """Analyze a VST data file and return structured data"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line.strip().strip("'") for line in f.readlines() if line.strip()]

    analysis = {
        'filepath': filepath,
        'total_lines': len(lines),
        'decoded_lines': [],
        'patterns': {},
        'text_content': []
    }

    for i, line in enumerate(lines, 1):
        if not line:
            continue

        raw_bytes, hex_repr = decode_base64_line(line)

        # Try to find text content
        text_content = ""
        try:
            # Look for readable ASCII strings
            decoded = raw_bytes.decode('utf-8', errors='ignore')
            readable_parts = [part for part in decoded if part.isprintable()]
            if len(readable_parts) > 3:  # If we have substantial readable content
                text_content = ''.join(readable_parts)
        except:
            pass

        line_data = {
            'line_number': i,
            'original': line,
            'length': len(line),
            'raw_bytes_length': len(raw_bytes),
            'hex': hex_repr,
            'text_content': text_content
        }

        analysis['decoded_lines'].append(line_data)

        # Look for specific patterns
        if "prog" in text_content.lower():
            analysis['text_content'].append(f"Line {i}: {text_content}")

        # Detect repeating patterns in hex
        if len(hex_repr) > 20:
            # Look for 4-byte patterns that repeat
            for j in range(0, len(hex_repr) - 8, 8):
                pattern = hex_repr[j:j+8]
                count = hex_repr.count(pattern)
                if count > 3:  # Significant repetition
                    if pattern not in analysis['patterns']:
                        analysis['patterns'][pattern] = {'count': count, 'lines': []}
                    if i not in analysis['patterns'][pattern]['lines']:
                        analysis['patterns'][pattern]['lines'].append(i)

    return analysis

def compare_vst_files(file1_path: str, file2_path: str, output_path: str = None) -> Dict:
    """Compare two VST data files and identify differences"""
    print(f"Analyzing {file1_path}...")
    analysis1 = analyze_vst_file(file1_path)

    print(f"Analyzing {file2_path}...")
    analysis2 = analyze_vst_file(file2_path)

    comparison = {
        'file1': analysis1['filepath'],
        'file2': analysis2['filepath'],
        'line_count_diff': analysis2['total_lines'] - analysis1['total_lines'],
        'changed_lines': [],
        'new_lines': [],
        'removed_lines': [],
        'pattern_changes': {},
        'text_changes': []
    }

    # Compare line by line
    max_lines = max(len(analysis1['decoded_lines']), len(analysis2['decoded_lines']))

    for i in range(max_lines):
        line1 = analysis1['decoded_lines'][i] if i < len(analysis1['decoded_lines']) else None
        line2 = analysis2['decoded_lines'][i] if i < len(analysis2['decoded_lines']) else None

        if line1 is None:
            comparison['new_lines'].append(line2)
        elif line2 is None:
            comparison['removed_lines'].append(line1)
        elif line1['hex'] != line2['hex']:
            # Find specific byte differences
            hex1, hex2 = line1['hex'], line2['hex']
            byte_diffs = []

            min_len = min(len(hex1), len(hex2))
            for j in range(0, min_len, 2):
                byte1 = hex1[j:j+2] if j+1 < len(hex1) else hex1[j:]
                byte2 = hex2[j:j+2] if j+1 < len(hex2) else hex2[j:]
                if byte1 != byte2:
                    byte_diffs.append({
                        'position': j//2,
                        'old_byte': byte1,
                        'new_byte': byte2,
                        'old_decimal': int(byte1, 16) if len(byte1) == 2 else None,
                        'new_decimal': int(byte2, 16) if len(byte2) == 2 else None
                    })

            comparison['changed_lines'].append({
                'line_number': i + 1,
                'old_line': line1,
                'new_line': line2,
                'byte_differences': byte_diffs,
                'total_byte_changes': len(byte_diffs)
            })

    # Compare text content
    text1 = analysis1['text_content']
    text2 = analysis2['text_content']

    if text1 != text2:
        comparison['text_changes'] = {
            'old_text': text1,
            'new_text': text2,
            'diff': list(difflib.unified_diff(text1, text2, lineterm=''))
        }

    # Compare patterns
    patterns1 = set(analysis1['patterns'].keys())
    patterns2 = set(analysis2['patterns'].keys())

    comparison['pattern_changes'] = {
        'new_patterns': list(patterns2 - patterns1),
        'removed_patterns': list(patterns1 - patterns2),
        'changed_frequency': {}
    }

    for pattern in patterns1 & patterns2:
        freq1 = analysis1['patterns'][pattern]['count']
        freq2 = analysis2['patterns'][pattern]['count']
        if freq1 != freq2:
            comparison['pattern_changes']['changed_frequency'][pattern] = {
                'old_count': freq1,
                'new_count': freq2,
                'difference': freq2 - freq1
            }

    # Save detailed comparison
    if output_path:
        with open(output_path, 'w') as f:
            json.dump(comparison, f, indent=2)
        print(f"Detailed comparison saved to {output_path}")

    return comparison

def print_summary(comparison: Dict):
    """Print a human-readable summary of the comparison"""
    print("\n" + "="*60)
    print("VST DATA COMPARISON SUMMARY")
    print("="*60)

    print(f"File 1: {comparison['file1']}")
    print(f"File 2: {comparison['file2']}")
    print(f"Line count difference: {comparison['line_count_diff']}")

    if comparison['changed_lines']:
        print(f"\nCHANGED LINES: {len(comparison['changed_lines'])}")
        for change in comparison['changed_lines'][:5]:  # Show first 5
            line_num = change['line_number']
            byte_changes = change['total_byte_changes']
            print(f"  Line {line_num}: {byte_changes} byte(s) changed")

            # Show specific byte changes
            for diff in change['byte_differences'][:3]:  # Show first 3 byte changes
                pos = diff['position']
                old_val = diff['old_decimal']
                new_val = diff['new_decimal']
                if old_val is not None and new_val is not None:
                    print(f"    Byte {pos}: {old_val} -> {new_val} (change: {new_val - old_val})")

        if len(comparison['changed_lines']) > 5:
            print(f"  ... and {len(comparison['changed_lines']) - 5} more changed lines")

    if comparison['new_lines']:
        print(f"\nNEW LINES: {len(comparison['new_lines'])}")

    if comparison['removed_lines']:
        print(f"REMOVED LINES: {len(comparison['removed_lines'])}")

    if comparison['text_changes']:
        print(f"\nTEXT CONTENT CHANGES:")
        print("Old text:", comparison['text_changes']['old_text'])
        print("New text:", comparison['text_changes']['new_text'])

    if comparison['pattern_changes']['new_patterns']:
        print(f"\nNEW PATTERNS: {comparison['pattern_changes']['new_patterns']}")

    if comparison['pattern_changes']['removed_patterns']:
        print(f"REMOVED PATTERNS: {comparison['pattern_changes']['removed_patterns']}")

    if comparison['pattern_changes']['changed_frequency']:
        print(f"\nPATTERN FREQUENCY CHANGES:")
        for pattern, change in comparison['pattern_changes']['changed_frequency'].items():
            print(f"  {pattern}: {change['old_count']} -> {change['new_count']} ({change['difference']:+d})")

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 diff_analyzer.py <file1> <file2> [output_json]")
        print("Example: python3 diff_analyzer.py vst-data.txt vst-data-new.txt comparison.json")
        return

    file1 = sys.argv[1]
    file2 = sys.argv[2]
    output_json = sys.argv[3] if len(sys.argv) > 3 else None

    if not os.path.exists(file1):
        print(f"Error: {file1} not found")
        return

    if not os.path.exists(file2):
        print(f"Error: {file2} not found")
        return

    comparison = compare_vst_files(file1, file2, output_json)
    print_summary(comparison)

if __name__ == "__main__":
    main()
