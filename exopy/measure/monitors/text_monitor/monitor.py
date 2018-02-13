# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""The text monitor displays the database values it observes in a text format.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import os
from ast import literal_eval
from textwrap import fill

import enaml
from atom.api import (List, Dict, ForwardTyped, Property, Value)

from ..base_monitor import BaseMonitor
from .entry import MonitoredEntry

with enaml.imports():
    from enaml.stdlib.message_box import information


def import_monitor_plugin():
    """ Delayed import of the plugin to avoid circular imports.

    """
    from .plugin import TextMonitorPlugin
    return TextMonitorPlugin


class TextMonitor(BaseMonitor):
    """Simple monitor displaying entries as text in a widget.

    """
    #: List of the entries which should be displayed when a measure is running.
    #: This should not be manipulated directly by user code.
    displayed_entries = List(MonitoredEntry)

    #: List of the entries which should not be displayed when a measure is
    #: running. This should not be manipulated directly by user code.
    undisplayed_entries = List(MonitoredEntry)

    #: List of the entries which should be not displayed when a measure is
    #: running because they would be redundant with another entry. (created by
    #: a rule for example.)
    #: This should not be manipulated directly by user code.
    hidden_entries = List(MonitoredEntry)

    #: Mapping between a database entry and a list of callable used for
    #: updating a monitor entry which relies on the database entry.
    updaters = Dict()

    #: List of rules which should be used to build monitor entries.
    rules = List()

    #: List of user created monitor entries.
    custom_entries = List(MonitoredEntry)

    #: List of all the known database entries.
    known_monitored_entries = Property()

    def process_news(self, news):
        """Handle a news by calling every related entrt updater.

        """
        key, value = news
        values = self._database_values
        values[key] = value
        if key in self.updaters:
            for updater in self.updaters[key]:
                updater(values)

    def refresh_monitored_entries(self, entries=None):
        """Rebuild entries based on the rules and database entries.

        Parameters
        ----------
        entries : dict, optional
            Database entries to use when rebuilding the monitor entries.

        """
        if not entries:
            entries = self._database_values
        else:
            self._database_values = entries

        # Preserve the custom entries.
        custom = self.custom_entries[:]

        self._clear_state()
        self.custom_entries = custom

        for entry, value in entries.items():
            self.handle_database_entries_change(('added', entry, value))

    def handle_database_entries_change(self, news):
        """Generate new entries for added values and clean removed values.

        """
        # Unwrap multiple notifications.
        if isinstance(news[0], tuple):
            for n in news:
                self.handle_database_entries_change(n)

        # Handle the addition of a new entry to the database
        if news[0] == 'added':

            _, path, value = news

            # Store the new value.
            self._database_values[path] = value

            # Add a default entry to the displayed monitor entries.
            new_entry = self._create_default_entry(path, value)
            self.add_entries('displayed', (new_entry,))

            # Try to apply rules.
            for rule in self.rules:
                rule.try_apply(path, self)

            # Check whether any custom entry is currently hidden.
            hidden_custom = [e for e in self.custom_entries
                             if e not in self.displayed_entries and
                             e not in self.undisplayed_entries]

            # If there is one checks whether all the dependences are once
            # more available.
            if hidden_custom:
                for e in hidden_custom:
                    if all(d in self.monitored_entries for d in e.depend_on):
                        self.add_entries('displayed', (e,))

        # Handle the case of a database entry being suppressed, by removing all
        # monitors entries which where depending on this entry.
        elif news[0] == 'removed':

            _, path = news
            self.displayed_entries = [m for m in self.displayed_entries
                                      if path not in m.depend_on]
            self.undisplayed_entries = [m for m in self.undisplayed_entries
                                        if path not in m.depend_on]
            self.hidden_entries = [m for m in self.hidden_entries
                                   if path not in m.depend_on]

            if path in self.monitored_entries:
                self.monitored_entries.remove(path)

            if path in self.updaters:
                del self.updaters[path]

            if path in self._database_values:
                del self._database_values[path]

        # Handle the case of a database entry being renamed.
        elif news[0] == 'renamed':

            _, old, new, value = news
            _, old_entry_name = old.rsplit('/', 1)
            _, new_entry_name = new.rsplit('/', 1)
            suffix = os.path.commonprefix((old_entry_name[::-1],
                                           new_entry_name[::-1]))[::-1]
            old_task_name = old_entry_name[:-len(suffix)]
            new_task_name = new_entry_name[:-len(suffix)]
            for entries in ('displayed_entries', 'undisplayed_entries',
                            'hidden_entries'):
                for entry in getattr(self, entries):
                    if entry.path == old:
                        entry.path = new
                        entry.name = new_entry_name
                    elif old_task_name in entry.name:
                        entry.name = (new_task_name +
                                      entry.name[len(old_task_name):])

                    if old in entry.depend_on:
                        new_dep = entry.depend_on[:]
                        new_dep[new_dep.index(old)] = new
                        entry.depend_on = new_dep

            if old in self.monitored_entries:
                ind = self.monitored_entries.index(old)
                new_entries = self.monitored_entries[:]
                new_entries[ind] = new
                self.monitored_entries = new_entries

            if old in self.updaters:
                self.updaters[new] = self.updaters[old]
                del self.updaters[old]

            if old in self._database_values:
                del self._database_values[old]
                self._database_values[new] = value

    def handle_database_nodes_change(self, news):
        """Update the paths when a node is renamed.

        """
        # Unwrap multiple notifications.
        if isinstance(news[0], tuple):
            for n in news:
                self.handle_database_nodes_change(n)

        if news[0] == 'renamed':

            _, path, old, new = news
            old_path = path + '/' + old
            new_path = path + '/' + new
            for entries in ('displayed_entries', 'undisplayed_entries',
                            'hidden_entries'):
                for entry in getattr(self, entries):
                    if entry.path.startswith(old_path):
                        entry.path = new_path + entry.path[len(old_path):]

                    new_depend_on = []
                    for p in entry.depend_on:
                        if p.startswith(old_path):
                            new_depend_on.append(new_path + p[len(old_path):])
                        else:
                            new_depend_on.append(p)
                    entry.depend_on = new_depend_on

            new_monitored = []
            for e in self.monitored_entries:
                if e.startswith(old_path):
                    new_monitored.append(new_path + e[len(old_path):])
                else:
                    new_monitored.append(e)
            self.monitored_entries = new_monitored

            for attr in ('updaters', '_database_values'):
                new_val = {}
                for k, v in getattr(self, attr).items():
                    if k.startswith(old_path):
                        new_val[new_path + k[len(old_path):]] = v
                    else:
                        new_val[k] = v
                setattr(self, attr, new_val)

    def get_state(self):
        """Write the state of the monitor in a dictionary.

        """
        prefs = self.preferences_from_members()

        # Get the definitions of the custom entries.
        for i, custom_entry in enumerate(self.custom_entries):
            aux = 'custom_{}'.format(i)
            prefs[aux] = custom_entry.preferences_from_members()

        # Get the definitions of the rules.
        for i, rule in enumerate(self.rules):
            aux = 'rule_{}'.format(i)
            if rule.id in self._plugin._rule_configs.contributions:
                prefs[aux] = rule.id
            else:
                prefs[aux] = rule.preferences_from_members()

        # Get the displayed/undisplayed status of each entry based on its path.
        # If the monitor was never linked keep the values stored.
        if self._state:
            prefs['displayed'] = self._state['displayed']
            prefs['undisplayed'] = self._state['undisplayed']
            prefs['hidden'] = self._state['hidden']
        else:
            prefs['displayed'] = repr([e.path for e in self.displayed_entries])
            prefs['undisplayed'] = repr([e.path
                                         for e in self.undisplayed_entries])
            prefs['hidden'] = repr([e.path for e in self.hidden_entries])

        return prefs

    def set_state(self, state):
        """Rebuild all rules and dispatch entries according to the state.

        """
        # Identify all the rules.
        rules_config = [conf for name, conf in state.items()
                        if name.startswith('rule_')]

        # Rebuild all rules.
        rules = []
        for rule_config in rules_config:
            rule = self._plugin.build_rule(rule_config)
            if rule is not None:
                rules.append(rule)

        self.rules = rules

        customs_config = [conf for name, conf in state.items()
                          if name.startswith('custom_')]
        for custom_config in customs_config:
            entry = MonitoredEntry()
            entry.update_members_from_preferences(custom_config)
            self.custom_entries.append(entry)

        self._state = state

    def link_to_measure(self, measure):
        """Set the entries according to the state if one is present.

        """
        super(TextMonitor, self).link_to_measure(measure)
        database = measure.root_task.database
        self.refresh_monitored_entries(database.list_all_entries(values=True))

        if self._state:
            m_entries = set(self.displayed_entries + self.undisplayed_entries +
                            self.hidden_entries + self.custom_entries)

            config = self._state
            del self._state
            pref_disp = literal_eval(config['displayed'])
            pref_undisp = literal_eval(config['undisplayed'])
            pref_hidden = literal_eval(config['hidden'])

            disp = [e for e in m_entries if e.path in pref_disp]
            m_entries -= set(disp)
            undisp = [e for e in m_entries if e.path in pref_undisp]
            m_entries -= set(undisp)
            hidden = [e for e in m_entries if e.path in pref_hidden]
            m_entries -= set(hidden)

            # TODO this should not assume the UI exists
            if m_entries:
                e_l = [e.name for e in m_entries]
                mess = ('The following entries were not expected from the '
                        'config :  {}. These entries has been added to the '
                        'displayed ones.')
                information(parent=None,
                            title='Unhandled entries',
                            text=fill(mess.format(e_l)))
                disp += list(m_entries)

            self.displayed_entries = disp
            self.undisplayed_entries = undisp
            self.hidden_entries = hidden

    def add_entries(self, section, entries):
        """Add entries to the specified section.

        The entries should not be present in another section. (save hidden)

        Parameters
        ----------
        section : {'displayed', 'undisplayed', 'hidden'}
            Section in which to add the entries.

        entry : iterable[MonitoredEntry]
            Entries to add.

        """
        name = section+'_entries'
        container = getattr(self, name, None)
        if container is None:
            raise ValueError('Section must be one of : displayed, undisplayed,'
                             ' hidden, not %s' % section)

        copy = container[:]
        copy.extend(entries)

        if section == 'displayed':
            for e in entries:
                self._displayed_entry_added(e)

        setattr(self, name, copy)

    def move_entries(self, origin, destination, entries):
        """Move entries from a section to another.

        Parameters
        ----------
        origin : {'displayed', 'undisplayed', 'hidden'}
            Section in which the entries currently are.

        destination : {'displayed', 'undisplayed', 'hidden'}
            Section in which to put the entries.

        entries : iterable[MonitoredEntry]
            Entries to move.

        """
        o_name = origin+'_entries'
        o_container = getattr(self, o_name, None)
        if o_container is None:
            raise ValueError('Origin must be one of : displayed, undisplayed,'
                             ' hidden, not %s' % origin)

        d_name = destination+'_entries'
        d_container = getattr(self, d_name, None)
        if d_container is None:
            raise ValueError('Destination must be one of : displayed, '
                             'undisplayed, hidden, not %s' % destination)

        if origin == 'displayed':
            for e in entries:
                self._displayed_entry_removed(e)

        if destination == 'displayed':
            for e in entries:
                self._displayed_entry_added(e)

        setattr(self, o_name, [e for e in o_container if e not in entries])

        copy = d_container[:]
        copy.extend(entries)
        setattr(self, d_name, copy)

    def remove_entries(self, section, entries):
        """Remove entries to the specified section.

        The entries should not be present in another section.

        Parameters
        ----------
        section : {'displayed', 'undisplayed', 'hidden'}
            Section from which to remove the entries.

        entry : iterable[MonitoredEntry]
            Entries to remove.

        """
        name = section+'_entries'
        container = getattr(self, name, None)
        if container is None:
            raise ValueError('Origin must be one of : displayed, undisplayed,'
                             ' hidden, not %s' % section)

        if section == 'displayed':
            for e in entries:
                self._displayed_entry_removed(e)

        setattr(self, name, [e for e in container if e not in entries])

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: Known values of the database entries used when recomputing an entry
    #: value depending not on a single value. During edition all values are
    #: stored, regardless of whether or not the entry needs to be observed,
    #: when the start method is called the dict is cleaned.
    _database_values = Dict()

    #: Reference to the monitor plugin handling the rules persistence.
    _plugin = ForwardTyped(import_monitor_plugin)

    #: Temporary storage of the state that is preserved till the tool is
    #: linked to a measure.
    _state = Value()

    @staticmethod
    def _create_default_entry(entry_path, value):
        """ Create a monitor entry for a database entry.

        Parameters
        ----------
        entry_path : unicode
            Path of the database entries for which to create a monitor entry.

        Returns
        -------
        entry : MonitoredEntry
            Monitor entry to be added to the monitor.

        """
        _, name = entry_path.rsplit('/', 1)
        formatting = '{' + entry_path + '}'
        entry = MonitoredEntry(name=name, path=entry_path,
                               formatting=formatting, depend_on=[entry_path])
        entry.value = '{}'.format(value)
        return entry

    def _clear_state(self):
        """ Clear the monitor state.

        """
        with self.suppress_notifications():  # Need to clarify this
            self.displayed_entries = []
            self.undisplayed_entries = []
            self.hidden_entries = []
            self.updaters = {}
            self.custom_entries = []
            self.monitored_entries = []

    def _displayed_entry_added(self, entry):
        """ Tackle the addition of a displayed monitor entry.

        First this method will add the entry updater into the updaters dict for
        each of its dependence and if one dependence is absent from the
        monitored_entries it will be added.

        Parameters
        ----------
        entry : MonitoredEntry
            The entry being added to the list of displayed entries of the
            monitor.

        """
        for dependence in entry.depend_on:
            if dependence in self.updaters:
                self.updaters[dependence].append(entry.update)
            else:
                self.updaters[dependence] = [entry.update]

            if dependence not in self.monitored_entries:
                self.monitored_entries.append(dependence)

    def _displayed_entry_removed(self, entry):
        """ Tackle the deletion of a displayed monitor entry.

        First this method will remove the entry updater for each of its
        dependence and no updater remain for that database entry, the entry
        will be removed from the monitored_entries

        Parameters
        ----------
        entry : MonitoredEntry
            The entry being added to the list of displayed entries of the
            monitor.

        """
        for dependence in entry.depend_on:
            self.updaters[dependence].remove(entry.update)

            if not self.updaters[dependence]:
                del self.updaters[dependence]
                self.monitored_entries.remove(dependence)

    def _get_known_monitored_entries(self):
        """Getter for the known_monitored_entries property.

        """
        return self._database_values.keys()
