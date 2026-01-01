# grug for Python

This repository provides Python bindings, a frontend, and a backend for [grug](https://github.com/grug-lang/grug). It passes all tests in [grug-lang/grug-tests](https://github.com/grug-lang/grug-tests).

Install this package using `pip install grug-lang`, and run `python -c "import grug"` to check that it doesn't print an error.

A minimal example program is provided in the [`examples/minimal/` directory](https://github.com/grug-lang/grug-for-python/tree/main/examples/minimal) on GitHub:

```py
import grug
import time

state = grug.init()

@state.game_fn
def print_string(string: str):
    print(string)

file = state.compile_grug_file("animals/labrador-Dog.grug")
dog1 = file.create_entity()
dog2 = file.create_entity()

while True:
    state.update()
    dog1.on_bark("woof")
    dog2.on_bark("arf")
    time.sleep(1)
```
```py
on_bark(sound: string) {
    print_string(sound)

    # Print "arf" a second time
    if sound == "arf" {
        print_string(sound)
    }
}
```

Run it by cloning the repository, `cd`-ing into it, running `cd examples/minimal`, and finally running `python example.py`.

See the [`examples/` directory](https://github.com/grug-lang/grug-for-python/tree/main/examples) for more interesting programs, like [`examples/using_grug_packages`](https://github.com/grug-lang/grug-for-python/tree/main/examples/using_grug_packages).

## Dependencies

This project requires Python version 3.7 or newer. You can manage your Python versions using [pyenv](https://github.com/pyenv/pyenv).

If you are on a Python version older than 3.11, you will need to install these:

```sh
pip install tomli importlib-metadata
```

If you want to run the tests, you will need to install pytest:

```sh
pip install pytest
pip install -e .
```

## Tests

### Testing grug-lang changes

Either uninstall grug-lang, if you had it installed:
```sh
pip uninstall grug-lang
```
Or set up a virtual environment:
```sh
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
```
And then create an editable install of grug-lang:
```sh
pip install -e .
```

### Building `libtests.so`

1. Clone the [grug-tests](https://github.com/grug-lang/grug-tests) repository *next* to this repository
2. Run `git checkout development` in the `grug-tests` repository.
3. Follow the instructions in the `grug-tests` repository for building `libtests.so`.

### Running tests

In this grug-for-python repository, you can run all tests using this command:

```sh
pytest --grug-tests-path=../grug-tests -s -v
```

Pass `--whitelisted-test=f32_too_big` to only run the test called `f32_too_big`.

Alternatively, you can *walk* through the tests and set breakpoints by installing the [Python Debugger](https://marketplace.visualstudio.com/items?itemName=ms-python.debugpy) VS Code extension. Hit `F5` to run all tests. You can edit `.vscode/launch.json` to pass `--whitelisted-test=f32_too_big`.

## Type checking

1. `pip install -e .[dev]`
2. `pip install pyright[nodejs]`
3. `pyright`

## Updating the pypi package

```sh
python -m pip install --upgrade pip
python -m pip install --upgrade build
python -m build
python -m pip install --upgrade twine
python -m twine upload dist/*
```
