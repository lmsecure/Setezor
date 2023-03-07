import logging
from logging import StreamHandler, FileHandler, Formatter
import sys
import os


formatter = Formatter("%(asctime)s — %(name)s — %(levelname)s — %(message)s")


class LoggerNames:
    main = 'main'
    gui = 'gui'
    web_server = 'web_server'
    db = 'db'
    scan = 'scan'
    task = 'task'


def get_console_handler(*args, **kwargs):
    console_handler = StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    return console_handler


def get_file_handler(filename: str, path_prefix: str, *args, **kwargs):
    file_handler = FileHandler(os.path.join(path_prefix, filename))
    file_handler.setFormatter(formatter)
    return file_handler


def check_and_create_log_folder(path_prefix):
    
    if not os.path.exists(os.path.join(path_prefix, 'logs')):
        os.mkdir(os.path.join(path_prefix, 'logs'))


def get_logger(logger_name: str, level: str='debug', handlers: list=['console', 'file']):
    path_prefix = os.path.split(os.environ.get('APPIMAGE'))[0] if os.environ.get('APPIMAGE') else './'
    handlers_dict = {'console': get_console_handler,
                     'file': get_file_handler}
    check_and_create_log_folder(path_prefix=path_prefix)
    levels_dict = {'debug': logging.DEBUG, 'info': logging.INFO, 'warning': logging.WARNING, 'error': logging.ERROR,
                   'critical': logging.CRITICAL}
    if logger := logging.root.manager.loggerDict.get(logger_name):
        return logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(levels_dict.get(level) if levels_dict.get(level) else levels_dict.get('debug'))
    for i in handlers:
        logger.addHandler(handlers_dict.get(i)(filename=f'logs/{logger_name}.log', path_prefix=path_prefix))
    # if not logger.handlers:
    #     logger.addHandler(get_file_handler())
    #     logger.addHandler(get_console_handler())
    return logger

