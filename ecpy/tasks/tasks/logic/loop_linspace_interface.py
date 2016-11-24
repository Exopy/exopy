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

import numbers
from atom.api import Unicode
from numpy import arange
from decimal import Decimal

from ..task_interface import TaskInterface
from ..validators import Feval


class LinspaceLoopInterface(TaskInterface):
    """ Common logic for all loop tasks.

    """
    #: Value at which to start the loop.
    start = Unicode('0.0').tag(pref=True, feval=Feval(types=numbers.Real))

    #: Value at which to stop the loop (included)
    stop = Unicode('1.0').tag(pref=True, feval=Feval(types=numbers.Real))

    #: Step between loop values.
    step = Unicode('0.1').tag(pref=True, feval=Feval(types=numbers.Real))

    def check(self, *args, **kwargs):
        """Check evaluation of all loop parameters.

        """
        task = self.task
        err_path = task.path + '/' + task.name
        test, traceback = super(LinspaceLoopInterface,
                                self).check(*args, **kwargs)

        if not test:
            return test, traceback

        start = task.format_and_eval_string(self.start)
        stop = task.format_and_eval_string(self.stop)
        step = task.format_and_eval_string(self.step)
        if 'value' in task.database_entries:
            task.write_in_database('value', start)

        try:
            num = int(abs((stop - start)/step)) + 1
            task.write_in_database('point_number', num)
        except Exception as e:
            test = False
            mess = 'Loop task did not succeed to compute the point number: {}'
            traceback[err_path + '-points'] = mess.format(e)
            return test, traceback

        try:
            arange(start, stop, step)
        except Exception as e:
            test = False
            mess = 'Loop task did not succeed to create an arange: {}'
            traceback[err_path + '-arange'] = mess.format(e)

        return test, traceback

    def perform(self):
        """Build the arange and pass it to the LoopTask.

        """
        task = self.task
        start = task.format_and_eval_string(self.start)
        stop = task.format_and_eval_string(self.stop)
        step = task.format_and_eval_string(self.step)
        num = int(abs(((stop - start)/step)))

        if start > stop:
            step = -step

        if num >= abs((stop - start)/step):
            stop += step

        digit = abs(Decimal(str(step)).as_tuple().exponent)
        iterable = (round(value, digit) for value in arange(start, stop, step))
        task.perform_loop(iterable)
