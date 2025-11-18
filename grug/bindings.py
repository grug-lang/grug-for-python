from pathlib import Path


class Bindings:
    def compile_grug_fn(self, path: str):
        """Read a file and pass its contents to the frontend."""
        from . import Frontend  # TODO: Move this to the top of the file

        try:
            text = Path(path).read_text()
        except Exception as e:
            return f"Error reading file {path}: {e}"

        frontend = Frontend()
        return frontend.compile_grug_fn(text)
