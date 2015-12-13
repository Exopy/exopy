# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Simply test that the api module is not broken.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)


def test_api_import():
    """Test importing all the names defined in the api module.

    """
    from ecpy.measure.monitors.text_monitor.api import *
