import functools
import logging


class Logger:

    def __init__(self):
        self.__logger = logging.getLogger('app')

    def info(self, message):
        self.__logger.info(message)

    def error(self, message, exc_info=True):
        self.__logger.error(message, exc_info=exc_info)

    def warning(self, message):
        self.__logger.warning(message)

    def debug(self, message):
        self.__logger.debug(message)

    def not_implemented(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if args:
                cls_name = args[0].__class__.__name__ if not isinstance(args[0], type) else args[0].__name__
            else:
                cls_name = func.__qualname__.split('.')[0]
            self.__logger.debug(f'{cls_name} | {func.__name__} is not implemented')
            return func(*args, **kwargs)
        return wrapper


logger = Logger()

