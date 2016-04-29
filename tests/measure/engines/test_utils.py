# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test engine utilities

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from multiprocessing import Queue

from ecpy.tasks.tasks.database import TaskDatabase
from ecpy.measure.engines.api import BaseEngine
from ecpy.measure.engines.utils import MeasureSpy, ThreadMeasureMonitor


def test_spy():
    """Test the measure spy working.

    """
    q = Queue()
    data = TaskDatabase()
    spy = MeasureSpy(queue=q, observed_database=data,
                     observed_entries=('test',))

    data.notifier(('test', 1))
    assert q.get()

    data.notifier(('test2', 1))
    assert q.empty()

    spy.close()
    assert q.get() == ('', '')


def test_monitor_thread():
    """Test the monitor thread rerouting news to engine signal.

    """
    from atom.api import Value

    class E(BaseEngine):

        test = Value()

        def _observe_progress(self, val):
            self.test = val

    q = Queue()
    e = E()
    m = ThreadMeasureMonitor(e, q)
    m.start()
    q.put('test')
    q.put(('', ''))
    q.put((None, None))
    m.join()

    assert e.test == 'test'
