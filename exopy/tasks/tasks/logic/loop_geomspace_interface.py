# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2023 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Interface allowing to use a linspace in a LoopTask

"""
import numbers
from decimal import Decimal

import numpy as np
from atom.api import Str

from ..task_interface import TaskInterface
from ..validators import Feval


class GeomspaceLoopInterface(TaskInterface):
    """ Common logic for all loop tasks.

    """
    #: Value at which to start the loop.
    start = Str('1.0').tag(pref=True, feval=Feval(types=numbers.Real))

    #: Value at which to stop the loop (included)
    stop = Str('100.0').tag(pref=True, feval=Feval(types=numbers.Real))

    #: Step between loop values.
    num = Str('10').tag(pref=True, feval=Feval(types=numbers.Real))

    def check(self, *args, **kwargs):
        """Check evaluation of all loop parameters.

        """
        task = self.task
        err_path = task.path + '/' + task.name
        test, traceback = super(GeomspaceLoopInterface,
                                self).check(*args, **kwargs)

        if not test:
            return test, traceback

        start = task.format_and_eval_string(self.start)
        stop = task.format_and_eval_string(self.stop)
        num = task.format_and_eval_string(self.num)
        if 'value' in task.database_entries:
            task.write_in_database('value', start)

        task.write_in_database('point_number', num)

        return test, traceback

    def perform(self):
        """Build the arange and pass it to the LoopTask.

        """
        task = self.task
        start = task.format_and_eval_string(self.start)
        stop = task.format_and_eval_string(self.stop)
        num = task.format_and_eval_string(self.num)

        # Make sure the sign of the step makes sense.
        num = -abs(num) if start > stop else abs(num)

       
        # determine rounding from user input.   
        stop_digit = abs(Decimal(str(stop)).as_tuple().exponent)
        start_digit = abs(Decimal(str(start)).as_tuple().exponent)
        digit = max((start_digit, stop_digit))
        stop = round(stop, digit)

        # Round values to the maximal number of digit used in start and stop
        # so that we never get issues with floating point rounding issues.
        # The max is used to allow from 1.01 to 2.01 by 0.1
        raw_values = np.geomspace(start, stop, num)
        iterable = np.fromiter((round(value, digit)
                                for value in raw_values),
                               np.float64, len(raw_values))
        task.write_in_database('loop_values', np.array(iterable))
        task.perform_loop(iterable)
