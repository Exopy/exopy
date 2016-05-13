# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Task allowing to use a while statement.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import (Unicode, set_default)

from ..validators import Feval
from ..base_tasks import ComplexTask
from .loop_exceptions import BreakException, ContinueException
from ..decorators import handle_stop_pause


class WhileTask(ComplexTask):
    """ Task breaking out of a loop when a condition is met.

    See Python break statement documenttaion.

    """
    #: Condition under which to continue looping.
    condition = Unicode().tag(pref=True, feval=Feval())

    database_entries = set_default({'index': 1})

    def perform(self):
        """Loop as long as condition evaluates to True.

        """
        i = 1
        root = self.root
        while True:
            self.write_in_database('index', i)
            i += 1
            if not self.format_and_eval_string(self.condition):
                break

            if handle_stop_pause(root):
                return

            try:
                for child in self.children:
                    child.perform_()
            except BreakException:
                break
            except ContinueException:
                continue

KNOWN_PY_TASKS = [WhileTask]
