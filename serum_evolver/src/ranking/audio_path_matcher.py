"""Audio path matching functionality for GA solutions."""

import re
from pathlib import Path
from typing import Dict, Optional


class AudioPathMatcher:
    """Matches solution IDs to audio file paths."""

    @staticmethod
    def find_matching_audio_path(solution_id: str, audio_paths: Dict[str, Path]) -> Optional[Path]:
        """Find the audio path that matches the given solution ID.

        Args:
            solution_id: ID of the solution to find audio for
            audio_paths: Dictionary mapping identifiers to audio file paths

        Returns:
            Path to matching audio file, or None if not found
        """
        # Direct match
        if solution_id in audio_paths:
            return audio_paths[solution_id]

        # Fuzzy matching - check if solution_id is contained in any path key
        for path_key, path in audio_paths.items():
            if solution_id in path_key or path_key in solution_id:
                return path

        # Try extracting individual number from solution_id
        # Look for patterns like "sol_001", "generation_002", etc.
        match = re.search(r'(\d+)', solution_id)
        if match:
            number = match.group(1)

            # Try to find a path key that contains this number
            for path_key, path in audio_paths.items():
                if number in path_key:
                    return path

        return None

    @staticmethod
    def filter_valid_solutions(solution_ids: list, audio_paths: Dict[str, Path]) -> Dict[str, Path]:
        """Filter solutions that have valid audio paths.

        Args:
            solution_ids: List of solution IDs
            audio_paths: Dictionary of available audio paths

        Returns:
            Dictionary mapping valid solution IDs to their audio paths
        """
        valid_paths = {}

        for sol_id in solution_ids:
            matching_path = AudioPathMatcher.find_matching_audio_path(sol_id, audio_paths)
            if matching_path and matching_path.exists():
                valid_paths[sol_id] = matching_path

        return valid_paths
