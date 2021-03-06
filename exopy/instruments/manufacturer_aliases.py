# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Declarative object use to declare aliases of a manufacturer name.

ex : Keysight : aliases Agilent, HP

"""
from atom.api import Str, List
from enaml.core.api import Declarative, d_


class ManufacturerAlias(Declarative):
    """Declares that a manufacturer may be known under different names.

    """
    #: Main name under which the vendor is expected to be known
    id = d_(Str())

    #: List of aliased names.
    aliases = d_(List())
