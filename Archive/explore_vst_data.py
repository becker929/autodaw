import rpp
import base64
import struct
import json


def explore_vst_data():
    with open("data/serum_init.RPP") as f:
        project = rpp.load(f)

    # Find the track with the VST
    track = None
    for element in project.children:
        if hasattr(element, "tag") and element.tag == "TRACK":
            track = element
            break

    if not track:
        print("No track found")
        return

    # Find the FX chain
    fxchain = None
    for element in track.children:
        if hasattr(element, "tag") and element.tag == "FXCHAIN":
            fxchain = element
            break

    if not fxchain:
        print("No FX chain found")
        return

    # Find the VST
    vst = None
    for element in fxchain.children:
        if hasattr(element, "tag") and element.tag == "VST":
            vst = element
            break

    if not vst:
        print("No VST found")
        return

    print("VST found!")
    print("VST attributes:", vst.attrib)
    print("VST has", len(vst.children), "data chunks")

    # The VST data is typically in the children as base64 encoded strings
    for i, child in enumerate(vst.children):
        if isinstance(child, str):
            print(f"\nChunk {i}: {len(child)} characters")
            print(f"First 100 chars: {child[:100]}...")

            # Try to decode base64
            try:
                decoded = base64.b64decode(child)
                print(f"Decoded to {len(decoded)} bytes")

                # Show first 32 bytes as hex
                hex_data = " ".join(f"{b:02x}" for b in decoded[:32])
                print(f"First 32 bytes (hex): {hex_data}")

                # Try to find patterns that might be parameter data
                if len(decoded) > 100:  # Only analyze larger chunks
                    print(f"Analyzing chunk {i} for parameter patterns...")
                    analyze_parameter_data(decoded, i)

            except Exception as e:
                print(f"Failed to decode base64: {e}")


def analyze_parameter_data(data, chunk_index):
    """Look for floating point values that might be parameters"""
    # Try to interpret as floats (4 bytes each)
    if len(data) % 4 == 0:
        float_count = len(data) // 4
        print(f"  Could contain {float_count} 32-bit floats")

        # Extract first 20 floats to see if they look like parameter values (0-1 range)
        floats = []
        for i in range(min(20, float_count)):
            try:
                # Try both little-endian and big-endian
                float_le = struct.unpack("<f", data[i * 4 : (i + 1) * 4])[0]
                float_be = struct.unpack(">f", data[i * 4 : (i + 1) * 4])[0]
                floats.append((float_le, float_be))
            except:
                continue

        print(f"  First 10 float interpretations (little-endian, big-endian):")
        for i, (le, be) in enumerate(floats[:10]):
            print(f"    {i:2d}: {le:8.4f}, {be:8.4f}")

    # Look for specific byte patterns that might indicate parameter sections
    # Many VSTs store parameters as consecutive floats
    print(f"  Looking for parameter-like patterns in chunk {chunk_index}...")

    # Search for sequences of bytes that could be normalized parameter values
    potential_params = []
    for i in range(0, len(data) - 4, 4):
        try:
            val = struct.unpack("<f", data[i : i + 4])[0]
            # Check if it's in a reasonable parameter range (0-1 or -1 to 1)
            if 0.0 <= val <= 1.0 or -1.0 <= val <= 1.0:
                potential_params.append((i, val))
        except:
            continue

    if potential_params:
        print(
            f"  Found {len(potential_params)} potential parameter values (0-1 range):"
        )
        for i, (offset, val) in enumerate(potential_params[:20]):  # Show first 20
            print(f"    Offset {offset:4d}: {val:.6f}")


if __name__ == "__main__":
    explore_vst_data()
