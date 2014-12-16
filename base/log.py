import logging
import logging.handlers
import sys

import base.config as config

log_formatter = logging.Formatter('%(asctime)s %(levelname)s [%(name)s]: %(message)s')

file_handler = logging.handlers.RotatingFileHandler(
    config.LOG_FILENAME,
    backupCount=5,
)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.DEBUG)

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
stdout_handler.setFormatter(log_formatter)


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    logger.addHandler(file_handler)
    logger.addHandler(stdout_handler)

    return logger

