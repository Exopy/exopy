# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2016 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the api module and get_icon helper function.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from ecpy.app.icons.api import get_icon


def test_get_icon(icon_workbench):
    """Test getting an icon using the helper function.

    """
    assert get_icon(icon_workbench, 'folder-open')
