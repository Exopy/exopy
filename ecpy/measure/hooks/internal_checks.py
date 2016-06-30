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

from .base_hooks import BasePreExecutionHook


class InternalChecksHook(BasePreExecutionHook):
    """Pre-execution hook running the main task checks.

    """

    def check(self, workbench, **kwargs):
        """Run the main task internal checks.

        """
        # Short names
        meas = self.measure
        task = meas.root_task

        # Running the checks
        check, errors = task.check(**kwargs)

        # Check that no measure with the same name and id is saved in
        # the default path used by the root_task.
        default_filename = (meas.name + '_' + meas.id + '.meas.ini')
        path = os.path.join(task.default_path, default_filename)
        if os.path.isfile(path):
            msg = ('A measure file with the same name and id has already '
                   'been saved in %s, increments the id of your measure '
                   'to avoid overwriting it.')
            errors['internal'] = msg % task.default_path

        # Check that we can access all the build dependencies.
        b_deps = meas.dependencies.get_build_dependencies()
        if b_deps.errors:
            errors = b_deps.errors
            check = False

        return check, errors
