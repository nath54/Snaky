import inspect
from functools import wraps
import functools


DEBUG_FN_CALL = True


# def debug_inspect_fn_call(func):
#     """
#     Decorator to print function call details.

#     This includes parameters names and effective values.
#     """

#     @wraps(func)
#     def wrapper(*args, **kwargs):
#         if DEBUG_FN_CALL:
#             func_args = inspect.signature(func).bind(*args, **kwargs).arguments
#             func_args_str = ", ".join(map("{0[0]} = {0[1]!r}".format, func_args.items()))
#             print(f"{func.__module__}.{func.__qualname__} ( {func_args_str} )")
#         return func(*args, **kwargs)

#     return wrapper

# def debug_inspect_fn_call(func):
#     '''Decorator to print function call details - parameters names and effective values'''
#     def wrapper(*func_args, **func_kwargs):
#         if DEBUG_FN_CALL:
#             arg_names = func.__code__.co_varnames[:func.__code__.co_argcount]
#             args = func_args[:len(arg_names)]
#             defaults = func.__defaults__ or ()
#             args = args + defaults[len(defaults) - (func.__code__.co_argcount - len(args)):]
#             params = list(zip(arg_names, args))
#             args = func_args[len(arg_names):]
#             if args: params.append(('args', args))
#             if func_kwargs: params.append(('kwargs', func_kwargs))
#             print(func.__name__ + ' (' + ', '.join('%s = %r' % p for p in params) + ' )')
#         return func(*func_args, **func_kwargs)
#     return wrapper


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