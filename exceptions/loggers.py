import logging
from logging import StreamHandler, FileHandler, Formatter
import sys


formatter = Formatter("%(asctime)s — %(name)s — %(levelname)s — %(message)s")


class LoggerNames:
    main = 'main'
    gui = 'gui'
    db = 'db'
    scan = 'scan'


def get_console_handler():
    console_handler = StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    return console_handler


def get_file_handler(filename: str):
    file_handler = FileHandler(filename)
    file_handler.setFormatter(formatter)
    return file_handler


def get_logger(logger_name: str, level='debug'):
    levels_dict = {'debug': logging.DEBUG, 'info': logging.INFO, 'warning': logging.WARNING, 'error': logging.ERROR,
                   'critical': logging.CRITICAL}
    logger = logging.getLogger(logger_name)
    logger.setLevel(levels_dict.get(level) if levels_dict.get(level) else levels_dict.get('debug'))
    if not logger.handlers:
        logger.addHandler(get_file_handler(f'logs/{logger_name}.log'))
        logger.addHandler(get_console_handler())
    return logger

