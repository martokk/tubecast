from typing import Any

import functools
import time
from collections.abc import Callable

from python_fastapi_stack import logger


def log_function_enter_exit(  # type: ignore
    *, entry=True, exit=True
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for logging function calls.

    Args:
        entry: Log the function call.
        exit: Log the function return.

    Returns:
        The decorated function.
    """

    def wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
        name = func.__name__

        @functools.wraps(func)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            if entry:
                logger.debug(f"Entering '{name}' (args={args}, kwargs={kwargs})")
            result: Any = func(*args, **kwargs)
            if exit:
                logger.debug(f"Exiting '{name}' (result={result}, name={name})")
            return result

        return wrapped

    return wrapper


# type: ignore
def timeit(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator for logging the execution time of a function.

    Args:
        func: The function to be decorated.

    Returns:
        The decorated function.
    """

    @functools.wraps(func)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logger.debug("Function '{}' executed in {:f} s", func.__name__, end - start)
        return result

    return wrapped
