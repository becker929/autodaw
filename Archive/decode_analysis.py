#!/usr/bin/env python3
"""
Script to decode vst-data.txt using various encoding methods
"""

import base64
import binascii
import zlib
import gzip
import urllib.parse
import codecs
import json
from typing import List, Tuple, Optional

def read_vst_data(filename: str) -> List[str]:
    """Read the VST data file and return lines as strings"""
    with open(filename, 'r', encoding='utf-8') as f:
        lines = [line.strip().strip("'") for line in f.readlines() if line.strip()]
    return lines

def try_base64_decode(data: str) -> Optional[bytes]:
    """Try to decode as Base64"""
    try:
        return base64.b64decode(data)
    except Exception:
        return None

def try_hex_decode(data: str) -> Optional[bytes]:
    """Try to decode as hexadecimal"""
    try:
        return bytes.fromhex(data)
    except Exception:
        return None

def try_url_decode(data: str) -> Optional[str]:
    """Try to decode as URL encoding"""
    try:
        return urllib.parse.unquote(data)
    except Exception:
        return None

def try_zlib_decompress(data: bytes) -> Optional[bytes]:
    """Try to decompress with zlib"""
    try:
        return zlib.decompress(data)
    except Exception:
        return None

def try_gzip_decompress(data: bytes) -> Optional[bytes]:
    """Try to decompress with gzip"""
    try:
        return gzip.decompress(data)
    except Exception:
        return None

def safe_decode_text(data: bytes, encoding: str = 'utf-8') -> str:
    """Safely decode bytes to text"""
    try:
        return data.decode(encoding)
    except UnicodeDecodeError:
        # Try latin-1 as fallback
        try:
            return data.decode('latin-1')
        except:
            # Return hex representation if all else fails
            return f"[HEX: {data.hex()}]"

def analyze_line(line: str, line_num: int) -> dict:
    """Analyze a single line with various decoding methods"""
    results = {
        'line_number': line_num,
        'original': line,
        'length': len(line),
        'decodings': {}
    }

    # Try Base64 first
    b64_data = try_base64_decode(line)
    if b64_data:
        results['decodings']['base64_raw'] = safe_decode_text(b64_data)
        results['decodings']['base64_hex'] = b64_data.hex()

        # Try compression on base64 decoded data
        zlib_data = try_zlib_decompress(b64_data)
        if zlib_data:
            results['decodings']['base64_zlib'] = safe_decode_text(zlib_data)

        gzip_data = try_gzip_decompress(b64_data)
        if gzip_data:
            results['decodings']['base64_gzip'] = safe_decode_text(gzip_data)

    # Try hex decoding
    hex_data = try_hex_decode(line)
    if hex_data:
        results['decodings']['hex'] = safe_decode_text(hex_data)

    # Try URL decoding
    url_decoded = try_url_decode(line)
    if url_decoded and url_decoded != line:
        results['decodings']['url'] = url_decoded

    return results

def main():
    input_file = '/Users/anthonybecker/Desktop/tmsmsm/autodaw/reaper/data/vst-data.txt'
    lines = read_vst_data(input_file)

    all_results = []

    print(f"Analyzing {len(lines)} lines...")

    for i, line in enumerate(lines, 1):
        if line:  # Skip empty lines
            result = analyze_line(line, i)
            all_results.append(result)

    # Write results to separate files for each encoding type
    encoding_types = ['base64_raw', 'base64_hex', 'base64_zlib', 'base64_gzip', 'hex', 'url']

    for encoding_type in encoding_types:
        output_file = f'/Users/anthonybecker/Desktop/tmsmsm/autodaw/reaper/data/decoded_{encoding_type}.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"=== VST Data Decoded as {encoding_type.upper()} ===\n\n")

            for result in all_results:
                if encoding_type in result['decodings']:
                    f.write(f"Line {result['line_number']} (length: {result['length']}):\n")
                    f.write(f"Original: {result['original'][:100]}{'...' if len(result['original']) > 100 else ''}\n")
                    f.write(f"Decoded:  {result['decodings'][encoding_type]}\n")
                    f.write("-" * 80 + "\n\n")

    # Write comprehensive analysis
    with open('/Users/anthonybecker/Desktop/tmsmsm/autodaw/reaper/data/analysis_summary.json', 'w') as f:
        json.dump(all_results, f, indent=2)

    print("Analysis complete! Files created:")
    for encoding_type in encoding_types:
        print(f"  - decoded_{encoding_type}.txt")
    print("  - analysis_summary.json")

if __name__ == "__main__":
    main()
