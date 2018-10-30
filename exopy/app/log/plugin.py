# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Log plugin definition.

"""
import os
import logging

from atom.api import Unicode, Dict, List, Tuple, Typed
from enaml.workbench.api import Plugin

from .tools import (LogModel, GuiHandler, DayRotatingTimeHandler)

import enaml
with enaml.imports():
    from .widgets import LogDialog


MODULE_PATH = os.path.dirname(__file__)


class LogPlugin(Plugin):
    """Plugin managing the application logging.

    """
    #: List of installed handlers.
    handler_ids = List(Unicode())

    #: List of installed filters.
    filter_ids = List(Unicode())

    #: Model which can be used to display the log in the GUI. It is associated
    #: to a handler attached to the root logger.
    gui_model = Typed(LogModel)

    # Current log
    rotating_log = Typed(DayRotatingTimeHandler)

    def display_current_log(self):
        """Display the current instance of the rotating log file.

        """
        with open(self.rotating_log.path) as f:
            log = f.read()
        LogDialog(log=log).exec_()

    def add_handler(self, id, handler=None, logger='', mode=None):
        """Add a handler to the specified logger.

        Parameters
        ----------
        id : unicode
            Id of the new handler. This id should be unique.

        handler : logging.Handler, optional
            Handler to add.

        logger : unicode, optional
            Name of the logger to which the handler should be added. By default
            the handler is added to the root logger.

        mode : {'ui', }, optional
            Conveninence to add a simple logger. If this argument is specified,
            handler will be ignored and the command will return useful
            references (the model to which can be connected a ui for the 'ui'
            mode).

        Returns
        -------
        refs : list
            List of useful reference, empty if no mode is selected.

        """
        refs = []
        if not handler:
            if mode and mode == 'ui':
                model = LogModel()
                handler = GuiHandler(model=model)
                refs.append(model)
            else:
                logger = logging.getLogger(__name__)
                msg = ('Missing handler or recognised mode when adding '
                       'log handler under id %s to logger %s')
                logger.info(msg, id, logger)
                return []

        name = logger
        logger = logging.getLogger(name)

        logger.addHandler(handler)

        self._handlers[id] = (handler, name)
        self.handler_ids = list(self._handlers.keys())

        if refs:
            return refs

    def remove_handler(self, id):
        """Remove the specified handler.

        Parameters
        ----------
        id : unicode
            Id of the handler to remove.

        """
        handlers = self._handlers
        if id in handlers:
            handler, logger_name = handlers.pop(id)
            logger = logging.getLogger(logger_name)
            logger.removeHandler(handler)
            for filter_id in self.filter_ids:
                infos = self._filters[filter_id]
                if infos[1] == id:
                    del self._filters[filter_id]

            self.filter_ids = list(self._filters.keys())
            self.handler_ids = list(self._handlers.keys())

    def add_filter(self, id, filter, handler_id):
        """Add a filter to the specified handler.

        Parameters
        ----------
        id : unicode
            Id of the filter to add.

        filter : object
            Filter to add to the specified handler (object implemeting a filter
            method).

        handler_id : unicode
            Id of the handler to which this filter should be added

        """
        if not hasattr(filter, 'filter'):
            logger = logging.getLogger(__name__)
            logger.warning('Filter does not implemet a filter method')
            return

        handlers = self._handlers
        if handler_id in handlers:
            handler, _ = handlers[handler_id]
            handler.addFilter(filter)
            self._filters[id] = (filter, handler_id)

            self.filter_ids = list(self._filters.keys())

        else:
            logger = logging.getLogger(__name__)
            logger.warning('Handler {} does not exist')

    def remove_filter(self, id):
        """Remove the specified filter.

        Parameters
        ----------
        id : unicode
            Id of the filter to remove.

        """
        filters = self._filters
        if id in filters:
            filter, handler_id = filters.pop(id)
            handler, _ = self._handlers[handler_id]
            handler.removeFilter(filter)
            self.filter_ids = list(self._filters.keys())

    def set_formatter(self, handler_id, formatter):
        """Set the formatter of the specified handler.

        Parameters
        ----------
        handler_id : unicode
            Id of the handler whose formatter shoudl be set.

        formatter : Formatter
            Formatter for the handler.

        """
        handlers = self._handlers
        handler_id = str(handler_id)
        if handler_id in handlers:
            handler, _ = handlers[handler_id]
            handler.setFormatter(formatter)

        else:
            logger = logging.getLogger(__name__)
            logger.warning('Handler {} does not exist')

    # ---- Private API --------------------------------------------------------

    # Mapping between handler ids and handler, logger name pairs.
    _handlers = Dict(Unicode(), Tuple())

    # Mapping between filter_id and filter, handler_id pairs.
    _filters = Dict(Unicode(), Tuple())
