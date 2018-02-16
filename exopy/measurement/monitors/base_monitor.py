# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Base classes for all monitors.

"""
from atom.api import List, Typed, Bool
from enaml.core.api import d_, d_func
from enaml.widgets.api import DockItem

from ..base_tool import BaseMeasureTool, BaseToolDeclaration


class BaseMonitor(BaseMeasureTool):
    """ Base class for all monitors.

    """
    #: List of database entries which should be observed
    monitored_entries = List()

    def start(self):
        """Start the activity of the monitor.

        When this method is called the monitor is already observing the engine
        and connected to its view.

        """
        pass

    def stop(self):
        """Stop the activity of the monitor.

        When this method is invoked the monitor is no longer observing the
        engine.

        """
        pass

    def refresh_monitored_entries(self, entries=None):
        """Refresh all the entries of the monitor.

        Parameters
        ----------
        entries : dict[unicode], optionnal
            Dict of the database entries to consider, if empty the already
            known entries will be used. Entries should be specified using their
            full path.

        """
        raise NotImplementedError()

    def handle_database_entries_change(self, news):
        """Handle a modification of the database entries.

        Parameters
        ----------
        news : tuple|list
            Modification passed as a tuple ('added', path, value) for creation,
            as ('renamed', old, new, value) in case of renaming,
            ('removed', old) in case of deletion or as a list of such tuples.

        """
        raise NotImplementedError()

    def handle_database_node_change(self, news):
        """Handle a modification of the database nodes.

        Parameters
        ----------
        news : tuple|list
            Modification passed as a tuple ('added', path, name, node) for
            creation or as ('renamed', path, old, new) in case of renaming of
            the related node, as ('removed', path, old) in case of deletion or
            as a list of such tuples.

        """
        raise NotImplementedError()

    def process_news(self, news):
        """Handle news received from the engine.

        This method will be connected to the news signal of the engine when
        the measurement is started. The value received will be a tuple
        containing the name of the updated database entry and its new value.

        This method is susceptible to be called in a thread that is not the GUI
        thread. Any update of members that are connected to the view should be
        done using enaml.application.deferred_call/schedule.

        """
        raise NotImplementedError()

    def link_to_measurement(self, measurement):
        """Start observing the main task database.

        """
        super(BaseMonitor, self).link_to_measurement(measurement)
        if measurement.root_task:
            database = measurement.root_task.database
            database.observe('notifier', self.handle_database_entries_change)
            database.observe('nodes_notifier',
                             self.handle_database_nodes_change)

    def unlink_from_measurement(self):
        """Stop observing the main task database.

        """
        meas = self.measurement
        if meas.root_task:
            database = meas.root_task.database
            database.unobserve('notifier', self.handle_database_entries_change)
            database.unobserve('nodes_notifier',
                               self.handle_database_nodes_change)
        super(BaseMonitor, self).unlink_from_measurement()


class BaseMonitorItem(DockItem):
    """Base class for the view associated with a monitor.

    """
    #: Reference to the monitor driving this view. This is susceptible to
    #: change during the lifetime of the widget.
    monitor = d_(Typed(BaseMonitor))

    #: Should this item be made floating by default.
    float_default = d_(Bool())


class Monitor(BaseToolDeclaration):
    """A declarative class for defining a measurement monitor contribution.

    Monitor object can be contributed as extensions child to the
    'monitors' extension point of the 'exopy.measurement' plugin.

    """

    @d_func
    def create_item(self, workbench, area):
        """Create a dock item to display the informations of a monitor.

        The item must be created with a name matching the id.
        ex : return MyItem(name=self.id)

        Parameters
        ----------
        workbench :
            Reference to the application workbench.

        area :
            Dock area to use as the dock item parent.

        """
        pass
