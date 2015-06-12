# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Plugin centralizing the application error handling.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import List, Typed, Int
from enaml.workbench.api import Plugin

from .errors import ErrorHandler
from ..utils.plugin_tools import ExtensionCollector


class ErrorPlugin(Plugin):
    """Plugin in charge of collecting of the errors.

    It will always log the errors, and will notify the user according to their
    type.

    """
    #: Errors for which a custom handler is regsitered.
    errors = List()

    def start(self):
        """
        """
        pass

    def stop(self):
        """
        """
        pass

    def signal(self, kind, **kwargs):
        """Signal an error occured in the system.

        Parameters
        ----------
        kind : unicode or None
            Kind of error which occurred. If a specific handler is found, it is
            used, otherwise the generic handling method is used.

        **kwargs :
            Arguments to pass to the error handler.

        """
        pass

    def enter_error_gathering(self):
        """In gathering mode, error handling is differed till exiting the mode.

        """
        pass

    def exit_error_gathering(self):
        """Upon leaving gathering mode, errors are handled.

        If error handling should lead to a window display, all widgets are
        collected and displayed in a single window.
        As the gathering mode can be requested many times, the errors are only
        handled when this method has been called as many times as its
        counterpart.

        """
        pass

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: Contributed error handlers.
    _errors_handlers = Typed(ExtensionCollector)

    #: Counter keeping track of how many times the gathering mode was entered
    #: the mode is exited only when the value reaches 0.
    _gathering_counter = Int()

    def _update_errors(self, change):
        """Update th lis of supported errors when the registered handlers
        change

        """
        self.errors = list(self._errors_handlers.contributions)
