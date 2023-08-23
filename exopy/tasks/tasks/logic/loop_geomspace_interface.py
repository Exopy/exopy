# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2023 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Interface allowing to use a geomspace in a LoopTask

"""
import numbers
from decimal import Decimal

import numpy as np
from atom.api import Str, Int

from ..task_interface import TaskInterface
from ..validators import Feval


class GeomspaceLoopInterface(TaskInterface):
    """ Interface used to loop over numbers evenly spaced on a log scale

    """
    #: Value at which to start the loop.
    start = Str('1.0').tag(pref=True, feval=Feval(types=numbers.Real))

    #: Value at which to stop the loop (included)
    stop = Str('100.0').tag(pref=True, feval=Feval(types=numbers.Real))

    #: Step between loop values.
    num = Str('10').tag(pref=True, feval=Feval(types=numbers.Integral))

    def check(self, *args, **kwargs):
        """Check evaluation of all loop parameters.

        """
        task = self.task
        err_path = task.path + '/' + task.name
        test, traceback = super(GeomspaceLoopInterface,
                                self).check(*args, **kwargs)

        if not test:
            return test, traceback

        #try to generate appropriately rounded geomspace array
        try:
            self.generate_geomspace_array()
        except Exception as e:
            test = False
            mess = 'Loop task did not succeed to create a geomspace array: {}'
            traceback[err_path + '-geomspace'] = mess.format(e)

        return test, traceback

    def perform(self):
        """Build the arange and pass it to the LoopTask.

        """
        task = self.task
        array = self.generate_geomspace_array()
        task.perform_loop(array)
    
    def generate_geomspace_array(self):
        """Helper function for generating the geomspace array
        
        """
        task = self.task

        start = task.format_and_eval_string(self.start)
        stop = task.format_and_eval_string(self.stop)
        num = task.format_and_eval_string(self.num)

        # determine rounding from user input.   
        stop_digit = abs(Decimal(str(stop)).as_tuple().exponent)
        start_digit = abs(Decimal(str(start)).as_tuple().exponent)
        digit = max((start_digit, stop_digit))

        # Round values to the maximal number of digit used in start and stop
        # so that we never get issues with floating point rounding issues.
        raw_values = np.geomspace(start, stop, num)
        array = np.fromiter((round(value, digit)
                                for value in raw_values),
                               np.float64, len(raw_values))
        task.write_in_database('loop_values', np.array(array))

        return array
