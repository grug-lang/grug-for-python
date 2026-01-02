import subprocess
from pathlib import Path


def run_examples():
    # Run examples (timeout 3s, ignore exit code)
    for example in Path("examples").glob("*/example.py"):
        example_dir = example.parent
        try:
            subprocess.run(
                ["python", example.name],
                cwd=example_dir,
                timeout=3,
                check=False,  # Ignore exit code
            )
        except subprocess.TimeoutExpired:
            pass


def run_tests():
    # Run package tests
    for test_file in Path("src/grug/packages").glob("**/tests/tests.py"):
        test_dir = test_file.parent
        subprocess.run(
            ["python", test_file.name],
            cwd=test_dir,
            check=True,
        )


if __name__ == "__main__":
    run_examples()
    run_tests()
