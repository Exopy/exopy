# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018-2018 by Exopy Authors, see AUTHORS for more details.
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


class LinspaceLoopInterface(TaskInterface):
    """ Common logic for all loop tasks.

    """
    #: Value at which to start the loop.
    start = Str('0.0').tag(pref=True, feval=Feval(types=numbers.Real))

    #: Value at which to stop the loop (included)
    stop = Str('1.0').tag(pref=True, feval=Feval(types=numbers.Real))

    #: Step between loop values.
    step = Str('0.1').tag(pref=True, feval=Feval(types=numbers.Real))

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
            np.arange(start, stop, step)
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

        # Make sure the sign of the step makes sense.
        step = -abs(step) if start > stop else abs(step)

        # Compute the number of steps we need.
        num = int(round(abs(((stop - start)/step)))) + 1

        # Update stop to make sure that the generated step is close to the user
        # specified one.
        stop_digit = abs(Decimal(str(stop)).as_tuple().exponent)
        start_digit = abs(Decimal(str(start)).as_tuple().exponent)
        step_digit = abs(Decimal(str(step)).as_tuple().exponent)
        digit = max((start_digit, step_digit, stop_digit))
        stop = round(start + (num-1)*step, digit)

        # Round values to the maximal number of digit used in start, stop and
        # step so that we never get issues with floating point rounding issues.
        # The max is used to allow from 1.01 to 2.01 by 0.1
        raw_values = np.linspace(start, stop, num)
        iterable = np.fromiter((round(value, digit)
                                for value in raw_values),
                               np.float, len(raw_values))
        task.write_in_database('loop_values', np.array(iterable))
        task.perform_loop(iterable)
