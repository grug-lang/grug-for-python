#!/usr/bin/env python3

import argparse
import os
import sys
import tempfile

import atheris  # type: ignore

with atheris.instrument_imports():  # type: ignore
    import grug
    from grug.parser import ParserError
    from grug.tokenizer import TokenizerError
    from grug.type_propagator import TypePropagationError

mod_api_path = None


@atheris.instrument_func  # type: ignore
def test_one_input(input_bytes: bytes):
    try:
        text = input_bytes.decode()
    except UnicodeDecodeError:
        return

    # Create temporary mods directory (auto-cleaned up)
    with tempfile.TemporaryDirectory() as temp_mods_dir_path:
        # Create subdirectory <temp_mods_dir_path>/mymod
        mod_dir = os.path.join(temp_mods_dir_path, "mymod")
        os.makedirs(mod_dir)

        # Put `text` into <temp_mods_dir_path>/mymod/foo-D.grug
        file_path = os.path.join(mod_dir, "foo-D.grug")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)

        try:
            assert mod_api_path
            state = grug.init(
                mod_api_path=mod_api_path,
                mods_dir_path=temp_mods_dir_path,
            )

            file = state.compile_grug_file("mymod/foo-D.grug")

            _ = file

            # TODO: call state.on_a()
        except (TokenizerError, ParserError, TypePropagationError):
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
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mod-api-path",
        required=True,
        help="Path to mod_api.json",
    )

    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run coverage instead of fuzzing",
    )

    args, _ = parser.parse_known_args()

    global mod_api_path
    mod_api_path = args.mod_api_path

    if args.coverage:
        run_coverage()
        return

    atheris.Setup(sys.argv, test_one_input)  # type: ignore
    atheris.Fuzz()  # type: ignore


if __name__ == "__main__":
    main()
