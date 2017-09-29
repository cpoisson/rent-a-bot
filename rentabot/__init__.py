# -*- coding: utf-8 -*-
""" Rent-A-Bot

Your automation resource provider.
"""

from flask import Flask
app = Flask(__name__)

import rentabot.views
import rentabot.models
