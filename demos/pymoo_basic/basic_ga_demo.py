"""
Basic Genetic Algorithm Demonstration using pymoo
Solves a custom optimization problem with octave/semitone/fine tuning parameters
"""

from pymoo.core.problem import Problem
from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.optimize import minimize
import numpy as np
import random
import time


class Solution:
    def __init__(self, octave: float, semi: float, fine: float):
        self.octave = octave
        self.semi = semi
        self.fine = fine

    def calculate_sum(self):
        return self.octave + 0.01 * self.semi + 0.0001 * self.fine


class CustomTuningProblem(Problem):
    """Custom optimization problem for tuning parameters"""

    def __init__(self, target_value=1.0):
        self.target_value = target_value
        # Define bounds: octave [-2, 2], semi [-50, 50], fine [-100, 100]
        super().__init__(
            n_var=3, n_obj=1, xl=np.array([-2, -50, -100]), xu=np.array([2, 50, 100])
        )

    def _evaluate(self, x, out, *args, **kwargs):
        """Evaluate fitness function: minimize abs(target - sum)"""
        fitness_values = []

        for individual in x:
            octave, semi, fine = individual
            solution = Solution(octave, semi, fine)
            calculated_sum = solution.calculate_sum()
            fitness = abs(self.target_value - calculated_sum)
            fitness_values.append(fitness)

        out["F"] = np.array(fitness_values)


def initialize_random_target():
    """Initialize random seed and generate target value"""
    random.seed(time.time())
    target = random.uniform(-2, 2)
    return target


def display_target_value(target):
    """Display the target value for optimization"""
    print(f"Target value: {target}")


def create_optimization_problem(target):
    """Create the optimization problem with target value"""
    problem = CustomTuningProblem(target_value=target)
    print(
        f"Problem bounds: octave [{problem.xl[0]}, {problem.xu[0]}], "
        f"semi [{problem.xl[1]}, {problem.xu[1]}], "
        f"fine [{problem.xl[2]}, {problem.xu[2]}]"
    )
    return problem


def create_genetic_algorithm():
    """Create and configure the genetic algorithm"""
    algorithm = GA(
        pop_size=100,
        eliminate_duplicates=True,
        verbose=True,
    )
    return algorithm


def run_optimization(problem, algorithm):
    """Execute the genetic algorithm optimization"""
    result = minimize(problem, algorithm, termination=("n_gen", 100))
    return result


def extract_best_solution(result):
    """Extract the best solution from optimization result"""
    best_x = result.X
    octave, semi, fine = best_x
    best_solution = Solution(octave, semi, fine)
    return best_solution, result.F[0]


def display_optimization_results(target, best_solution, best_fitness, result):
    """Display the final optimization results"""
    octave, semi, fine = best_solution.octave, best_solution.semi, best_solution.fine

    print(f"\nResults:")
    print(f"Best solution - Octave: {octave:.4f}, Semi: {semi:.4f}, Fine: {fine:.4f}")
    print(f"Calculated sum: {best_solution.calculate_sum():.6f}")
    print(f"Target value: {target}")
    print(f"Final fitness (error): {best_fitness:.6f}")
    print(f"Function evaluations: {result.algorithm.evaluator.n_eval}")
    print(f"Execution time: {result.exec_time:.3f} seconds")


def run_basic_ga():
    """Run genetic algorithm on custom tuning problem"""
    target = initialize_random_target()
    display_target_value(target)

    problem = create_optimization_problem(target)
    algorithm = create_genetic_algorithm()

    result = run_optimization(problem, algorithm)

    best_solution, best_fitness = extract_best_solution(result)
    display_optimization_results(target, best_solution, best_fitness, result)

    return result


if __name__ == "__main__":
    result = run_basic_ga()
