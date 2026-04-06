from typing import Callable, Any
import functools
import logging


class Logger:

    def __init__(self):
        self.__logger = logging.getLogger('app')

    def info(self, message: str):
        self.__logger.info(message)

    def error(self, message: str, exc_info: bool = True):
        self.__logger.error(message, exc_info=exc_info)

    def warning(self, message: str):
        self.__logger.warning(message)

    def debug(self, message: str):
        self.__logger.debug(message)

    def not_implemented(self, func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: tuple[Any, ...], **kwargs: dict[Any, Any]) -> Callable[..., Any]:
            if args:
                cls_name = args[0].__class__.__name__ if not isinstance(args[0], type) else args[0].__name__
            else:
                cls_name = func.__qualname__.split('.')[0]
            self.__logger.debug(f'{cls_name} | {func.__name__} is not implemented')
            return func(*args, **kwargs)
        return wrapper


logger = Logger()

