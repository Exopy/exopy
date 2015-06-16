# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Application plugin handling the application startup and closing.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import Typed
from enaml.workbench.api import Plugin

from ..utils.priority_heap import PriorityHeap
from ..utils.plugin_tools import ExtensionsCollector
from .app_extensions import AppStartup, AppClosing, AppClosed


STARTUP_POINT = 'ecpy.app.startup'

CLOSING_POINT = 'ecpy.app.closing'

CLOSED_POINT = 'ecpy.app.closed'


def validate_startup(startup):
    """Assert that the startup does declare a run method.

    """
    msg = "AppStartup '%s' does not declare a run method"
    return startup.run.__func__ is AppStartup.run.__func__, msg % startup.id


def validate_closing(closing):
    """Assert that the closing does declare a validate method.

    """
    msg = "AppClosing '%s' does not declare a validate method"
    return (closing.validate.__func__ is AppClosing.validate.__func__,
            msg % closing.id)


def validate_closed(closed):
    """Assert that the closed does declare a clean method.

    """
    msg = "AppClosed '%s' does not declare a clean method"
    return closed.clean.__func__ is AppClosed.clean.__func__, msg % closed.id


class AppPlugin(Plugin):
    """ A plugin to manage application life cycle.

    """

    #: Collect all contributed AppStartup extensions.
    startup = Typed(ExtensionsCollector)

    #: Collect all contributed AppClosing extensions.
    closing = Typed(ExtensionsCollector)

    #: Collect all contributed AppClosed extensions.
    closed = Typed(ExtensionsCollector)

    def start(self):
        """Start the plugin life-cycle.

        This method is called by the framework at the appropriate time. It
        should never be called by user code.

        """
        self.startup = ExtensionsCollector(workbench=self.workbench,
                                           point=STARTUP_POINT,
                                           ext_class=AppStartup,
                                           validate_ext=validate_startup)
        self.closing = ExtensionsCollector(workbench=self.workbench,
                                           point=CLOSING_POINT,
                                           ext_class=AppClosing,
                                           validate_ext=validate_closing)
        self.closed = ExtensionsCollector(workbench=self.workbench,
                                          point=CLOSED_POINT,
                                          ext_class=AppClosed,
                                          validate_ext=validate_closed)

        self.startup.observe('contributions', self._update_heap)
        self.closed.observe('contributions', self._update_heap)
        self.startup.start()
        self.closing.start()
        self.closed.start()

    def stop(self):
        """Stop the plugin life-cycle.

        This method is called by the framework at the appropriate time.
        It should never be called by user code.

        """
        self.startup.unobserve('contributions', self._update_heap)
        self.closed.unobserve('contributions', self._update_heap)
        self.startup.stop()
        self.closing.stop()
        self.closed.stop()
        del self.startup, self.closing, self.closed
        del self._start_heap, self._clean_heap

    def run_app_startup(self, cmd_args):
        """Run all the registered app startups based on their priority.

        """
        for run in self._start_heap:
            run(self.workbench, cmd_args)

    def validate_closing(self, window, event):
        """Run all closing checks to determine whether or not to close the app.

        """
        for closing in self.closing.contributions.values():
            closing.validate(window, event)
            if not event.is_accepted():
                break

    def run_app_cleanup(self):
        """Run all the registered app closed based on their priority.

        """
        for clean in self._clean_heap:
            clean(self.workbench)

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: Priority heap storing contributed AppStartup.run by priority.
    _start_heap = Typed(PriorityHeap, ())

    #: Priority heap storing contributed AppClosed.clean by priority.
    _clean_heap = Typed(PriorityHeap, ())

    def _update_heap(self, change):
        """Update the heap corresponding to the updated contribution.

        This does not need to rely on container notifications as the
        contributions replaced after each update.

        """
        attr = 'run' if change['object'] is self.startup else 'clean'
        heap = self._start_heap if attr == 'run' else self._clean_heap
        old = set(change['oldvalue'].values()) if 'oldvalue' in change \
            else set()
        new = set(change['value'].values())

        removed = old - new
        added = new - old

        for r in removed:
            heap.remove(getattr(r, attr))

        for a in added:
            heap.push(a.priority, getattr(a, attr))
