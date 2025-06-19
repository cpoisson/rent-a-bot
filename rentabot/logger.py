# coding: utf-8
"""
rentabot.logging

This module contains rentabot logging facility.
"""

import logging
import sys

LOG_FORMAT = "%(asctime)s - %(name)s.%(funcName)s - %(message)s"

# Configure the root logger
def setup_logging():
    # Clear any existing handlers
    logging.root.handlers = []
    
    # Add our stdout handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logging.root.addHandler(handler)
    logging.root.setLevel(logging.INFO)

# Initialize logging on module import
setup_logging()

def get_logger(name, **kwargs):
    """
    Return a logger object configured to print in stdout

    Args:
        name (str): Logger name

    Returns:
        A logger object
    """
    # instantiate the logger object
    return logging.getLogger(name)