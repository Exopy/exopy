# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Validators for feval members.

"""
from atom.api import Atom, Value, Bool

from ...utils.traceback import format_exc


class Feval(Atom):
    """Object hanlding the validation of feval tagged member.

    """
    #: Allowed types for the result of the evaluation of the member.
    types = Value()

    #: Should the validator propagate an error or simply warn the user.
    warn = Bool()

    def check(self, task_or_interface, member):
        """Validate the feval formula.

        """
        str_value = getattr(task_or_interface, member)
        if not self.should_test(task_or_interface, str_value):
            return None, True, ''

        msg = ''
        val = None
        try:

            task = (task_or_interface.task
                    if task_or_interface.dep_type == 'exopy.tasks.interface'
                    else task_or_interface)
            val = task.format_and_eval_string(str_value)
        except Exception:
            msg = 'Failed to eval %s : %s' % (member, format_exc())

        if not msg:
            val, msg = self.validate(task_or_interface, val)

        res = bool(not msg or (msg and self.warn))

        return val, res, msg

    def should_test(self, task, str_value):
        """Should the value actually be tested given its value and the task.

        """
        return True

    def validate(self, task, value):
        """Validate that the value resulting from the evaluation makes sense.

        """
        if self.types:
            if not isinstance(value, self.types):
                msg = 'Expected value should of types {}, got {}.'
                return None, msg.format(self.types, type(value))

        return value, ''


class SkipEmpty(Feval):
    """Specialized validator skipping empty fields.

    """
    def should_test(self, task, str_value):
        """Only test if a formula is provided.

        """
        return bool(str_value)


class SkipLoop(Feval):
    """Specialized validator skipping empty field if task is embedded inside
    a LoopTask.

    """
    def should_test(self, task, str_value):
        """Only test if not embedded in a LoopTask.

        """
        from .logic.loop_task import LoopTask
        if isinstance(task.parent, LoopTask) and task.parent.task is task:
            return False
        else:
            return True
