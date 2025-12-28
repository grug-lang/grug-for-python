# grug for Python

This repository provides Python bindings, a frontend, and a backend for [grug](https://github.com/grug-lang/grug).

Install this package using `pip install grug-lang`, and run `python -c "import grug"` to check that it doesn't print an error.

A minimal example program is provided in the [`example/` directory](https://github.com/grug-lang/grug-for-python/tree/main/example) on GitHub:

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

Run it by cloning the repository, `cd`-ing into it, running `cd example`, and finally running `python example.py`.

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

Run `pyright` in the terminal to type check the Python code. Pyright can be installed using `sudo npm install -g pyright`.

## Updating the pypi package

```sh
python -m pip install --upgrade pip
python -m pip install --upgrade build
python -m build
python -m pip install --upgrade twine
python -m twine upload dist/*
```
