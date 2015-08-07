# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Base classes for all monitors.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import List, Str, Bool

from ..base_tools import BaseMeasureTool, BaseToolDeclaration


class BaseMonitor(BaseMeasureTool):
    """ Base class for all monitors.

    """
    # List of database which should be observed
    database_entries = List(Str())

    # Whether or not to show the monitor on start-up
    auto_show = Bool(True).tag(pref=True)

    def start(self, parent_ui):
        """Start the activity of the monitor.

        It is the reponsability of the monitor to display any widget,
        the provided widget can be used as parent. The auto-show member value
        should be respected.

        Parameters
        ----------
        parent_ui : Widget
            Enaml widget to use as a parent for any ui to be shown.

        """
        raise NotImplementedError()

    def stop(self):
        """Stop the activity of the monitor.

        If the monitor opened any window it is responsability to close them at
        this point.

        """
        raise NotImplementedError()

    # TODO more explicit docstring
    def refresh_monitored_entries(self, entries={}):
        """Refresh all the entries of the monitor.

        Parameters
        ----------
        entries : dict(str), optionnal
            Dict of the database entries to consider, if empty the already
            known entries will be used.

        """
        raise NotImplementedError()

    def process_news(self, news):
        """Handle news received from the engine.

        This method will be connected to the news signal of the engine when
        the measure is started. The value received will be a tuple containing
        the name of the updated database entry and its new value.

        """
        raise NotImplementedError()

    def clear_state(self):
        """Clear the monitor state.

        """
        pass

    def show_monitor(self, parent_ui):
        """Show the monitor if pertinent using the provided parent.

        By default this is a no-op assuming the monitor has no ui. If a ui is
        already active it should be a no-op or restore the monitor.

        Parameters
        ----------
        parent_ui : enaml.widgets.Widget
            Parent to use for the display.

        """
        pass


class Monitor(BaseToolDeclaration):
    """A declarative class for defining a measure monitor contribution.

    Monitor object can be contributed as extensions child to the
    'monitors' extension point of the 'ecpy.measure' plugin.

    The name member inherited from enaml.core.Object should always be set to an
    easily understandable name for the user.

    """
    pass
