# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Interface allowing to use an iterable in a LoopTask.

"""
import numpy

from atom.api import Unicode
from collections import Iterable

from ..task_interface import TaskInterface
from ..validators import Feval


class IterableLoopInterface(TaskInterface):
    """Interface used to loop on a Python iterable.

    """
    #: Iterable on which to iterate.
    iterable = Unicode('range(10)').tag(pref=True, feval=Feval(types=Iterable))

    def check(self, *args, **kwargs):
        """Check that the iterable member evaluation does yield an iterable.

        """
        test, traceback = super(IterableLoopInterface,
                                self).check(*args, **kwargs)
        if not test:
            return test, traceback

        task = self.task
        iterable = task.format_and_eval_string(self.iterable)
        task.write_in_database('point_number', len(iterable))
        task.write_in_database('loop_values', numpy.array(iterable))
        if 'value' in task.database_entries:
            task.write_in_database('value', next(iter(iterable)))

        return test, traceback

    def perform(self):
        """Compute the iterable and pass it to the LoopTask.

        """
        task = self.task
        iterable = task.format_and_eval_string(self.iterable)

        task.perform_loop(iterable)
