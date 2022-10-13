import traceback
from functools import wraps
from exceptions.loggers import get_logger


def exception_decorator(logger_name: str, default_return=None, logger_level='debug'):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name, logger_level)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(traceback.format_exc())
                return default_return
        return wrapper
    return decorator
