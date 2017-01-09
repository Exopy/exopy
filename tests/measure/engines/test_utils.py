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
from pickle import dumps

import pytest

from ecpy.tasks.tasks.database import TaskDatabase
from ecpy.measure.engines.api import BaseEngine
from ecpy.measure.engines.utils import MeasureSpy, ThreadMeasureMonitor


def test_spy(caplog):
    """Test the measure spy working.

    """
    q = Queue()
    # Set up the database
    data = TaskDatabase()
    data.set_value('root', 'test', 0)
    data.set_value('root', 'test2', 2)
    data.prepare_to_run()

    spy = MeasureSpy(queue=q, observed_database=data,
                     observed_entries=('root/test',))

    class A(object):

        def __getstate__(self):
            raise Exception()

    with pytest.raises(Exception):
        dumps(A())

    data.set_value('root', 'test', 1)
    assert q.get(2) == ('root/test', 1)

    data.set_value('root', 'test', A())
    assert caplog.records

    data.set_value('root', 'test2', 1)
    assert q.empty()

    spy.close()
    assert q.get(2) == ('', '')


class B(object):

    def __getstate__(self):
        return (1,)

    def __setstate__(self, state):
        print('restore')
        raise Exception()


def test_monitor_thread(caplog):
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

    q.put(B())
    q.put('test')
    q.put(('', ''))
    q.put((None, None))
    m.join()

    assert caplog.records
    assert e.test == 'test'
