# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Ditextibuted under the terms of the BSD license.
#
# The full license is in the file LICENCE, ditextibuted with this software.
# -----------------------------------------------------------------------------
"""Test measure tracker.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from time import sleep
from threading import Event

import pytest
import enaml
from atom.api import Value
from enaml.core.object import Object

from ecpy.measure.workspace.measure_tracking import MeasureTracker
from ecpy.testing.measure.fixtures import measure

with enaml.imports():
    from ecpy.measure.workspace.measure_edition import MeasureEditorDockItem


pytest_plugins = str('ecpy.testing.measure.fixtures'),


class FalseObject(Object):
    """Object waiting for an event to yield its parents.

    """
    event = Value()

    def traverse_ancestors(self):
        """Wait on the given event to yield the parents.

        """
        self.event.wait()
        for a in super(FalseObject, self).traverse_ancestors():
            yield a


def create_false_widget(measure, event):
    """Create a false widget waiting to yiel its parent on an event.

    """
    if measure:
        return FalseObject(parent=MeasureEditorDockItem(measure=measure),
                           event=event)
    else:
        return FalseObject(parent=Object(), event=event)


@pytest.mark.timeout(10)
def test_measure_tracker(measure_workbench):
    """Test the measure tracker.

    """
    tracker = MeasureTracker()
    meas1 = measure(measure_workbench)
    meas2 = measure(measure_workbench)

    ev1 = Event()
    ev2 = Event()
    ev3 = Event()

    w1 = create_false_widget(meas1, ev1)
    w2 = create_false_widget(meas2, ev2)
    w3 = create_false_widget(None, ev3)

    tracker.start(meas1)

    assert tracker.get_selected_measure() is meas1

    tracker.enqueue(w2)
    sleep(0.01)
    ev2.set()
    assert tracker.get_selected_measure() is meas2
    ev2.clear()

    tracker._selected = meas1

    # Test discarding the buffer when new widgets are enqueued while processing
    tracker.enqueue(w3)
    tracker.enqueue(w1)
    sleep(0.01)
    assert not tracker._queue_not_empty.is_set()
    tracker.enqueue(w2)
    ev3.set()
    ev2.set()
    assert tracker.get_selected_measure() is meas2

    ev2.clear()
    ev3.clear()

    # Test getting the selected when the buffer is empty but not the queue.
    tracker.enqueue(w1)
    sleep(0.01)
    assert not tracker._queue_not_empty.is_set()
    tracker.enqueue(w3)
    ev1.set()
    ev3.set()
    assert tracker.get_selected_measure() is meas1

    # Test stopping while processing.
    ev3.clear()
    tracker.enqueue(w3)
    sleep(0.01)
    tracker._should_stop.set()
    ev3.set()
    tracker.stop()
