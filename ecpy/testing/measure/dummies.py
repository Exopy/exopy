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

from time import sleep
from threading import Event

import enaml
from atom.api import Atom, Bool, List, Value, set_default

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

    should_pause = Bool()

    accept_pause = Bool(True)

    should_resume = Bool()

    measure_force_enqueued = Bool()

    signal_resuming = Value(factory=Event)

    go_on_resuming = Value(factory=Event)

    signal_resumed = Value(factory=Event)

    go_on_resumed = Value(factory=Event)

    _stop = Bool()

    def perform(self, exec_infos):
        """Simply return the exec_infos.

        """
        self.measure_force_enqueued = not exec_infos.checks
        self.waiting.set()
        self.progress(('test', True))
        self.go_on.wait()
        if self.accept_pause and self.should_pause:
            self.status = 'Pausing'
            sleep(0.001)
            self.status = 'Paused'
            while True:
                if self.should_resume:
                    self.signal_resuming.set()
                    self.status = 'Resuming'
                    self.go_on_resuming.wait()
                    self.status = 'Running'
                    break
                sleep(0.001)
            self.signal_resumed.set()
            self.go_on_resumed.wait()
        if self._stop:
            return exec_infos
        self.waiting.clear()
        self.go_on.clear()
        exec_infos.success = False if self.fail_perform else True
        return exec_infos

    def pause(self):
        self.should_pause = True

    def resume(self):
        self.should_resume = True

    def stop(self, force=False):
        """Stop the execution.

        """
        self._stop = True

    def shutdown(self, force=False):
        if force:
            self.status = 'Stopped'


class DummyHook(Atom):
    fail_check = Bool().tag(pref=True)

    fail_run = Bool()

    should_pause = Bool()

    accept_pause = Bool(True)

    should_resume = Bool()

    stop_called = Bool()

    waiting = Value(factory=Event)

    go_on = Value(factory=Event)

    signal_resuming = Value(factory=Event)

    go_on_resuming = Value(factory=Event)

    signal_resumed = Value(factory=Event)

    go_on_resumed = Value(factory=Event)

    def run(self, workbench, engine):
        self.waiting.set()
        self.go_on.wait()
        if self.fail_run:
            raise RuntimeError()
        if self.accept_pause and self.should_pause:
            self.paused = True
            while True:
                sleep(0.001)
                if self.should_resume:
                    self.signal_resuming.set()
                    self.go_on_resuming.wait()
                    self.resumed = True
                    break
            self.signal_resumed.set()
            self.go_on_resumed.wait()

        self.waiting.clear()
        self.go_on.clear()

    def pause(self):
        self.should_pause = True

    def resume(self):
        self.should_resume = True

    def stop(self, force=False):
        self.stop_called = True


class DummyPreHook(DummyHook, BasePreExecutionHook):
    """Dummy pre-execution hook used for testing.

    """
    def check(self, workbench, **kwargs):
        """Fail the check if the fail_check member is set or 'fail' is found in
        the kwargs.

        """
        if self.fail_check or 'fail' in kwargs:
            return False, 'pre'

        return True, ''

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
    running = Bool()

    monitored_entries = set_default(['default_path'])

    received_news = List()

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def refresh_monitored_entries(self, entries=None):
        """Do nothing when refreshing.

        """
        pass

    def handle_database_change(self, news):
        """Add all entries to the monitored ones.

        """
        if news[0] == 'added':
            self.monitored_entries = self.monitored_entries + [news[1]]

    def process_news(self, news):
        self.received_news.append(news)


class DummyPostHook(DummyHook, BasePostExecutionHook):
    """Dummy post execution hook used for testing.

    """
    def check(self, workbench, **kwargs):
        """Fail the check if the fail_check member is set or 'fail' is found in
        the kwargs.

        """
        if self.fail_check or 'fail_post' in kwargs:
            return False, 'post'

        # Check that Measure.run_checks can handle a None retur value
