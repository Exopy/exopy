# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Interface allowing to use an iterable in a LoopTask.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import Unicode
from collections import Iterable

from ..task_interface import TaskInterface


class IterableLoopInterface(TaskInterface):
    """Interface used to loop on a Python iterable.

    """
    #: Iterable on which to iterate.
    iterable = Unicode('0.0').tag(pref=True, feval=True)

    def check(self, *args, **kwargs):
        """Check that the iterable member evaluation does yield an iterable.

        """
        test, traceback = super(IterableLoopInterface).check(*args, **kwargs)
        if not test:
            return test, traceback

        task = self.task
        iterable = task.format_and_eval_string(self.iterable)
        if isinstance(iterable, Iterable):
            task.write_in_database('point_number', len(iterable))
            if 'value' in task.task_database_entries:
                task.write_in_database('value', next(iter(iterable)))
        else:
            test = False
            traceback[task.path + '_' + task.name] = \
                'The computed iterable is not iterable.'

        return test, traceback

    def perform(self):
        """Compute the iterable and pass it to the LoopTask.

        """
        task = self.task
        iterable = task.format_and_eval_string(self.iterable)

        task.perform_loop(iterable)
