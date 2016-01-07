# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Base classes to handle driver settings edition.

Settings are architecture specific information. Then can allow to select a
if several are available for example.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import Unicode, Typed
from enaml.core.api import d_, Declarative, d_func
from enaml.widgets.api import GroupBox

from ..connections.base_connection import BaseConnection


class BaseSettings(GroupBox):
    """Base widget for creating settings.

    """

    #: Connection this settings is matched with (allow to adapt the UI if
    #: necessary)
    connection = d_(Typed(BaseConnection))

    @d_func
    def gather_infos(self):
        """Return the current values as a dictionary.

        """
        raise NotImplementedError()


class Settings(Declarative):
    """A declarative class for contributing a driver settings.

    Settings object can be contributed as extensions child to the
    'settings' extension point of the 'ecpy.instruments' plugin.

    """
    #: Unique name used to identify the editor.
    id = d_(Unicode())

    #: Connection description.
    description = d_(Unicode())

    @d_func
    def new(self, workbench, connection, defaults):
        """Create a new setting and instantiate it properly.

        Defaults should be used to update the created setting.

        """
        raise NotImplementedError()
