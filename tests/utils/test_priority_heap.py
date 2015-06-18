# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test for the priority heap.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from pytest import raises

from ecpy.utils.priority_heap import PriorityHeap


class TestPriorityHeap(object):
    """Test the basic use of a Priority queue.

    """

    def setup(self):
        self.queue = PriorityHeap()

    def test_push_pop(self):

        self.queue.push(1, 5)
        self.queue.push(0, 6)
        assert len(self.queue) == 2
        assert self.queue.pop() == 6
        assert self.queue.pop() == 5
        with raises(IndexError):
            self.queue.pop()
        assert self.queue._counter == 0

    def test_ordering(self):

        self.queue.push(0, 5)
        self.queue.push(0, 4)
        self.queue.push(0, 6)
        assert list(self.queue) == [5, 4, 6]

    def test_removing(self):

        self.queue.push(0, 5)
        self.queue.push(0, 6)
        self.queue.remove(5)
        assert len(self.queue) == 1
        assert self.queue.pop() == 6

    def test_pushing_while_iterating(self):

        self.queue.push(1, 1)
        for i, obj in enumerate(self.queue):
            if i == 10:
                break
            self.queue.push(1, 2)
            self.queue.push(0, 3)
        assert len(self.queue) == 10
        assert 3 not in self.queue._heap
