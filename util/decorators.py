import time
from loguru import logger


def func_time(func):
    """Measure execution time of a method/function"""

    def wrapper(*args, **kwargs):
        t = time.time()
        res = func(*args, **kwargs)
        logger.info(f"executed in {time.time() - t} s.")
        return res

    return wrapper
