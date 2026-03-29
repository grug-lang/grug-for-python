import sys

import atheris

with atheris.instrument_imports():
    from grug.tokenizer import Tokenizer, TokenizerError


@atheris.instrument_func
def test_one_input(bytes):
    try:
        text = bytes.decode()
    except UnicodeDecodeError:
        return

    try:
        tokens = Tokenizer(text).tokenize()
    except TokenizerError:
        pass


def main():
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
