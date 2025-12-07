# grug for Python

This repository provides Python bindings, a frontend, and a backend for [grug](https://github.com/grug-lang/grug).

## Dependencies

This project requires Python version >=3.11. You can manage Python versions using [pyenv](https://github.com/pyenv/pyenv).

```sh
pip install pytest
pip install -e .
```

## Running the tests

You will need to clone the [grug-tests](https://github.com/grug-lang/grug-tests) repository *next* to this repository, and then run `git checkout development` in it, followed by `./tests.sh`.

In this grug-for-python repository, you can then run all tests using this command:

```sh
pytest --grug-tests-path=../grug-tests -s
```

You can additionally pass `--whitelisted-test=f32_too_big` if you only want to run the test called `f32_too_big`.

Alternatively, you can *walk* through the tests and set breakpoints by installing the [Python Debugger](https://marketplace.visualstudio.com/items?itemName=ms-python.debugpy) VS Code extension. Hit `F5` to run all tests. You can edit `.vscode/launch.json` if you want to pass `--whitelisted-test=f32_too_big`.
