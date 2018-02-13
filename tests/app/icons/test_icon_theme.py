# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the icon theme basic capabilities.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import enaml

with enaml.imports():
    from .contributions import (DummyTheme, DummyThemeExtension, DumbIcon)


def test_icon_theme():
    """Test getting an icon from a theme.

    """
    theme = DummyTheme()

    icon = theme.get_icon(None, 'dumb1')
    assert isinstance(icon, DumbIcon)
    assert icon.id == 'dumb1'

    assert theme.get_icon(None, '__non_existing__') is None


def test_icon_theme_extension():
    """Test listing the icons in an icon theme extension.

    """
    ext = DummyThemeExtension()
    assert len(ext.icons()) == 1
