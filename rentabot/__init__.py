"""Rent-A-Bot

Your automation resource provider.
"""

__version__ = "0.2.0"

# Import logger
from rentabot.logger import get_logger

logger = get_logger(__name__)

# Import models and controllers
import rentabot.controllers
import rentabot.models
