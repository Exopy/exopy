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

from collections import defaultdict
from inspect import cleandoc
from pprint import pformat
from traceback import format_exc

from atom.api import List, Typed, Int
from enaml.workbench.api import Plugin

from .errors import ErrorHandler
from .widgets import ErrorsDialog, UnknownErrorWidget
from .standard_handlers import handle_unkwown_error
from ..utils.plugin_tools import ExtensionsCollector


ERR_HANDLER_POINT = 'ecpy.app.errors.handler'


def check_handler(handler):
    """Ensure that the handler does implement a handle method and provide a
    description.

    """
    if not handler.description:
        return False, 'Handler %s does not provide a description' % handler.id

    if handler.handle is ErrorHandler.handle:
        msg = 'Handler %s does not implement a handle method'
        return False, msg % handler.id


class ErrorPlugin(Plugin):
    """Plugin in charge of collecting of the errors.

    It will always log the errors, and will notify the user according to their
    type.

    """
    #: Errors for which a custom handler is regsitered.
    errors = List()

    def start(self):
        """Collect extensions.

        """
        self._errors_handlers = ExtensionsCollector(workbench=self.workbench,
                                                    point=ERR_HANDLER_POINT,
                                                    ext_type=ErrorHandler,
                                                    validate_ext=check_handler)
        self._errors_handlers.start()

    def stop(self):
        """Stop the extension collector and clear the list of handlers.

        """
        self._errors_handlers.stop()
        self.errors = []

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
        if self._gathering_counter:
            self._delayed[kind].append(kwargs)
            return

        widget = self._handle(kind, kwargs)

        if widget:
            # Show dialog in application modal mode
            dial = ErrorsDialog(errors={kind: widget})
            dial.exec_()

    def report(self, kind=None):
        """Show a widget summarizing all the errors.

        Parameters
        ----------
        kind : unicode, optional
            If specified only the error related to the specified kind will
            be reported.

        """
        errors = {}
        if kind:
            if kind not in self._errors_handlers:
                msg = '''{} is not a registered error kind (it has no
                    associated handler)'''.format(kind)
                self.signal(None,
                            {'message': cleandoc(msg).replace('\n', ' ')})
                return

            errors[kind] = self._errors_handlers[kind].report()

        else:
            for kind in self._errors_handlers:
                errors[kind] = self._errors_handlers[kind].report()

        dial = ErrorsDialog(errors=errors)
        dial.exec_()

    def enter_error_gathering(self):
        """In gathering mode, error handling is differed till exiting the mode.

        """
        self._gathering_counter += 1

    def exit_error_gathering(self):
        """Upon leaving gathering mode, errors are handled.

        If error handling should lead to a window display, all widgets are
        collected and displayed in a single window.
        As the gathering mode can be requested many times, the errors are only
        handled when this method has been called as many times as its
        counterpart.

        """
        self._gathering_counter -= 1
        if self._gathering_counter < 1:
            # handle all delayed errors
            errors = {}
            for kind in self._delayed:
                errors[kind] = self._handle(kind, self._delayed[kind])

            self._delayed = {}
            dial = ErrorsDialog(errors=errors)
            dial.exec_()

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: Contributed error handlers.
    _errors_handlers = Typed(ExtensionsCollector)

    #: Counter keeping track of how many times the gathering mode was entered
    #: the mode is exited only when the value reaches 0.
    _gathering_counter = Int()

    #: List of pairs (kind, kwargs) representing the error reports received
    #: while the gathering mode was active.
    _delayed = Typed(defaultdict, list)

    def _update_errors(self, change):
        """Update th lis of supported errors when the registered handlers
        change

        """
        self.errors = list(self._errors_handlers.contributions)

    def _handle(self, kind, infos):
        """Dispatch error report to appropriate handler.

        """
        if kind in self._errors_handlers:
            handler = self._errors_handlers[kind]
            return handler.handle(self.workbench, infos)

        else:
            return handle_unkwown_error(self.workbench, kind, infos)

    def _handle_unknwon(self, kind, infos):
        """Generic handler for unregistered kind of errors.

        """
        try:
            # Delayed handling of errors
            if not isinstance(infos, dict):
                msg = '\n\n'.join((pformat(i) for i in infos))

            else:
                msg = pformat(infos)

        except Exception:
            msg = 'Failed to format the errors infos.\n' + format_exc()

        return UnknownErrorWidget(kind=kind, msg=msg)