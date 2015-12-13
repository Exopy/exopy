# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Mixin class to provide declarative finalization customisations capabilities.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import Event
from enaml.core.api import d_


def add_destroy_hook(cls):
    """Add a declarative event signaling that an object will be destroyed.

    """
    class Destroyable(cls):

        #: Event emitted just before destroying the object.
        ended = d_(Event())

        def destroy(self):
            """Re-implemented to emit ended before cleaning up the declarative
            structure.

            """
            self.ended = True
            super(Destroyable, self).destroy()

    return Destroyable
