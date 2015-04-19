# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Utility object to test the execution of tasks.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import Value, Int, Callable

from ecpy.tasks.base_tasks import SimpleTask


class CheckTask(SimpleTask):
    """Task keeping track of check and perform call and value passed to perform

    """
    #: Number of time the check method has been called.
    check_called = Int()

    #: Number of time the perform method has been called.
    perform_called = Int()

    #: Value passed to the perform method.
    perform_value = Value()

    #: Function to call in the perform method
    custom = Callable(lambda t, x: None)

    def check(self, *args, **kwargs):

        self.check_called += 1
        return super(CheckTask, self).check(*args, **kwargs)

    def perform(self, value=None):

        self.perform_called += 1
        self.perform_value = value
        self.custom(self, value)


class ExceptionTask(SimpleTask):
    """Task raising an exception when executed.

    """

    def perform(self):
        raise Exception()


def join_threads(root):
    """Wait for all threads to stop.

    """
    for pool_name in root.threads:
        with root.threads.safe_access(pool_name) as pool:
            for thread in pool:
                try:
                    thread.join()
                except Exception:
                    pass
