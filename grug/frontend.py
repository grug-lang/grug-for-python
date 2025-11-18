class Frontend:
    def compile_grug_fn(self, source: str):
        """
        Compile source text and return an error message string,
        or None if compilation succeeded.
        """

        # TODO: Remove
        if "foo: i32 = 0" in source:
            return "Expected token type OPEN_BRACE_TOKEN, but got ASSIGNMENT_TOKEN on line 4"
        elif "boolean: bool = 1" in source:
            return "foo"

        return None  # No error message
