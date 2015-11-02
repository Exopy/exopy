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

from time import sleep
from multiprocessing.queues import Queue

from ecpy.tasks.tools.database import TaskDatabase
from ecpy.measure.engines.api import BaseEngine
from ecpy.measure.engines.utils import MeasureSpy, ThreadMeasureMonitor


def test_spy():
    """Test the measure spy working.

    """
    q = Queue()
    data = TaskDatabase()
    spy = MeasureSpy(queue=q, observed_database=data,
                     observed_entries=('test',))

    data.notifier = {'value': ('test', 1)}
    assert q.get()

    data.notifier = {'value': ('test', 1)}
    assert q.empty()

    spy.close()
    assert q.get() == ('', '')


def test_monitor_thread():
    """Test the monitor thread rerouting news to engine signal.

    """
    news = None

    class E(BaseEngine):

        def _observe_news(self, val):
            global news
            news = val

    q = Queue()
    m = ThreadMeasureMonitor(E(), q)
    q.put('test')
    sleep(0.01)
    assert news == 'test'

    q.put(('', ''))
    sleep(0.01)

    q.put((None, None))
    m.join()
