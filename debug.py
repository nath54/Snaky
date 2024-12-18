import functools


DEBUG_FN_CALL = True


def debug_inspect_fn_call(func):
    """
    A decorator that logs the name of the function being called
    and its arguments.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Log the function name
        print(f"\nCalling function: {func.__name__}")

        # Log positional arguments
        if args:
            print(f"  - Positional arguments: {args}")
        else:
            print("  - No positional arguments.")

        # Log keyword arguments
        if kwargs:
            print(f"  - Keyword arguments: {kwargs}")
        else:
            print("  - No keyword arguments.")

        # Call the original function
        result = func(*args, **kwargs)

        # Log the result
        print(f"  -> Result: {result}")

        return result
    return wrapper