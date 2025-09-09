#!/usr/bin/env python3
"""
ArtifactManager for organizing experiment results with proper structure.

Manages the complete lifecycle of experiment artifacts:
- Target audio and features
- Generation-based organization
- Post-REAPER artifact copying and organization
"""

import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import time

logger = logging.getLogger(__name__)


class ArtifactManager:
    """
    Manages experiment artifacts with proper directory structure outside REAPER.
    
    Structure:
    autodaw/experiment_results/
      <experiment_name>/
        target/
          reference.wav
          features.json
        generation_001/
          individuals/
            individual_000.wav
            individual_001.wav
            ...
          session_config.json
          generation_stats.json
        generation_002/
          ...
        experiment_log.txt
        fitness_log.csv
    """
    
    def __init__(self, experiment_name: str, base_dir: Optional[Path] = None):
        """
        Initialize artifact manager for an experiment.
        
        Args:
            experiment_name: Unique name for this experiment
            base_dir: Base directory for all experiments (defaults to ./experiment_results)
        """
        self.experiment_name = experiment_name
        
        if base_dir is None:
            base_dir = Path(__file__).parent / "experiment_results"
        
        self.base_dir = Path(base_dir)
        self.experiment_dir = self.base_dir / experiment_name
        
        # Create experiment directory structure
        self.experiment_dir.mkdir(parents=True, exist_ok=True)
        self.target_dir = self.experiment_dir / "target"
        self.target_dir.mkdir(exist_ok=True)
        
        # Initialize logging
        self.experiment_log = self.experiment_dir / "experiment_log.txt"
        self.fitness_log = self.experiment_dir / "fitness_log.csv"
        
        # Initialize fitness log with header
        if not self.fitness_log.exists():
            with open(self.fitness_log, 'w') as f:
                f.write("generation,individual,fitness,parameters\n")
        
        logger.info(f"Initialized ArtifactManager for experiment: {experiment_name}")
        logger.info(f"Experiment directory: {self.experiment_dir}")
    
    def set_target_audio(self, target_audio_path: Path, target_features: Optional[Dict] = None) -> Path:
        """
        Set the target reference audio for the experiment.
        
        Args:
            target_audio_path: Path to reference audio file
            target_features: Optional dictionary of extracted features
            
        Returns:
            Path to copied target audio in experiment directory
        """
        if not target_audio_path.exists():
            raise FileNotFoundError(f"Target audio not found: {target_audio_path}")
        
        # Copy target audio to experiment directory
        target_dest = self.target_dir / "reference.wav"
        shutil.copy2(target_audio_path, target_dest)
        
        # Save target features if provided
        if target_features:
            features_path = self.target_dir / "features.json"
            with open(features_path, 'w') as f:
                json.dump(target_features, f, indent=2)
        
        self._log(f"Set target audio: {target_audio_path} -> {target_dest}")
        return target_dest
    
    def create_generation_dir(self, generation: int) -> Path:
        """
        Create directory structure for a generation.
        
        Args:
            generation: Generation number (1-based)
            
        Returns:
            Path to generation directory
        """
        gen_dir = self.experiment_dir / f"generation_{generation:03d}"
        gen_dir.mkdir(exist_ok=True)
        
        # Create individuals subdirectory
        individuals_dir = gen_dir / "individuals"
        individuals_dir.mkdir(exist_ok=True)
        
        self._log(f"Created generation directory: {gen_dir}")
        return gen_dir
    
    def collect_reaper_artifacts(self, generation: int, reaper_renders_dir: Path, 
                                session_config_path: Path) -> Tuple[int, List[Path]]:
        """
        Collect and organize artifacts from REAPER renders directory.
        
        Args:
            generation: Generation number
            reaper_renders_dir: REAPER's renders directory to search
            session_config_path: Path to the session configuration used
            
        Returns:
            Tuple of (num_collected, list_of_individual_audio_paths)
        """
        gen_dir = self.create_generation_dir(generation)
        individuals_dir = gen_dir / "individuals"
        
        # Copy session config to generation directory
        if session_config_path.exists():
            session_dest = gen_dir / "session_config.json"
            shutil.copy2(session_config_path, session_dest)
        
        # Find and collect rendered audio files from REAPER
        collected_audio = []
        
        # Look for any WAV files in REAPER renders directory
        # Pattern: look for recently created wav files
        wav_files = list(reaper_renders_dir.glob("**/*.wav"))
        
        # Sort by modification time (newest first) to get recent renders
        wav_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        individual_count = 0
        generation_timestamp = time.time()
        
        for wav_file in wav_files:
            # Check if file was created recently (within last 60 seconds)
            file_age = generation_timestamp - wav_file.stat().st_mtime
            if file_age > 60:  # Skip files older than 60 seconds
                continue
            
            # Copy to individuals directory with proper naming
            individual_dest = individuals_dir / f"individual_{individual_count:03d}.wav"
            shutil.copy2(wav_file, individual_dest)
            collected_audio.append(individual_dest)
            
            individual_count += 1
            self._log(f"Collected individual {individual_count}: {wav_file} -> {individual_dest}")
        
        self._log(f"Generation {generation}: collected {len(collected_audio)} individuals")
        return len(collected_audio), collected_audio
    
    def log_generation_fitness(self, generation: int, individual_fitness: List[Tuple[int, float, Dict]]):
        """
        Log fitness results for a generation.
        
        Args:
            generation: Generation number
            individual_fitness: List of (individual_id, fitness, parameters) tuples
        """
        # Log to CSV file
        with open(self.fitness_log, 'a') as f:
            for individual_id, fitness, params in individual_fitness:
                params_str = json.dumps(params)
                f.write(f"{generation},{individual_id},{fitness},\"{params_str}\"\n")
        
        # Create generation stats
        gen_dir = self.experiment_dir / f"generation_{generation:03d}"
        if gen_dir.exists():
            stats = {
                "generation": generation,
                "timestamp": time.time(),
                "population_size": len(individual_fitness),
                "fitness_stats": {
                    "best": min(fitness for _, fitness, _ in individual_fitness),
                    "worst": max(fitness for _, fitness, _ in individual_fitness),
                    "mean": sum(fitness for _, fitness, _ in individual_fitness) / len(individual_fitness)
                },
                "individuals": [
                    {"id": ind_id, "fitness": fitness, "parameters": params}
                    for ind_id, fitness, params in individual_fitness
                ]
            }
            
            stats_path = gen_dir / "generation_stats.json"
            with open(stats_path, 'w') as f:
                json.dump(stats, f, indent=2)
        
        best_fitness = min(fitness for _, fitness, _ in individual_fitness)
        worst_fitness = max(fitness for _, fitness, _ in individual_fitness)
        self._log(f"Generation {generation} fitness: best={best_fitness:.4f}, worst={worst_fitness:.4f}")
    
    def get_target_audio(self) -> Optional[Path]:
        """
        Get path to target reference audio.
        
        Returns:
            Path to target audio or None if not set
        """
        target_path = self.target_dir / "reference.wav"
        return target_path if target_path.exists() else None
    
    def get_target_features(self) -> Optional[Dict]:
        """
        Get target features if available.
        
        Returns:
            Dictionary of target features or None
        """
        features_path = self.target_dir / "features.json"
        if features_path.exists():
            with open(features_path) as f:
                return json.load(f)
        return None
    
    def get_generation_individuals(self, generation: int) -> List[Path]:
        """
        Get list of individual audio files for a generation.
        
        Args:
            generation: Generation number
            
        Returns:
            List of paths to individual audio files
        """
        individuals_dir = self.experiment_dir / f"generation_{generation:03d}" / "individuals"
        if not individuals_dir.exists():
            return []
        
        return sorted(individuals_dir.glob("individual_*.wav"))
    
    def get_generation_stats(self, generation: int) -> Optional[Dict]:
        """
        Get statistics for a generation.
        
        Args:
            generation: Generation number
            
        Returns:
            Dictionary of generation statistics or None
        """
        stats_path = self.experiment_dir / f"generation_{generation:03d}" / "generation_stats.json"
        if stats_path.exists():
            with open(stats_path) as f:
                return json.load(f)
        return None
    
    def list_experiment_structure(self) -> Dict[str, List[str]]:
        """
        List the complete experiment directory structure.
        
        Returns:
            Dictionary with structure information
        """
        structure = {
            "target": [],
            "generations": [],
            "logs": []
        }
        
        # Target files
        if self.target_dir.exists():
            for item in self.target_dir.iterdir():
                structure["target"].append(str(item.relative_to(self.experiment_dir)))
        
        # Generation directories
        for gen_dir in sorted(self.experiment_dir.glob("generation_*")):
            gen_info = {
                "name": gen_dir.name,
                "individuals": len(list((gen_dir / "individuals").glob("*.wav"))) if (gen_dir / "individuals").exists() else 0,
                "has_stats": (gen_dir / "generation_stats.json").exists(),
                "has_config": (gen_dir / "session_config.json").exists()
            }
            structure["generations"].append(gen_info)
        
        # Log files
        for log_file in [self.experiment_log, self.fitness_log]:
            if log_file.exists():
                structure["logs"].append(str(log_file.relative_to(self.experiment_dir)))
        
        return structure
    
    def cleanup_old_experiments(self, keep_latest: int = 5):
        """
        Clean up old experiment directories, keeping only the latest N.
        
        Args:
            keep_latest: Number of latest experiments to keep
        """
        if not self.base_dir.exists():
            return
        
        # Get all experiment directories sorted by creation time
        exp_dirs = [d for d in self.base_dir.iterdir() if d.is_dir()]
        exp_dirs.sort(key=lambda x: x.stat().st_ctime, reverse=True)
        
        # Remove old experiments
        for old_exp in exp_dirs[keep_latest:]:
            self._log(f"Cleaning up old experiment: {old_exp}")
            shutil.rmtree(old_exp)
    
    def _log(self, message: str):
        """Log message to both logger and experiment log file."""
        logger.info(message)
        
        # Also log to experiment file with timestamp
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(self.experiment_log, 'a') as f:
            f.write(f"{timestamp} - {message}\n")
    
    def __str__(self) -> str:
        """String representation of the artifact manager."""
        return f"ArtifactManager(experiment={self.experiment_name}, dir={self.experiment_dir})"