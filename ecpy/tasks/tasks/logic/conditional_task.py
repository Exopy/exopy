# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Task equivalent to an if statement.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import (Unicode)

from ...base_tasks import ComplexTask


class ConditionalTask(ComplexTask):
    """Task calling its children only if a given condition is met.

    """
    #: Class attribute marking this task as being logical, used in filtering.
    logic_task = True

    #: Condition to meet in order to perform the children tasks.
    condition = Unicode().tag(pref=True, feval=True)

    def perform(self):
        """Call the children task if the condition evaluate to True.

        """
        if self.format_and_eval_string(self.condition):
            for child in self.children_task:
                child.perform_(child)
