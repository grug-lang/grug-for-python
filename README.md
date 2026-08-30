# grug for Python · ![Coverage](.github/badges/coverage.svg)

This repository provides Python bindings, a frontend, and a backend for [grug](https://github.com/grug-lang/grug). It passes all tests in [grug-lang/grug-tests](https://github.com/grug-lang/grug-tests).

Install this package using `pip install grug-lang`, and run `python -c "import grug"` to check that it works.

A minimal example program is provided in the [`examples/minimal/` directory](https://github.com/grug-lang/grug-for-python/tree/main/examples/minimal) on GitHub:

```py
import time

import grug
from grug import GrugState

state = grug.init()

@state.game_fn
def print_string(state: GrugState, string: str):
    print(string)

file = state.mods["animals"]["labrador-Dog.grug"]

dog1 = file.create_entity()
dog2 = file.create_entity()

while True:
    state.update()
    dog1.bark("woof")
    dog2.bark("arf")
    time.sleep(1)
```
```py
export bark(sound: string) {
    print_string(sound)

    # Print "arf" a second time
    if sound == "arf" {
        print_string(sound)
    }
}
```

Run it by cloning the repository, `cd`-ing into it, running `cd examples/minimal`, and finally running `python example.py`.

See the [`examples/` directory](https://github.com/grug-lang/grug-for-python/tree/main/examples) for more interesting programs, like [`examples/using_grug_packages`](https://github.com/grug-lang/grug-for-python/tree/main/examples/using_grug_packages).

## Static methods

A class or entity can declare `static_methods` in `mod_api.json`. Their receiver
is the type itself rather than a value of it, which is what lets a mod construct
one without a free game function like `vec_number_new()`:

```py
export bark(sound: string) {
    sounds: VecNumber = VecNumber.new()
    sounds.push(1)
}
```

```json
"VecNumber": {
    "description": "A growable list of numbers.",
    "static_methods": {
        "new": {
            "description": "Creates a new empty VecNumber.",
            "parameters": [],
            "return_type": { "name": "VecNumber" }
        }
    }
}
```

Calling a method statically (`VecNumber.push(x)`) and calling a static method on
a value (`x.new()`) are both compile errors, each naming the other spelling. A
class or entity may not declare a method and a static method with the same name,
which is what lets a name alone say which of the two is being registered.

On the Python side, a static method takes the `GrugState` as its first argument,
where a method takes the receiver first and the state second:

```py
@state.grug_class
class VecNumber:
    @staticmethod
    def new(state: GrugState) -> "VecNumber":
        ...

    def push(self, state: GrugState, value: float) -> None:
        ...
```

A *generic* static method has the same Python signature as a generic method, so
it is marked with `@grug.static_method` to say which one is meant. See
[`examples/static_method`](https://github.com/grug-lang/grug-for-python/tree/main/examples/static_method)
for a program using all of these.

## Dependencies

This project requires Python version 3.7 or newer. You can manage your Python versions using [pyenv](https://github.com/pyenv/pyenv).

If you are on a Python version older than 3.11, you will need to install these:

```sh
pip install tomli importlib-metadata
```

If you want to run the tests and check their coverage, you will need to install `pytest` and `coverage`:

```sh
pip install pytest coverage
pip install -e .
```

## Tests

Run `python tests.py` to test all examples and package tests.

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

You can run all tests using this command:

```sh
coverage run -m pytest --grug-tests-path=../grug-tests -s -v && \
python tests.py && \
coverage report -m --skip-covered && \
coverage html
```

Run `python -m http.server` in a different terminal to view the HTML output in your browser.

If you compiled grug-tests with `ASAN=1` in your environment, you need to pass `export LD_PRELOAD=$(gcc -print-file-name=libasan.so) ASAN_OPTIONS="detect_leaks=0"` before you run pytest.

Pass `--whitelisted-test=f32_too_big` to only run the test called `f32_too_big`.

Alternatively, you can *walk* through the tests and set breakpoints by installing the [Python Debugger](https://marketplace.visualstudio.com/items?itemName=ms-python.debugpy) VS Code extension. Hit `F5` to run all tests. You can edit `.vscode/launch.json` to pass `--whitelisted-test=f32_too_big`.

## Benchmarks

After building the grug benchmark library, run the Python benchmark harness with:

```sh
python benchmarks.py --grug-bench-path=../grug-bench 
```

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
