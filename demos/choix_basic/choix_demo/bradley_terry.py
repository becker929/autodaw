"""Bradley-Terry algorithm implementation and demonstration."""

import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Any
import choix


class BradleyTerryDemo:
    """Demonstrates the Bradley-Terry model for pairwise comparisons."""

    def __init__(self, n_items: int = 5, random_seed: int = 42):
        """Initialize the Bradley-Terry demonstration.

        Args:
            n_items: Number of items to compare
            random_seed: Random seed for reproducibility
        """
        self.n_items = n_items
        self.random_seed = random_seed
        np.random.seed(random_seed)

        # True underlying strengths (unknown in practice)
        self.true_strengths = np.random.exponential(1.0, n_items)
        self.true_strengths = np.sort(self.true_strengths)[::-1]  # Sort descending

        # Item names
        self.item_names = [f"Item_{i:02d}" for i in range(n_items)]

        # Store comparisons and results
        self.comparisons = []
        self.estimated_strengths = None

    def generate_comparison_data(self, n_comparisons: int = 100) -> List[Tuple[int, int, int]]:
        """Generate simulated pairwise comparison data.

        Args:
            n_comparisons: Number of comparisons to generate

        Returns:
            List of (winner, loser, margin) tuples
        """
        comparisons = []

        for _ in range(n_comparisons):
            # Randomly select two different items
            i, j = np.random.choice(self.n_items, size=2, replace=False)

            # Bradley-Terry probability that item i beats item j
            prob_i_wins = self.true_strengths[i] / (self.true_strengths[i] + self.true_strengths[j])

            # Simulate the outcome
            if np.random.random() < prob_i_wins:
                winner, loser = i, j
            else:
                winner, loser = j, i

            # Add some noise to the margin (not used in basic BT model)
            margin = 1

            comparisons.append((winner, loser, margin))

        self.comparisons = comparisons
        return comparisons

    def fit_bradley_terry_model(self) -> np.ndarray:
        """Fit the Bradley-Terry model to the comparison data.

        Returns:
            Estimated item strengths
        """
        if not self.comparisons:
            raise ValueError("No comparison data available. Call generate_comparison_data() first.")

        # Convert comparisons to format expected by choix
        data = [(winner, loser) for winner, loser, _ in self.comparisons]

        # Fit the Bradley-Terry model
        self.estimated_strengths = choix.ilsr_pairwise(self.n_items, data)

        return self.estimated_strengths

    def get_rankings(self) -> Dict[str, Any]:
        """Get rankings based on true and estimated strengths.

        Returns:
            Dictionary containing true and estimated rankings
        """
        if self.estimated_strengths is None:
            raise ValueError("Model not fitted. Call fit_bradley_terry_model() first.")

        # True ranking (sorted by true strengths)
        true_order = np.argsort(self.true_strengths)[::-1]
        true_ranking = [self.item_names[i] for i in true_order]

        # Estimated ranking (sorted by estimated strengths)
        estimated_order = np.argsort(self.estimated_strengths)[::-1]
        estimated_ranking = [self.item_names[i] for i in estimated_order]

        return {
            'true_ranking': true_ranking,
            'estimated_ranking': estimated_ranking,
            'true_strengths': self.true_strengths[true_order],
            'estimated_strengths': self.estimated_strengths[estimated_order]
        }

    def get_comparison_matrix(self) -> pd.DataFrame:
        """Get the win-loss matrix from comparisons.

        Returns:
            DataFrame showing wins between items
        """
        matrix = np.zeros((self.n_items, self.n_items), dtype=int)

        for winner, loser, _ in self.comparisons:
            matrix[winner, loser] += 1

        df = pd.DataFrame(matrix,
                         index=self.item_names,
                         columns=self.item_names)
        return df

    def calculate_accuracy_metrics(self) -> Dict[str, float]:
        """Calculate accuracy metrics comparing true vs estimated rankings.

        Returns:
            Dictionary of accuracy metrics
        """
        rankings = self.get_rankings()
        true_ranking = rankings['true_ranking']
        estimated_ranking = rankings['estimated_ranking']

        # Kendall's tau (rank correlation)
        from scipy.stats import kendalltau
        tau, p_value = kendalltau(
            [true_ranking.index(item) for item in self.item_names],
            [estimated_ranking.index(item) for item in self.item_names]
        )

        # Top-k accuracy (how many of top k items are correctly identified)
        top_k_accuracies = {}
        for k in range(1, min(6, self.n_items + 1)):
            true_top_k = set(true_ranking[:k])
            estimated_top_k = set(estimated_ranking[:k])
            accuracy = len(true_top_k & estimated_top_k) / k
            top_k_accuracies[f'top_{k}_accuracy'] = accuracy

        return {
            'kendall_tau': tau,
            'kendall_p_value': p_value,
            **top_k_accuracies
        }

    def run_full_demo(self, n_comparisons: int = 100) -> Dict[str, Any]:
        """Run the complete Bradley-Terry demonstration.

        Args:
            n_comparisons: Number of comparisons to simulate

        Returns:
            Complete results dictionary
        """
        # Generate data and fit model
        self.generate_comparison_data(n_comparisons)
        self.fit_bradley_terry_model()

        # Gather results
        results = {
            'n_items': self.n_items,
            'n_comparisons': n_comparisons,
            'rankings': self.get_rankings(),
            'accuracy_metrics': self.calculate_accuracy_metrics(),
            'comparison_matrix': self.get_comparison_matrix()
        }

        return results
