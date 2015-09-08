# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Implementaion of the InternalChecks hook.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import os

from ..base_hooks import BasePreExecutionHook


class InternalChecksHook(BasePreExecutionHook):
    """Pre-execution hook running the main task checks.

    """

    def check(self, **kwargs):
        """Run the main task internal checks.

        """
        task = self.measure.root_task
        check, errors = task.checks(**kwargs)

        # Check that no measure with the same name and id is saved in
        # the default path used by the root_task.
        default_filename = (self.measure.name + '_' + self.measure.id +
                            '.meas.ini')
        path = os.path.join(self.measure.root_task.default_path,
                            default_filename)
        if os.path.isfile(path):
            msg = ('A measure file with the same name and id has already '
                   'been saved in %s, increments the id of your measure '
                   'to avoid overwriting it.')
            errors['internal'] = msg % self.measure.root_task.default_path

        return check, errors
