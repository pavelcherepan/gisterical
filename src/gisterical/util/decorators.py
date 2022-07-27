import time
from loguru import logger


def func_time(func):
    """Measure execution time of a method/function"""
    def wrapper(*args, **kwargs):
        t = time.time()
        res = func(*args, **kwargs)
        logger.info(f"{func.__name__} executed in {time.time() - t} s.")
        return res

    return wrapper
