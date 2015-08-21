# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
# XXXX
"""

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import logging
from threading import Thread
from queue import Empty  # This is allowed thanks to the future package
from multiprocessing.queues import Queue

from atom.api import Atom, Coerced, Typed

from ...tasks.tools.task_database import TaskDatabase


class MeasureSpy(Atom):
    # XXXX here need a timer to avoid useless transfer
    """ Spy observing a task database and sending values update into a queue.

    """
    observed_entries = Coerced(set)
    observed_database = Typed(TaskDatabase)
    queue = Typed(Queue)

    def __init__(self, queue, observed_entries, observed_database):
        super(MeasureSpy, self).__init__()
        self.queue = queue
        self.observed_entries = set(observed_entries)
        self.observed_database = observed_database
        self.observed_database.observe('notifier', self.enqueue_update)

    def enqueue_update(self, change):
        new = change['value']
        if new[0] in self.observed_entries:
            self.queue.put_nowait(new)

    def close(self):
        # Simply signal the queue the working thread that the spy won't send
        # any more informations. But don't request the thread to exit this
        # is the responsability of the engine.
        self.queue.put(('', ''))


class ThreadMeasureMonitor(Thread):
    # XXXX
    """ Thread sending a queue content to the news signal of a engine.

    """

    def __init__(self, engine, queue):
        super(ThreadMeasureMonitor, self).__init__()
        self.queue = queue
        self.engine = engine

    def run(self):
        while True:
            try:
                news = self.queue.get()
                if news not in [(None, None), ('', '')]:
                    # Here news is a Signal not Event hence the syntax.
                    self.engine.news(news)
                elif news == ('', ''):
                    logger = logging.getLogger(__name__)
                    logger.debug('Spy closed')
                else:
                    break
            except Empty:
                continue
