#!/usr/bin/env python3

import os
import sys

import atheris  # type: ignore

with atheris.instrument_imports():  # type: ignore
    from grug.tokenizer import Tokenizer, TokenizerError


@atheris.instrument_func  # type: ignore
def test_one_input(input_bytes: bytes):
    try:
        text = input_bytes.decode()
    except UnicodeDecodeError:
        return

    try:
        tokens = Tokenizer(text).tokenize()
        _ = tokens
    except TokenizerError:
        pass


def run_coverage():
    """Manually executes the target against the corpus for coverage collection."""
    corpus_dir = "minimized_corpus"
    if not os.path.exists(corpus_dir):
        print(f"Error: {corpus_dir} directory not found.")
        sys.exit(1)

    print(f"Running coverage on files in {corpus_dir}...")
    for filename in os.listdir(corpus_dir):
        filepath = os.path.join(corpus_dir, filename)
        if os.path.isfile(filepath):
            with open(filepath, "rb") as f:
                test_one_input(f.read())
    print("Done.")


def main():
    # Check for our custom coverage flag
    if "--coverage" in sys.argv:
        run_coverage()
        return

    # Otherwise, proceed with standard Atheris fuzzing
    # Note: Atheris consumes arguments it recognizes from sys.argv
    atheris.Setup(sys.argv, test_one_input)  # type: ignore
    atheris.Fuzz()  # type: ignore


if __name__ == "__main__":
    main()
