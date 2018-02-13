# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
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
from ..utils.plugin_tools import ExtensionsCollector, make_extension_validator
from .app_extensions import AppStartup, AppClosing, AppClosed


STARTUP_POINT = 'exopy.app.startup'

CLOSING_POINT = 'exopy.app.closing'

CLOSED_POINT = 'exopy.app.closed'


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
        validator = make_extension_validator(AppStartup, ('run',), ())
        self.startup = ExtensionsCollector(workbench=self.workbench,
                                           point=STARTUP_POINT,
                                           ext_class=AppStartup,
                                           validate_ext=validator)

        validator = make_extension_validator(AppClosing, ('validate',), ())
        self.closing = ExtensionsCollector(workbench=self.workbench,
                                           point=CLOSING_POINT,
                                           ext_class=AppClosing,
                                           validate_ext=validator)

        validator = make_extension_validator(AppClosed, ('clean',), ())
        self.closed = ExtensionsCollector(workbench=self.workbench,
                                          point=CLOSED_POINT,
                                          ext_class=AppClosed,
                                          validate_ext=validator)

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
        for runner in self._start_heap:
            runner.run(self.workbench, cmd_args)

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
        for cleaner in self._clean_heap:
            cleaner.clean(self.workbench)

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: Priority heap storing contributed AppStartup by priority.
    _start_heap = Typed(PriorityHeap, ())

    #: Priority heap storing contributed AppClosed by priority.
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
            heap.remove(r)

        for a in added:
            heap.push(a.priority, a)
