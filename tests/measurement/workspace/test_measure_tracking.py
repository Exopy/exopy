# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Ditextibuted under the terms of the BSD license.
#
# The full license is in the file LICENCE, ditextibuted with this software.
# -----------------------------------------------------------------------------
"""Test measurement tracker.

"""
from time import sleep
from threading import Event

import pytest
import enaml
from atom.api import Value
from enaml.core.object import Object

from exopy.measurement.workspace.measurement_tracking import MeasurementTracker
from exopy.testing.measurement.fixtures import measurement

with enaml.imports():
    from exopy.measurement.workspace.measurement_edition\
        import MeasurementEditorDockItem


pytest_plugins = str('exopy.testing.measurement.fixtures'),


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


def create_false_widget(measurement, event):
    """Create a false widget waiting to yiel its parent on an event.

    """
    if measurement:
        return FalseObject(
            parent=MeasurementEditorDockItem(measurement=measurement),
            event=event)
    else:
        return FalseObject(parent=Object(), event=event)


@pytest.mark.timeout(10)
def test_measurement_tracker(measurement_workbench):
    """Test the measurement tracker.

    """
    tracker = MeasurementTracker()
    meas1 = measurement(measurement_workbench)
    meas2 = measurement(measurement_workbench)

    ev1 = Event()
    ev2 = Event()
    ev3 = Event()

    w1 = create_false_widget(meas1, ev1)
    w2 = create_false_widget(meas2, ev2)
    w3 = create_false_widget(None, ev3)

    tracker.start(meas1)

    assert tracker.get_selected_measurement() is meas1

    tracker.enqueue(w2)
    sleep(0.01)
    ev2.set()
    assert tracker.get_selected_measurement() is meas2
    ev2.clear()

    tracker._selected = meas1

    # Test discarding the buffer when new widgets are enqueued while processing
    tracker.enqueue(w3)
    tracker.enqueue(w1)
    while tracker._buffer_empty.is_set():
        sleep(0.01)
    assert not tracker._queue_not_empty.is_set()
    tracker.enqueue(w2)
    ev3.set()
    ev2.set()
    assert tracker.get_selected_measurement() is meas2

    ev2.clear()
    ev3.clear()

    # Test getting the selected when the buffer is empty but not the queue.
    tracker.enqueue(w1)
    sleep(0.01)
    assert not tracker._queue_not_empty.is_set()
    tracker.enqueue(w3)
    ev1.set()
    ev3.set()
    assert tracker.get_selected_measurement() is meas1

    # Test stopping while processing.
    ev3.clear()
    tracker.enqueue(w3)
    sleep(0.01)
    tracker._should_stop.set()
    ev3.set()
    tracker.stop()
