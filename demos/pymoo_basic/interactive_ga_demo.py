"""
Basic Genetic Algorithm Demonstration using pymoo
Solves a custom optimization problem with octave/semitone/fine tuning parameters
"""

from pymoo.core.problem import Problem
from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.core.population import Population
from pymoo.core.sampling import Sampling
from pymoo.operators.sampling.rnd import FloatRandomSampling
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


class InteractiveTuningProblem(Problem):
    """Interactive optimization problem where user provides fitness manually"""

    def __init__(self, target_value=1.0):
        self.target_value = target_value
        # Define bounds: octave [-2, 2], semi [-50, 50], fine [-100, 100]
        super().__init__(
            n_var=3, n_obj=1, xl=np.array([-2, -50, -100]), xu=np.array([2, 50, 100])
        )

    def _evaluate(self, x, out, *args, **kwargs):
        """Interactive fitness evaluation - user provides distance manually"""
        fitness_values = []

        print(f"\n--- Evaluating {len(x)} individuals ---")
        print(f"Target value: {self.target_value:.6f}")

        for i, individual in enumerate(x):
            octave, semi, fine = individual
            solution = Solution(octave, semi, fine)
            calculated_sum = solution.calculate_sum()

            print(f"\nIndividual {i+1}/{len(x)}:")
            print(f"  Octave: {octave:.4f}, Semi: {semi:.4f}, Fine: {fine:.4f}")
            print(f"  Calculated sum: {calculated_sum:.6f}")
            print(
                f"  Expected distance from target: {abs(self.target_value - calculated_sum):.6f}"
            )

            while True:
                try:
                    user_distance = float(input("Enter the distance you measured: "))
                    if user_distance >= 0:
                        fitness_values.append(user_distance)
                        break
                    else:
                        print("Distance must be non-negative. Please try again.")
                except ValueError:
                    print("Invalid input. Please enter a number.")

        out["F"] = np.array(fitness_values)


def initialize_random_target():
    """Initialize random seed and generate target value"""
    random.seed(time.time())
    target = random.uniform(-2, 2)
    return target


def display_welcome_message(target):
    """Display welcome message and target information"""
    print(f"=== Interactive Genetic Algorithm ===")
    print(f"Target value: {target:.6f}")


def create_problem_and_algorithm(target):
    """Create optimization problem and GA algorithm"""
    problem = InteractiveTuningProblem(target_value=target)
    print(
        f"Problem bounds: octave [{problem.xl[0]}, {problem.xu[0]}], "
        f"semi [{problem.xl[1]}, {problem.xu[1]}], "
        f"fine [{problem.xl[2]}, {problem.xu[2]}]"
    )

    algorithm = GA(
        pop_size=10,  # Smaller population for interactive use
        eliminate_duplicates=True,
        verbose=False,  # We'll handle our own progress display
    )

    algorithm.setup(problem)
    return problem, algorithm


def display_run_parameters(algorithm, max_generations):
    """Display algorithm run parameters"""
    print(
        f"\nRunning for {max_generations} generations with population size {algorithm.pop_size}"
    )
    print("You will be asked to manually evaluate the distance for each individual.")


def initialize_first_population(problem, algorithm):
    """Create initial population for first generation"""
    sampling = FloatRandomSampling()
    return Population.new(X=sampling(problem, algorithm.pop_size).get("X"))


def display_generation_header(generation, max_generations):
    """Display generation header"""
    print(f"\n{'='*50}")
    print(f"GENERATION {generation + 1}/{max_generations}")
    print(f"{'='*50}")


def evaluate_population(algorithm, problem, population):
    """Evaluate population and update algorithm state"""
    algorithm.evaluator.eval(problem, population)
    algorithm.pop = population
    return population


def find_best_individual(population):
    """Find and return the best individual from population"""
    best_idx = np.argmin(population.get("F"))
    return population[best_idx]


def display_generation_summary(generation, best_individual, target):
    """Display summary of current generation"""
    best_x = best_individual.X
    best_f = best_individual.F[0]
    octave, semi, fine = best_x
    best_solution = Solution(octave, semi, fine)

    print(f"\nGeneration {generation + 1} Summary:")
    print(f"Best individual - Octave: {octave:.4f}, Semi: {semi:.4f}, Fine: {fine:.4f}")
    print(f"Calculated sum: {best_solution.calculate_sum():.6f}")
    print(f"User-provided fitness: {best_f:.6f}")
    print(f"Expected fitness: {abs(target - best_solution.calculate_sum()):.6f}")


def advance_to_next_generation(algorithm):
    """Apply genetic operators to create next generation"""
    algorithm.next()


def ask_user_to_continue(generation):
    """Ask user if they want to continue to next generation"""
    continue_choice = (
        input(f"\nContinue to generation {generation + 1}? (y/n): ").lower().strip()
    )
    return continue_choice == "y"


def display_final_results(generation, target, best_individual):
    """Display final optimization results"""
    best_x = best_individual.X
    best_f = best_individual.F[0]
    octave, semi, fine = best_x
    best_solution = Solution(octave, semi, fine)

    print(f"\n{'='*50}")
    print("FINAL RESULTS")
    print(f"{'='*50}")
    print(f"Completed {generation} generations")
    print(f"Target value: {target:.6f}")
    print(f"Best solution found:")
    print(f"  Octave: {octave:.4f}, Semi: {semi:.4f}, Fine: {fine:.4f}")
    print(f"  Calculated sum: {best_solution.calculate_sum():.6f}")
    print(f"  User-provided fitness: {best_f:.6f}")


def run_interactive_ga():
    """Run interactive genetic algorithm with manual fitness evaluation"""
    target = initialize_random_target()
    display_welcome_message(target)

    problem, algorithm = create_problem_and_algorithm(target)

    max_generations = 5
    display_run_parameters(algorithm, max_generations)

    population = initialize_first_population(problem, algorithm)
    generation = 0
    best_individual = None

    while generation < max_generations:
        display_generation_header(generation, max_generations)

        if generation > 0:
            population = algorithm.pop

        population = evaluate_population(algorithm, problem, population)
        best_individual = find_best_individual(population)
        display_generation_summary(generation, best_individual, target)

        generation += 1

        if generation < max_generations:
            if not ask_user_to_continue(generation):
                break
            advance_to_next_generation(algorithm)

    display_final_results(generation, target, best_individual)
    return best_individual


if __name__ == "__main__":
    result = run_interactive_ga()
