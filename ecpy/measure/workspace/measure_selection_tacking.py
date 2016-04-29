# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Thread-loke object keeping track of the last edited measure.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)


from threading import Thread, Lock

import enaml
from atom.api import Atom, Value, List, Event

with enaml.imports():
    from .measure_edition import MeasureEditorDockItem
    from .tools_edition import ToolsEditorDockItem


class MeasureTacker(Atom):
    """
    """

    def start(self):
        """
        """
        pass

    def stop(self):
        """
        """
        pass

    def enqueue(self, widget):
        """Enqueue a newly selected widget.

        """
        pass

    def run(self):
        """Process.

        """
        pass

    def get_selected_measure(self):
        """
        """
        pass

    # --- Private API ---------------------------------------------------------

    #:
    _thread = Value()

    #:
    _lock = Value(factory=Lock)

    #:
    _queue = List()

    #:
    _buffer = List()

    #:
    _should_stop = Value(factory=Event)
