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

import logging

from atom.api import List, Typed, Unicode

from ...utils.plugin_tools import HasPreferencesPlugin, ExtensionsCollector


ICON_THEME_POINT = 'ecpy.app.icons.icon_theme'

ICON_THEME_EXTENSION_POINT = 'ecpy.app.icons.icon_theme_extension'


class IconManagerPlugin(HasPreferencesPlugin):
    """Plugin managing icon theme and access to icon for the application.

    """
    #: Id of the currently selected icon theme
    current_theme = Unicode('ecpy.FontAwesome').tag(pref=True)

    #: Id of the icon theme to use as fallback if a theme fail to provide an
    #: icon.
    fallback_theme = Unicode('ecpy.FontAwesome').tag(pref=True)

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

    #: Collector for the declared icon themes.
    _icon_themes = Typed(ExtensionsCollector)

    #: Collector for the declared icon theme extensions.
    _icon_themes_extension = Typed(ExtensionsCollector)

    def _add_extensions_to_selected_theme(self, change=None):
        """Add contributed theme extension to the selected theme.

        """
        # Assign all contributed icons from all extensions.
        if change is None:
            pass

        # Only update icons provided by new extensions.
        else:
            pass

    def _bind_observers(self):
        """
        """
        pass

    def _unbind_observers(self):
        """
        """
        pass
