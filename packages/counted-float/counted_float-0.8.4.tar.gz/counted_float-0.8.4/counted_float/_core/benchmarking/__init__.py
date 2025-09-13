from counted_float._core.counting.models import FlopsBenchmarkResults

from ._flops_benchmark_suite import FlopsBenchmarkSuite


def run_flops_benchmark() -> FlopsBenchmarkResults:
    """Run the flops benchmark suite with default settings returns a FlopsBenchmarkResults object."""
    return FlopsBenchmarkSuite().run()
