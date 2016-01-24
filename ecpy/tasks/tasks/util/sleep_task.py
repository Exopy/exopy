# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Task that makes the system wait on all multithreading pools
for a set amount of time.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import (Unicode, set_default)
from time import sleep

from ...base_tasks import SimpleTask


class SleepTask(SimpleTask):
    """Simply sleeps for the specified amount of time.
    Wait for any parallel operation before execution by default.
    """

    # Class attribute marking this task as being logical, used in filtering.
    util_task = True

    # Time to wait
    time = Unicode().tag(pref=True, feval=True)

    wait = set_default({'': True})

    database_entries = set_default({'time': 1})

    def perform(self):
        t = self.format_and_eval_string(self.time)
        self.write_in_database('time', t)
        sleep(t)

    def check(self, *args, **kwargs):
        """ Check if time > 0

        """
        test, tb = super(SleepTask, self).check(*args, **kwargs)
        if test and self.format_and_eval_string(self.time) < 0:
            tb[self.path + '/' + self.name] = 'Sleep time must be positive.'
            test = False

        return test, tb
