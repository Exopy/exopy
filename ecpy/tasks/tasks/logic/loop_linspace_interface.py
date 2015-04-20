# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Interface allowing to use a linspace in a LoopTask

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import Unicode
from numpy import linspace

from ..task_interface import TaskInterface


class LinspaceLoopInterface(TaskInterface):
    """ Common logic for all loop tasks.

    """
    #: Value at which to start the loop.
    start = Unicode('0.0').tag(pref=True, feval=True)

    #: Value at which to stop the loop (included)
    stop = Unicode('1.0').tag(pref=True, feval=True)

    #: Step between loop values.
    step = Unicode('0.1').tag(pref=True, feval=True)

    def check(self, *args, **kwargs):
        """Check evaluation of all loop parameters.

        """
        task = self.task
        err_path = task.task_path + '/' + task.task_name
        test, traceback = super(LinspaceLoopInterface,
                                self).check(*args, **kwargs)

        if not test:
            return test, traceback

        start = task.format_and_eval_string(self.start)
        stop = task.format_and_eval_string(self.stop)
        step = task.format_and_eval_string(self.step)

        try:
            num = int(abs((stop - start)/step)) + 1
            task.write_in_database('point_number', num)
        except Exception as e:
            test = False
            mess = 'Loop task did not succeed to compute the point number: {}'
            traceback[err_path + '-points'] = mess.format(e)
            return test, traceback

        try:
            linspace(start, stop, num)
        except Exception as e:
            test = False
            mess = 'Loop task did not succeed to create a linspace: {}'
            traceback[err_path + '-linspace'] = mess.format(e)

        return test, traceback

    def perform(self):
        """Build the linspace and pass it to the LoopTask.

        """
        task = self.task
        start = task.format_and_eval_string(self.start)
        stop = task.format_and_eval_string(self.stop)
        step = task.format_and_eval_string(self.step)
        num = int(round(abs(((stop - start)/step)))) + 1

        iterable = linspace(start, stop, num)
        task.perform_loop(iterable)
