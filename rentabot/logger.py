"""
rentabot.logging

This module contains rentabot logging facility.
"""

import logging
import sys

LOG_FORMAT = "%(asctime)s - %(name)s.%(funcName)s - %(message)s"

# Configure logging at module level
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)


def get_logger(name, **kwargs):
    """
    Return a logger object configured to print in stdout

    Args:
        name (str): Logger name

    Returns:
        A logger object
    """
    return logging.getLogger(name)
