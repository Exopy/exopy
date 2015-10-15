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

from threading import Event

import enaml
from atom.api import Bool, Value

from ecpy.app.dependencies.plugin import RuntimeContainer
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
    fail_perform = Bool()

    waiting = Value(factory=Event)

    go_on = Value(factory=Event)

    def perform(self, exec_infos):
        """Simply return the exec_infos.

        """
        self.waiting.set()
        self.go_on.wait()
        self.waiting.clear()
        self.go_on.clear()

        exec_infos.success = False if self.fail_perform else True
        return exec_infos


class DummyPreHook(BasePreExecutionHook):
    """Dummy pre-execution hook used for testing.

    """
    fail_check = Bool().tag(pref=True)

    waiting = Value(factory=Event)

    go_on = Value(factory=Event)

    def check(self, workbench, **kwargs):
        """Fail the check if the fail_check member is set or 'fail' is found in
        the kwargs.

        """
        if self.fail_check or 'fail' in kwargs:
            return False, 'pre'

        return True, ''

    def run(self, workbench, engine):
        self.waiting.set()
        self.go_on.wait()
        self.waiting.clear()
        self.go_on.clear()

    def list_runtimes(self, workbench):
        """Say that dummy is a dependency.

        """
        with enaml.imports():
            from .contributions import Flags

        deps = RuntimeContainer()

        if Flags.RUNTIME2_FAIL_ANALYSE:
            deps.errors[self.declaration.id] = 'rr'
        else:
            deps.dependencies = {'dummy2': set(['test'])}
        return deps


class DummyMonitor(BaseMonitor):
    """Dummy monitor used for testing.

    """
    def refresh_monitored_entries(self):
        """Do nothing when refreshing.

        """
        pass

    def handle_database_change(self, news):
        """Add all entries to the monitored ones.

        """
        if news[0] == 'added':
            self.monitored_entries = self.monitored_entries + [news[1]]


class DummyPostHook(BasePostExecutionHook):
    """Dummy post execution hook used for testing.

    """
    fail_check = Bool().tag(pref=True)

    waiting = Value(factory=Event)

    go_on = Value(factory=Event)

    def check(self, workbench, **kwargs):
        """Fail the check if the fail_check member is set or 'fail' is found in
        the kwargs.

        """
        if self.fail_check or 'fail_post' in kwargs:
            return False, 'post'

        # Check that Measure.run_checks can handle a None retur value

    def run(self, workbench, engine):
        self.waiting.set()
        self.go_on.wait()
        self.waiting.clear()
        self.go_on.clear()
