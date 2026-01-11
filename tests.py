import subprocess
from pathlib import Path


def run_examples():
    for example in Path("examples").glob("*/example.py"):
        example_dir = example.parent
        print(f"\nRunning {example_dir}...")
        try:
            subprocess.run(
                ["python", example.name], cwd=example_dir, timeout=3, check=True
            )
        except subprocess.TimeoutExpired:
            pass


def run_package_tests():
    for test_file in Path("src/grug/packages").glob("**/tests/tests.py"):
        test_dir = test_file.parent
        print(f"\nRunning {test_dir}...")
        subprocess.run(
            ["python", test_file.name],
            cwd=test_dir,
            check=True,
        )


if __name__ == "__main__":
    print("Running all example programs and package tests...")
    run_examples()
    run_package_tests()
