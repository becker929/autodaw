"""Complete demo suite orchestration."""

from pathlib import Path
from typing import Dict, Any

from .demo_runner import DemoRunner, DemoResultsFormatter
from .oracle_accuracy import OracleAccuracyTester
from .implementations import (
    FileSystemProjectValidator,
    StandardOptimizationProblemFactory,
    StandardGAConfigFactory
)
from .oracle_accuracy import StandardOracleFactory


class DemoSuite:
    """Orchestrates the complete demo suite."""

    def __init__(
        self,
        demo_runner: DemoRunner,
        oracle_tester: OracleAccuracyTester,
        formatter: DemoResultsFormatter
    ):
        self.demo_runner = demo_runner
        self.oracle_tester = oracle_tester
        self.formatter = formatter

    def run_complete_suite(self, reaper_project_path: Path) -> Dict[str, Any]:
        """Run the complete demo suite."""
        self.formatter.print_suite_header()

        all_results = {}

        try:
            # JSI Optimization Demo
            self.formatter.print_demo_header("JSI Audio Optimization Demo")
            jsi_results = self.demo_runner.run_jsi_optimization(reaper_project_path)
            all_results['jsi_optimization'] = jsi_results
            print(self.formatter.format_jsi_results(jsi_results))

            # Multi-target Demo
            self.formatter.print_demo_header("Multi-Target JSI Optimization Demo")
            multi_results = self.demo_runner.run_multi_target_optimization(
                reaper_project_path,
                target_frequencies=[220.0, 440.0, 880.0]
            )
            all_results['multi_target_optimization'] = multi_results
            print(self.formatter.format_multi_target_results(multi_results))

            # Oracle Accuracy Demo
            self.formatter.print_demo_header("Comparison Oracle Accuracy Demo")
            oracle_results = self.oracle_tester.test_oracle_accuracy(
                reaper_project_path, n_comparisons=20
            )
            all_results['oracle_accuracy'] = oracle_results
            print(f"Oracle agreement rates: {oracle_results.get('agreement_rates', [])}")

        except Exception as e:
            print(f"Demo suite failed: {e}")
            all_results['error'] = str(e)

        self.formatter.print_suite_footer()
        return all_results


def create_standard_demo_suite() -> DemoSuite:
    """Create a demo suite with standard implementations."""
    # Create dependencies
    validator = FileSystemProjectValidator()
    problem_factory = StandardOptimizationProblemFactory()
    ga_factory = StandardGAConfigFactory()
    oracle_factory = StandardOracleFactory()

    # Create main components
    demo_runner = DemoRunner(validator, problem_factory, ga_factory)
    oracle_tester = OracleAccuracyTester(oracle_factory)
    formatter = DemoResultsFormatter()

    return DemoSuite(demo_runner, oracle_tester, formatter)


def run_full_demo_suite(reaper_project_path: Path) -> Dict[str, Any]:
    """Convenience function to run the complete demo suite."""
    suite = create_standard_demo_suite()
    return suite.run_complete_suite(reaper_project_path)
