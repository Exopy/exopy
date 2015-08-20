# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Definition of the base views for the tasks.

If need be one can inherit from an enamldef class to build a new class using
class.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import Event
from enaml.declarative.api import Declarative, d_


class DestroyHook(Declarative):
    """Declarative subclass providing an event to customize behavior before
    destroying.

    This class is meant to be used as a Mixin

    """
    #: Event emitted just before destroying the object.
    ended = d_(Event())

    def destroy(self):
        """Re-implemented to emit ended before cleaning up the declarative
        structure.

        """
        self.ended = True
        super(DestroyHook, self).destroy()
