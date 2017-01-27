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

from time import sleep
from threading import Thread, Lock, Event

import enaml
from atom.api import Atom, Value, List, Typed

from ..measure import Measure

with enaml.imports():
    from .measure_edition import MeasureEditorDockItem
    from .tools_edition import ToolsEditorDockItem


MEASURE_PARENTS = (MeasureEditorDockItem, ToolsEditorDockItem)


class MeasureTracker(Atom):
    """Object responsible for tracking the currently edited measure.

    The tracking relies on the last focus that got focus.

    """

    def start(self, measure):
        """Start the working thread.

        """
        self._selected = measure
        self._should_stop.clear()
        self._buffer_empty.set()
        self._thread = Thread(target=self.run)
        self._thread.daemon = True
        self._thread.start()

    def stop(self):
        """Stop the working thread.

        """
        self._should_stop.set()
        self._queue_not_empty.set()  # So that the working thread stop waiting
        self._thread.join()

    def enqueue(self, widget):
        """Enqueue a newly selected widget.

        """
        with self._lock:
            self._queue.append(widget)
            self._queue_not_empty.set()

    def run(self):
        """Method called by the working thread.

        """
        while True:

            self._queue_not_empty.wait()

            if self._should_stop.is_set():
                break

            with self._lock:
                self._buffer_empty.clear()
                self._buffer.extend(self._queue[::-1])
                self._queue = []
                self._queue_not_empty.clear()

            for w in self._buffer[::-1]:
                selected = None
                for p in w.traverse_ancestors():
                    if isinstance(p, MEASURE_PARENTS):
                        selected = p.measure
                        break

                if selected is not None:
                    self._selected = selected
                    break
                if (self._queue_not_empty.is_set() or
                        self._should_stop.is_set()):
                    break

            self._buffer = []
            self._buffer_empty.set()

    def get_selected_measure(self):
        """Get the currently selected measure.

        The measure is returned only when thread in done processing the
        enqueued widgets.

        """
        while True:

            self._buffer_empty.wait()
            if self._queue_not_empty.is_set():
                # Cannot be tested in a perfectly deterministic way
                sleep(0.05)  # pragma: no cover
            else:
                break

        return self._selected

    def set_selected_measure(self, measure):
        """Set the currently selected measure.

        This is used when the selected measure does not result from focusing.

        """
        while True:

            self._buffer_empty.wait()
            if self._queue_not_empty.is_set():
                # Cannot be tested in a perfectly deterministic way
                sleep(0.05)  # pragma: no cover
            else:
                break

        self._selected = measure

    # --- Private API ---------------------------------------------------------

    #: Background thread processing the last selection.
    _thread = Value()

    #: Lock ensuring the thread-safety when modifying the queue.
    _lock = Value(factory=Lock)

    #: Widgets that got focus and that have not yet been analysed.
    _queue = List()

    #: Widgets that got focus and that can be discarded if a selected measure
    #: is foound.
    _buffer = List()

    #: Event used to signal the working thread it should stop.
    _should_stop = Value(factory=Event)

    #: Event used to signal the working thread some widgets are waiting to be
    #: analysed
    _queue_not_empty = Value(factory=Event)

    #: Event signaling that the thread has processed its current buffer.
    _buffer_empty = Value(factory=Event)

    #: Current answer to the get_selected_measure query.
    _selected = Typed(Measure)
