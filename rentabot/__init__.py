"""Rent-A-Bot

Your automation resource provider.
"""
try:
    from importlib.metadata import version
except ImportError:
    # Python < 3.8
    from importlib_metadata import version

__version__ = version("rent-a-bot")

# Import logger
from rentabot.logger import get_logger

logger = get_logger(__name__)
