import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COVERAGE_FILE = ROOT / ".coverage"
RCFILE = ROOT / ".coveragerc"

COVERAGE_BASE_CMD = [
    "coverage",
    "run",
    "--append",
    f"--data-file={COVERAGE_FILE}",
    f"--rcfile={RCFILE}",
]


def run_examples():
    examples_path = ROOT / "examples"
    for example in examples_path.glob("*/example.py"):
        example_dir = example.parent
        print(f"\nRunning {example_dir}...")

        # Use Popen to control the termination sequence,
        # since subprocess.run(timeout=3) doesn't output coverage
        with subprocess.Popen(
            [*COVERAGE_BASE_CMD, example.name], cwd=example_dir
        ) as proc:
            try:
                proc.communicate(timeout=1)
            except subprocess.TimeoutExpired:
                # Send SIGTERM instead of the uncatchable SIGKILL
                proc.terminate()
                # Wait for the process to execute its cleanup routines and exit
                proc.communicate()


def run_package_tests():
    tests_path = ROOT / "src/grug/packages"
    for test_file in tests_path.glob("**/tests/tests.py"):
        test_dir = test_file.parent
        print(f"\nRunning {test_dir}...")
        subprocess.run(
            [*COVERAGE_BASE_CMD, test_file.name],
            cwd=test_dir,
            check=True,
        )


def run_coverage_tests():
    coverage_tests_path = ROOT / "tests/test_coverage.py"
    if coverage_tests_path.exists():
        print(f"\nRunning coverage tests...")
        subprocess.run(
            [*COVERAGE_BASE_CMD, "-m", "pytest", str(coverage_tests_path), "-v"],
            check=True,
        )


if __name__ == "__main__":
    print("Running all example programs and package tests...")
    run_examples()
    run_package_tests()
    run_coverage_tests()
