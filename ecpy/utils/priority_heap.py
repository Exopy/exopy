# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Priority heap based on list and heapq module.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import heapq
from future.utils import implements_iterator


#: Sentinel used to invalidated an object in the heap.
_REMOVED = object()


@implements_iterator
class PriorityHeap(object):
    """A priority heap implementation based on a heapq.

    """

    __slots__ = ('_heap', '_map', '_counter')

    def __init__(self):
        self._heap = []
        self._map = {}
        self._counter = 0

    def push(self, priority, obj):
        """Push a task with a given priority on the queue.

        Parameters
        ----------
        priority : int
            Priority associated with the object to push.

        obj :
            Object to push on the heap.

        """
        task = [priority, self._counter, obj]
        heapq.heappush(self._heap, task)
        self._map[obj] = task
        self._counter += 1

    def pop(self):
        """Pop a task from the queue.

        """
        while True:
            _, _, obj = heapq.heappop(self._heap)
            if obj is not _REMOVED:
                del self._map[obj]
                break
        if not self._heap:
            self._counter = 0
        return obj

    def remove(self, obj):
        """Mark a task as being outdated.

        This is the only way to remove an object from a heap without messing
        with the sorting.

        """
        if obj in self._map:
            heapobj = self._map[obj]
            heapobj[2] = _REMOVED
            del self._map[obj]

    def __iter__(self):
        """Allow to use this object as an iterator.

        """
        return self

    def __len__(self):
        """Return the length of the underlying list.

        """
        return len([t for t in self._heap if t[2] is not _REMOVED])

    def __next__(self):
        """Iterate over the heap by poping object.

        Iterating over the heap will destroy it.

        """
        try:
            return self.pop()
        except IndexError:
            raise StopIteration
