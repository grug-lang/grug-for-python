# grug for Python

This repository provides Python bindings, a frontend, and a backend for [grug](https://github.com/grug-lang/grug).

## Dependencies

This project requires Python version >=3.11. You can manage Python versions using [pyenv](https://github.com/pyenv/pyenv).

```sh
pip install pytest
pip install -e .
```

## Running the tests

You can run the tests with this command:

```sh
pytest --grug-tests-path=../grug-tests -s
```

You can additionally pass `--whitelisted-test=f32_too_big` if you only want to run the test called `f32_too_big`.

Alternatively you can walk through the tests by installing the [Python Debugger](https://marketplace.visualstudio.com/items?itemName=ms-python.debugpy) VS Code extension, and hitting `F5` to launch all tests. You can edit `.vscode/launch.json` to pass `--whitelisted-test=f32_too_big`.
