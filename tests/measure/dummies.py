# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Dummy engines, editors and measure tools used for testing.

Those are contributed by the manifest found in contributions.enaml

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import Bool

from ecpy.measure.editors.api import BaseEditor
from ecpy.measure.hooks.api import BasePreExecutionHook, BasePostExecutionHook
from ecpy.measure.engines.api import BaseEngine
from ecpy.measure.monitors.api import BaseMonitor


class DummyEditor(BaseEditor):
    """Dummy editor used for testing.

    """
    pass


class DummyEngine(BaseEngine):
    """Dummy engine used for testing.

    """
    pass


class DummyPreHook(BasePreExecutionHook):
    """Dummy pre-execution hook used for testing.

    """
    fail_check = Bool().tag(pref=True)

    def check(self, workbench, **kwargs):
        """Fail the check if the fail_check member is set or 'fail' is found in
        the kwargs.

        """
        if self.fail_check or 'fail' in kwargs:
            return False, 'pre'

        return True, ''


class DummyMonitor(BaseMonitor):
    """Dummy monitor used for testing.

    """
    pass


class DummyPostHook(BasePostExecutionHook):
    """Dummy post execution hook used for testing.

    """
    fail_check = Bool().tag(pref=True)

    def check(self, workbench, **kwargs):
        """Fail the check if the fail_check member is set or 'fail' is found in
        the kwargs.

        """
        if self.fail_check or 'fail_post' in kwargs:
            return False, 'post'

        # Check that Measure.run_checks can handle a None retur value
