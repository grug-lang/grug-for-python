#!/usr/bin/env python3

import sys

import atheris  # type: ignore

with atheris.instrument_imports():  # type: ignore
    from grug.tokenizer import Tokenizer, TokenizerError


@atheris.instrument_func  # type: ignore
def test_one_input(bytes: bytes):
    try:
        text = bytes.decode()
    except UnicodeDecodeError:
        return

    try:
        tokens = Tokenizer(text).tokenize()
        _ = tokens
    except TokenizerError:
        pass


def main():
    atheris.Setup(sys.argv, test_one_input) # type: ignore
    atheris.Fuzz() # type: ignore


if __name__ == "__main__":
    main()
