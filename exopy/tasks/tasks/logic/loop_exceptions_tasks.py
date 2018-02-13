# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Tasks used to modify the execution of a loop.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import (Unicode, set_default)

from ..validators import Feval
from ..base_tasks import SimpleTask
from .loop_task import LoopTask
from .while_task import WhileTask
from .loop_exceptions import BreakException, ContinueException


class BreakTask(SimpleTask):
    """ Task breaking out of a loop when a condition is met.

    See Python break statement documenttaion.

    """
    #: Condition under which to perform the break.
    condition = Unicode().tag(pref=True, feval=Feval())

    #: Never run this task in parallel.
    parallel = set_default({'forbidden': True})

    def check(self, *args, **kwargs):
        """Check that the parent makes sense

        """
        test, traceback = super(BreakTask, self).check(*args, **kwargs)

        if not isinstance(self.parent, (LoopTask, WhileTask)):
            test = False
            mess = 'Incorrect parent type: {}, expected LoopTask or WhileTask.'
            traceback[self.path + '/' + self.name + '-parent'] = \
                mess.format(self.parent.task_id)

        return test, traceback

    def perform(self):
        """If the condition evaluates to true, break from the loop.

        """
        if self.format_and_eval_string(self.condition):
            raise BreakException()


class ContinueTask(SimpleTask):
    """Task jumping to next loop iteration when a condition is met.

    See Python continue statement documenttaion.

    """
    #: Condition under which to continue.
    condition = Unicode().tag(pref=True, feval=Feval())

    #: Never run this task in parallel.
    parallel = set_default({'forbidden': True})

    def check(self, *args, **kwargs):
        """Check that the parent makes sense

        """
        test, traceback = super(ContinueTask, self).check(*args, **kwargs)

        if not isinstance(self.parent, (LoopTask, WhileTask)):
            test = False
            mess = 'Incorrect parent type: {}, expected LoopTask or WhileTask.'
            traceback[self.path + '/' + self.name + '-parent'] = \
                mess.format(self.parent.task_id)

        return test, traceback

    def perform(self):
        """"If the condition evaluates to true, continue.

        """
        if self.format_and_eval_string(self.condition):
            raise ContinueException()
