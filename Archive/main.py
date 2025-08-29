import re


def extract_vst_data(rpp_file_path):
    """Extract VST data lines from RPP file"""
    with open(rpp_file_path, "r") as f:
        content = f.read()

    # Find the VST section and extract Base64 lines
    vst_lines = []
    in_vst_section = False

    for line in content.split("\n"):
        line = line.strip()

        if "<VST" in line and "Serum" in line:
            in_vst_section = True
            continue
        elif line == ">":
            in_vst_section = False
            continue
        elif in_vst_section and line:
            # Skip non-Base64 lines
            if (
                not line.startswith("PRESETNAME")
                and not line.startswith("FLOATPOS")
                and not line.startswith("FXID")
                and not line.startswith("WAK")
            ):
                vst_lines.append(line)

    return vst_lines


def save_vst_data(vst_lines, output_file):
    """Save VST data in the same format as original vst-data.txt"""
    with open(output_file, "w") as f:
        for line in vst_lines:
            f.write(f"'{line}'\n")


# Extract VST data from all project files
project_files = {
    "init": "data/serum_init.RPP",
    "init_2": "data/serum_init_2.RPP",
    "oct_neg1": "data/serum_oct_neg1.RPP",
    "oct_pos2": "data/serum_oct_pos2.RPP",
}

for name, file_path in project_files.items():
    try:
        vst_data = extract_vst_data(file_path)
        output_file = f"data/vst-data-{name}.txt"
        save_vst_data(vst_data, output_file)
        print(f"Extracted {len(vst_data)} lines from {file_path} -> {output_file}")
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

print("\nReady to run diff analysis!")
print(
    "Example: python3 data/diff_analyzer.py data/vst-data-init.txt data/vst-data-oct_pos2.txt"
)
