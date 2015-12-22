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

from atom.api import Unicode, Enum, Value, Dict
from enaml.core.api import d_, Declarative


class BaseConnection():
    pass




class Connection(Declarative):
    """A declarative class for contributing a connection.

    Connection object can be contributed as extensions child to the
    'connections' extension point of the 'ecpy.instruments' plugin.

    """
    #: Unique name used to identify the editor.
    id = d_(Unicode())

    #: Connection description.
    description = d_(Unicode())
