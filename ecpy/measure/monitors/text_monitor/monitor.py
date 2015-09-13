# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
# XXXX
"""

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from ast import literal_eval
from textwrap import fill

import enaml
from atom.api import (List, Dict, ForwardTyped)

from ..base_monitor import BaseMonitor
from .entries import MonitoredEntry

with enaml.imports():
    from enaml.stdlib.message_box import information


def import_monitor_plugin():
    """ Delayed import of the plugin to avoid circular imports.

    """
    from .text_monitor_plugin import TextMonitorPlugin
    return TextMonitorPlugin


class TextMonitor(BaseMonitor):
    """Simple monitor displaying entries as text in a widget.

    """
    #: List of the entries which should be displayed when a measure is running.
    displayed_entries = List(MonitoredEntry)

    #: List of the entries which should not be displayed when a measure is
    #: running.
    undisplayed_entries = List(MonitoredEntry)

    #: List of the entries which should be not displayed when a measure is
    #: running because they would be redundant with another entry. (created by
    #: a rule for example.)
    hidden_entries = List(MonitoredEntry)

    #: Mapping between a database entry and a list of callable used for
    #: updating a monitor entry which relies on the database entry.
    updaters = Dict()

    #: List of rules which should be used to build monitor entries.
    rules = List()

    #: List of user created monitor entries.
    custom_entries = List(MonitoredEntry)

    def process_news(self, news):
        """Handle a news by calling every related entrt updater.

        """
        key, value = news
        values = self._database_values
        values[key] = value
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

        for entry, value in entries.iteritems():
            self.handle_database_change(('added', entry, value))

    # XXXX
    def handle_database_change(self, news):
        """Generate new entries for added values and clean removed values.

        """
        # Handle the addition of a new entry to the database
        if news[0] == 'added':

            _, path, value = news

            # Store the new value.
            self._database_values[path] = value

            # Add a default entry to the displayed monitor entries.
            new_entry = self._create_default_entry(path, value)
            self.displayed_entries.append(new_entry)  # XXXX GUI

            # Try to apply rules.
            for rule in self.rules:
                rule.try_apply(path, self)

            # Check whether any custom entry is currently hidden.
            hidden_custom = [e for e in self.custom_entries
                             if e not in self.displayed_entries or
                             e not in self.undisplayed_entries]

            # If there is one checks whether all the dependences are once
            # more available.
            if hidden_custom:
                for e in hidden_custom:
                    if all(d in self.database_entries for d in e.depend_on):
                        self.displayed_entries.append(e)  # XXXX GUI

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

            if path in self.database_entries:
                self.database_entries.remove(path)

            if path in self._database_values:
                del self._database_values[path]

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
            prefs[aux] = rule.preferences_from_members()

        # Get the state of each entry based on its path.
        prefs['displayed'] = repr([e.path for e in self.displayed_entries])
        prefs['undisplayed'] = repr([e.path for e in self.undisplayed_entries])
        prefs['hidden'] = repr([e.path for e in self.hidden_entries])

        return prefs

    def set_state(self, config, entries):
        """Rebuild all rules and dispatch entries according to the state.

        """
        # Request all the rules class from the plugin.
        rules_config = [conf for name, conf in config.iteritems()
                        if name.startswith('rule_')]

        # Rebuild all rules.
        rules = []
        for rule_config in rules_config:
            rule = self._plugin.build_rule(rule_config)
            if rule is not None:
                rules.append(rule)

        self.rules = rules

        customs_config = [conf for name, conf in config.iteritems()
                          if name.startswith('custom_')]
        for custom_config in customs_config:
            entry = MonitoredEntry()
            entry.update_members_from_preferences(**custom_config)
            self.custom_entries.append(entry)

        self.refresh_monitored_entries(entries)

        m_entries = set(self.displayed_entries + self.undisplayed_entries +
                        self.hidden_entries + self.custom_entries)

        pref_disp = literal_eval(config['displayed'])
        pref_undisp = literal_eval(config['undisplayed'])
        pref_hidden = literal_eval(config['hidden'])

        disp = [e for e in m_entries if e.path in pref_disp]
        m_entries -= set(disp)
        undisp = [e for e in m_entries if e.path in pref_undisp]
        m_entries -= set(undisp)
        hidden = [e for e in m_entries if e.path in pref_hidden]
        m_entries -= set(hidden)

        if m_entries:
            e_l = [e.name for e in m_entries]
            mess = ('The following entries were not expected from the config :'
                    ' {}. These entries has been added to the displayed ones.')
            information(parent=None,
                        title='Unhandled entries',
                        text=fill(mess.format(e_l)))
            pref_disp += list(m_entries)

        self.displayed_entries = disp
        self.undisplayed_entries = undisp
        self.hidden_entries = hidden

    # XXXX
    @property
    def all_database_entries(self):
        """ Getter returning all known database entries.

        """
        return self._database_values.keys()

    def add_rule_to_plugin(self, rule_name):
        """ Add a rule definition to the plugin.

        Parameters
        ----------
        rule_name : unicode
            Name of the rule whose description should be added to the plugin.
            If the rule is already known (same name) this is a no-op.

        """
        plugin = self._plugin
        if rule_name in self._plugin.rules:
            return

        config = {}
        for rule in self.rules:
            if rule.name == rule_name:
                config = rule.preferences_from_members()
                break

        if config:
            plugin.rules[rule_name] = config

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
            self.database_entries = []

    # XXXX
    def _observe_displayed_entries(self, change):
        """ Observer updating internals when the displayed entries change.

        This observer ensure that the list of database entries which need to
        be monitored reflects the actual needs of the monitor and that the
        monitor entries updaters mapping is up to date.

        """
        if change['type'] == 'update':
            added = set(change['value']) - set(change['oldvalue'])
            removed = set(change['oldvalue']) - set(change['value'])

            for entry in removed:
                self._displayed_entry_removed(entry)
            for entry in added:
                self._displayed_entry_added(entry)

        elif change['type'] == 'container':
            op = change['operation']
            if op in ('__iadd__', 'append', 'extend', 'insert'):
                if 'item' in change:
                    self._displayed_entry_added(change['item'])
                if 'items' in change:
                    for entry in change['items']:
                        self._displayed_entry_added(entry)

            elif op in ('__delitem__', 'remove', 'pop'):
                if 'item' in change:
                    self._displayed_entry_removed(change['item'])
                if 'items' in change:
                    for entry in change['items']:
                        self._displayed_entry_removed(entry)

            elif op in '__setitem__':
                old = change['olditem']
                if isinstance(old, list):
                    for entry in old:
                        self._displayed_entry_removed(entry)
                else:
                    self._displayed_entry_removed(old)

                new = change['newitem']
                if isinstance(new, list):
                    for entry in new:
                        self._displayed_entry_added(entry)
                else:
                    self._displayed_entry_added(new)

    # XXXX
    def _displayed_entry_added(self, entry):
        """ Tackle the addition of a displayed monitor entry.

        First this method will add the entry updater into the updaters dict for
        each of its dependence and if one dependence is absent from the
        database_entries it will be added.

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

            if dependence not in self.database_entries:
                self.database_entries.append(dependence)

    # XXXX
    def _displayed_entry_removed(self, entry):
        """ Tackle the deletion of a displayed monitor entry.

        First this method will remove the entry updater for each of its
        dependence and no updater remain for that database entry, the entry
        will be removed from the database_entries

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
                self.database_entries.remove(dependence)
