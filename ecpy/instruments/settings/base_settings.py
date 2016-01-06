# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Base classes to handle connection information edition.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import Unicode
from enaml.core.api import d_, Declarative, d_func
from enaml.widgets.api import GroupBox


class BaseSettings(GroupBox):
    """
    """

    @d_func
    def set_default(self, defaults):
        """
        """
        pass

    @d_func
    def gather_infos(self):
        """
        """
        pass


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
    def new(self, workbench, defaults):
        """
        """
        pass  # Simply returns a new connection instance properly initialized
