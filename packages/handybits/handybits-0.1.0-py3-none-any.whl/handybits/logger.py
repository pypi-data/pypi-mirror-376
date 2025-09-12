import sys
import logging
from logging import handlers


FORMATTER = logging.Formatter(
    '%(asctime)-25s %(levelname)-10s %(module)-25s %(funcName)-20s %(message)s'
)


def get_console_log_handler(log_level: int = logging.ERROR):
    console_log_handler = logging.StreamHandler(sys.stderr)
    console_log_handler.setFormatter(FORMATTER)
    console_log_handler.setLevel(log_level)
    return console_log_handler


def get_file_log_handler(path: str, log_level: int = logging.ERROR, **kwargs):
    file_log_handler = handlers.TimedRotatingFileHandler(
        filename=path,
        encoding=kwargs.pop('encoding', 'UTF-8'),
        backupCount=kwargs.pop('backupCount', 7),
        when=kwargs.pop('when', 'midnight'),
        **kwargs
    )
    file_log_handler.setFormatter(FORMATTER)
    file_log_handler.setLevel(log_level)
    return file_log_handler


def get_logger(name: str, filepath: str | None = None, log_level: int = logging.ERROR) -> logging.Logger:
    """ Get logger with console and file handlers. """
    logger = logging.getLogger(name=name)
    logger.addHandler(get_console_log_handler(log_level=log_level))

    if filepath:
        file_log_handler = get_file_log_handler(
            filepath,
            log_level=log_level,
            encoding='UTF-8',
            backupCount=7,
            when='midnight'
        )
        logger.addHandler(file_log_handler)

    logger.setLevel(log_level)
    return logger
