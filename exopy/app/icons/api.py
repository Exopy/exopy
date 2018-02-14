# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Api of the icon plugin.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from .icon_theme import IconTheme, Icon


def get_icon(workbench, icon_id):
    """Utility function querying an icon.

    This function is provided to be more compact than using the core plugin.
    All widgets if the main application window is one of their parent can
    access the workbench thanks to dynamic scoping.

    """
    plugin = workbench.get_plugin('exopy.app.icons')
    return plugin.get_icon(icon_id)


__all__ = ['IconTheme', 'Icon', 'get_icon']
