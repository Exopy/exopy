# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Extension objects to the icon plugin.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import Unicode, Dict, List
from enaml.core.api import Declarative, d_, d_func


class IconTheme(Declarative):
    """Declaration of an icon theme.

    An icon theme should provide the following icons  as far as the main
    application is concerned:
    - folder-open
    -
    -
    -

    """
    #: Unique id of the icon theme.
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
        if not self._icons and self.children:
            self._refresh_children_icons()

        if icon_id in self._icons:
            return self._icons[icon_id].get_icon(manager, self)

        else:
            return None

    # --- Private API ---------------------------------------------------------

    #: Map of id: icon as declared as children to this theme.
    _icons = Dict()

    def _refresh_children_icons(self):
        """Refresh the mapping of the icons contributed as children.

        """
        # HINT when reparenting enaml does not properly update the children
        for c in [c for c in self.children if c.parent is self]:
            if isinstance(c, Icon):
                self._icons[c.id] = c


class IconThemeExtension(Declarative):
    """Declarative object used to contribute new icons to an existing theme.

    """
    #: Unicsue id of the extension.
    id = d_(Unicode())

    #: Id of the icon theme to which to contribute the children Icon objects.
    theme = d_(Unicode())

    def icons(self):
        """List the associated icons.

        """
        if not self._icons:
            self._icons = [c for c in self.children if isinstance(c, Icon)]

        return self._icons

    # --- Private API ---------------------------------------------------------

    #: Private list of contributed icons.
    _icons = List()


class Icon(Declarative):
    """Declarative object used to contribute an icon.

    """
    #: Unique id describing the icon. It should provide a clear description
    #: of the icon purpose.
    id = d_(Unicode())

    @d_func
    def get_icon(self, manager, theme):
        """Generate the corresponding enaml icon object.

        """
        raise NotImplementedError()
