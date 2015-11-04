# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Useful tools for engines.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import logging
from threading import Thread
from queue import Empty  # This is allowed thanks to the future package
from multiprocessing.queues import Queue

from atom.api import Atom, Coerced, Typed

from ...tasks.tools.database import TaskDatabase


class MeasureSpy(Atom):
    """Spy observing a task database and sending values update into a queue.

    All updates are sent immediatly as no issues have been detected so far.
    Using a timer based implementation would complicate things.

    """
    #: Set of entries for which to send notifications.
    observed_entries = Coerced(set)

    #: Reference to the database that needs to be observed.
    observed_database = Typed(TaskDatabase)

    #: Queue in which to send the updates.
    queue = Typed(Queue)

    def __init__(self, queue, observed_entries, observed_database):
        super(MeasureSpy, self).__init__(queue=queue,
                                         observed_database=observed_database,
                                         observed_entries=observed_entries)
        self.observed_database.observe('notifier', self.enqueue_update)

    def enqueue_update(self, change):
        """Put an update in the queue.

        Notes
        -----
        Change is a tuple as this is connected to a Signal.

        """
        if change[0] in self.observed_entries:
            self.queue.put_nowait(change)

    def close(self):
        """Put a dummy object signaling that no more updates will be sent.

        """
        self.queue.put(('', ''))


class ThreadMeasureMonitor(Thread):
    """Thread sending a queue content to the news signal of an engine.

    """

    def __init__(self, engine, queue):
        super(ThreadMeasureMonitor, self).__init__()
        self.queue = queue
        self.engine = engine

    def run(self):
        """Send the news received from the queue to the engine news signal.

        """
        while True:
            try:
                news = self.queue.get()
                if news not in [(None, None), ('', '')]:
                    # Here news is a Signal not Event hence the syntax.
                    self.engine.progress(news)
                elif news == ('', ''):
                    logger = logging.getLogger(__name__)
                    logger.debug('Spy closed')
                else:
                    break
            except Empty:
                continue
