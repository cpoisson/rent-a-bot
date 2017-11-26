# coding: utf-8
"""
rentabot.logging

This module contains rentabot logging facility.
"""

import logging
import daiquiri
import daiquiri.formatter

LOG_FORMAT = "%(color)s%(asctime)s - %(name)s.%(funcName)s - %(message)s%(color_stop)s"

daiquiri.setup(
    level=logging.INFO,
    outputs=(
        daiquiri.output.Stream(formatter=daiquiri.formatter.ColorFormatter(fmt=LOG_FORMAT)),
    )
)


def get_logger(name, **kwargs):
    """
    Return a logger object configured to print in stdout

    Args:
        name (str): Logger name

    Returns:
        A logger object
    """
    # instantiate the logger object
    return daiquiri.getLogger(name, **kwargs)