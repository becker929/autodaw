import difflib
from typing import List


def compare_strings(str1: str, str2: str):
    """
    Compare two strings using difflib and return differences
    """
    d = difflib.Differ()
    return list(d.compare(str1.splitlines(), str2.splitlines()))


def get_differences(str1: str, str2: str) -> List[str]:
    """
    Get a list of differences between two strings
    """
    diff = compare_strings(str1, str2)
    return [line for line in diff if line.startswith('+ ') or line.startswith('- ')]


def similarity_ratio(str1: str, str2: str) -> float:
    """
    Get similarity ratio between two strings (0.0 to 1.0)
    """
    seq_matcher = difflib.SequenceMatcher(None, str1, str2)
    return seq_matcher.ratio()


if __name__ == "__main__":
    # Example usage
    string1 = "This is a test string for comparison"
    string2 = "This is a test string for comparing"

    # Get full diff with context
    diff = compare_strings(string1, string2)
    print("Full diff with context:")
    for line in diff:
        print(f"  {line}")

    # Get only the differences
    diffs = get_differences(string1, string2)
    print("\nOnly differences:")
    for diff in diffs:
        print(f"  {diff}")

    # Calculate similarity ratio
    ratio = similarity_ratio(string1, string2)
    print(f"\nSimilarity ratio: {ratio:.2f}")

    # Example with file comparison
    print("\nComparing from files:")
    try:
        with open("file1.txt", "r") as f1, open("file2.txt", "r") as f2:
            content1 = f1.read()
            content2 = f2.read()

            diff = compare_strings(content1, content2)
            ratio = similarity_ratio(content1, content2)

            print(f"Similarity ratio: {ratio:.2f}")
            print(f"Number of diff lines: {len(diff)}")
    except FileNotFoundError:
        print("Example files not found. Create file1.txt and file2.txt to test file comparison.")
