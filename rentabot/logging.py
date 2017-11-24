# coding: utf-8
"""
logging_utils.py

Offer some option to configure and instantiate logging.
"""

import logging
import datetime

ANSI_COLORS = {"reset": "\033[0m",
               "bold": "\033[1m",
               "italics": "\033[3m",
               "fred": "\033[31m",
               "fgreen": "\033[32m",
               "fyellow": "\033[33m",
               "fblue": "\033[34m",
               "fmagenta": "\033[35m",
               "fcyan": "\033[36m",
               }


def get_logger(name):
    """
    :param name: name of the logger
    :return: a logger parametrize to log into the console.
    """
    # instantiate the logger object
    logger = logging.getLogger(name)
    # Avoid double registration of the logger.
    if not logger.handlers:
        # Create a handler to write into the console
        stream_handler = logging.StreamHandler()
        # add a formatter to the handler
        stream_handler.setFormatter(PrettyPrinterFormatter())
        # Add the handler to the logger
        logger.addHandler(stream_handler)
    return logger


class PrettyPrinterFormatter(logging.Formatter):
    """
    A custom formatter for colored printing
    """
    LOG_FORMAT = '%(levelname)s - %(message)s'

    def __init__(self):
        """
        Set custom log format
        """
        # Construct formatter
        super(PrettyPrinterFormatter, self).__init__(fmt=self.LOG_FORMAT)

    def format(self, record):
        """
        Overload format, for colored printing

        :param record: record object
        """
        # Custom parser & color application
        if record.levelno is logging.DEBUG:
            _format = ANSI_COLORS['bold'] + \
                      ANSI_COLORS['fgreen'] + "{}" + ANSI_COLORS['reset']
        elif record.levelno is logging.INFO:
            _format = ANSI_COLORS['bold'] + \
                      ANSI_COLORS['fblue'] + "{}" + ANSI_COLORS['reset']
        elif record.levelno is logging.WARNING:
            _format = ANSI_COLORS['bold'] + \
                      ANSI_COLORS['fyellow'] + "{}" + ANSI_COLORS['reset']
        elif record.levelno is logging.ERROR:
            _format = ANSI_COLORS['bold'] + \
                      ANSI_COLORS['fred'] + "{}" + ANSI_COLORS['reset']
        elif record.levelno is logging.CRITICAL:
            _format = ANSI_COLORS['bold'] + \
                      ANSI_COLORS['fmagenta'] + "{}" + ANSI_COLORS['reset']
        else:
            raise ValueError("Unsupported record level number")

        if isinstance(record.msg, dict):
            record.msg = record.msg['message']

        name = _format.format(record.name)
        funcname = _format.format(record.funcName)
        record.levelname = _format.format(record.levelname)
        msg = _format.format(record.msg)
        if not hasattr(record, 'asctime'):
            created = record.created
            value = datetime.datetime.fromtimestamp(created)
            asctime = _format.format(value.strftime('%Y-%m-%d %H:%M:%S'))
        else:
            asctime = _format.format(record.asctime)

        record.msg = "{} - {} - {} - {}".format(asctime, name, funcname, msg)

        return super(PrettyPrinterFormatter, self).format(record)

