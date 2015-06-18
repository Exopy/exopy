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

import logging
from collections import defaultdict
from inspect import cleandoc
from pprint import pformat
from traceback import format_exc

import enaml
from atom.api import List, Typed, Int
from enaml.workbench.api import Plugin

from .errors import ErrorHandler
from ...utils.plugin_tools import ExtensionsCollector

with enaml.imports():
    from .widgets import ErrorsDialog, UnknownErrorWidget


ERR_HANDLER_POINT = 'ecpy.app.errors.handler'

logger = logging.getLogger(__name__)


def check_handler(handler):
    """Ensure that the handler does implement a handle method and provide a
    description.

    """
    if not handler.description:
        return False, 'Handler %s does not provide a description' % handler.id

    func = getattr(handler.handle, 'im_func',
                   getattr(handler.handle, '__func__', None))
    if not func or func is ErrorHandler.handle.__func__:
        msg = 'Handler %s does not implement a handle method'
        return False, msg % handler.id

    return True, ''


class ErrorsPlugin(Plugin):
    """Plugin in charge of collecting of the errors.

    It will always log the errors, and will notify the user according to their
    type.

    """
    #: Errors for which a custom handler is registered.
    errors = List()

    def start(self):
        """Collect extensions.

        """
        self._errors_handlers = ExtensionsCollector(workbench=self.workbench,
                                                    point=ERR_HANDLER_POINT,
                                                    ext_class=ErrorHandler,
                                                    validate_ext=check_handler)
        self._errors_handlers.start()
        self._update_errors(None)

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
        handlers = self._errors_handlers.contributions
        errors = {}
        if kind:
            if kind not in handlers:
                msg = '''{} is not a registered error kind (it has no
                    associated handler)'''.format(kind)
                self.signal('error',
                            message=cleandoc(msg).replace('\n', ' '))
                return

            handlers = {kind: handlers[kind]}

        for kind in handlers:
            report = handlers[kind].report(self.workbench)
            if report:
                errors[kind] = report

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
            # Make sure to also gather additional errors signal during errors
            # handling
            self._gathering_counter += 1

            # Handle all delayed errors
            errors = {}
            while self._delayed:
                delayed = self._delayed.copy()
                self._delayed.clear()
                for kind in delayed:
                    res = self._handle(kind, delayed[kind])
                    if res:
                        errors[kind] = res

            self._gathering_counter = 0

            if errors:
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
    _delayed = Typed(defaultdict, (list,))

    def _update_errors(self, change):
        """Update the list of supported errors when the registered handlers
        change

        """
        self.errors = list(self._errors_handlers.contributions)

    def _handle(self, kind, infos):
        """Dispatch error report to appropriate handler.

        """
        if kind in self._errors_handlers.contributions:
            handler = self._errors_handlers.contributions[kind]
            try:
                return handler.handle(self.workbench, infos)
            except Exception:
                try:
                    msg = ('Failed to handle %s error, infos were:\n' % kind
                           + pformat(infos) + '\nError was :\n' + format_exc())
                except Exception:
                    msg = ('Failed to handle %s error, and to ' % kind +
                           'format infos:\n' + format_exc())
                core = self.workbench.get_plugin('enaml.workbench.core')
                core.invoke_command('ecpy.app.errors.signal',
                                    dict(kind='error', message=msg))

        else:
            return self._handle_unknwon(kind, infos)

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

        logger.debug('No handler found for "%s" kind of error:\n %s',
                     kind, msg)

        return UnknownErrorWidget(kind=kind, msg=msg)
