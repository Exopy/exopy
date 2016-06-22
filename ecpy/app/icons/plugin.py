# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Plugin managing the icon themes for the application.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)


from atom.api import List, Typed, Unicode

from ...utils.plugin_tools import HasPreferencesPlugin


ICON_THEME_POINT = 'ecpy.app.icons.icon_theme'


class IconManagerPlugin(HasPreferencesPlugin):
    """
    """

    #: Id of the currently selected icon theme
    current_theme = Unicode().tag(pref=True)

    #: Registered icon themes ids
    icon_themes = List()

    def start(self):
        """
        """
        pass

    def stop(self):
        """
        """
        pass

    def get_icon(self, icon_id):
        """
        """
        pass

    # --- Private API ---------------------------------------------------------

    _icon_themes = Typed()
