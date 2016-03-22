# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Extension API for the instrument plugin.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from .user import InstrUser

from .drivers.driver_decl import Driver, Drivers
from .starters.base_starter import Starter
from .starters.exceptions import InstrIOError
from .connections.base_connection import BaseConnection, Connection
from .settings.base_settings import BaseSettings, Settings
from .manufacturer_aliases import ManufacturerAlias

__all__ = ['Driver', 'Drivers', 'InstrUser', 'BaseConnection', 'Connection',
           'Settings', 'BaseSettings', 'Starter', 'ManufacturerAlias',
           'InstrIOError']
