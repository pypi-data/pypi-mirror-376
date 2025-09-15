from hjb_solver.imports import inspect, ast, re


def get_return_dict_keys(cls, method_name) -> set[str]:
    """Extract keys from the dictionary returned by a specified method of a class."""
    # Get the source code of the method
    source = inspect.getsource(getattr(cls, method_name))
    # Remove leading spaces to avoid IndentationError
    source = re.sub(r"^\s*def ", "def ", source)
    # Parse the source code into an AST
    tree = ast.parse(source)
    # Traverse the AST to find the return statement
    for node in ast.walk(tree):
        # Look for return statements
        if isinstance(node, ast.Return):
            # Check if the return value is a tuple
            if isinstance(node.value, ast.Tuple):
                # The first element of the tuple is the dictionary
                first = node.value.elts[0]
                # Ensure it's a dictionary and extract keys
                if isinstance(first, ast.Dict):
                    return set(
                        (
                            str(k.value)
                            for k in first.keys
                            if isinstance(k, ast.Constant)
                        )
                    )
    return set()
