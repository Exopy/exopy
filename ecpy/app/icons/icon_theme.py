# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Extension objects to the icon plugin.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import Unicode, Dict
from enaml.core.api import Declarative, d_, d_func


class IconTheme(Declarative):
    """Declaration of an icon theme.

    An icon theme should provide the following icons :
    -
    -
    -
    -

    """
    #:
    id = d_(Unicode())

    @d_func
    def get_icon(self, manager, icon_id):
        """Generate an icon corresponding to an id.

        By default an icon theme simply check its children Icons and ask it to
        generate the actual icon.

        Parameters
        ----------
        manager : IconManagerPlugin
            Reference to the plugin manager.

        icon_id : unicode
            Id of the icon which should be generated.

        Returns
        -------
        icon : enaml.icon.Icon or None
            Icon matching the id or None if no icon match the provided id.

        """
        if not self._icons:
            for c in self.children:
                if isinstance(c, Icon):
                    self._icons[c.id] = c

        if icon_id in self._icons:
            return self._icons[icon_id].get_icon(manager, self)

        else:
            return None

    # --- Private API ---------------------------------------------------------

    #: Map of id: icon as declared as children to this theme.
    _icons = Dict()


class IconThemeExtension(Declarative):
    """
    """
    pass


class Icon(Declarative):
    """
    """
    #:
    id = d_(Unicode())

    @d_func
    def get_icon(self, manager, theme):
        """
        """
        pass
