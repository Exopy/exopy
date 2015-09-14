# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Rules allow to defines some automatic handling of database entries in the
TextMonitor.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import (Unicode, Bool)

from ..entries import MonitoredEntry
from .base import BaseRule


class RejectRule(BaseRule):
    """Automatically remove an entry given the specified suffixes.

    """
    def try_apply(self, new_entry, monitor):
        """Hide an entry if it suffix match.

        """
        for suffix in self.suffixes:
            if new_entry.endswith(suffix):
                for entry in monitor.displayed_entries:
                    if entry.path == new_entry:
                        monitor.move_entries('displayed', 'undisplayed',
                                             (new_entry,))
                        break


class FormatRule(BaseRule):
    """ Create a new entry with a special formatting if some entries exist.

    Simple entries which would be redundant with the informations contained
    in the new formatting can be automatically hidden.

    """
    #: The format in which the new entry created by the rule should be
    #: displayed
    new_entry_formatting = Unicode().tag(pref=True)

    #: The suffix of the new entry created by the rule.
    new_entry_suffix = Unicode().tag(pref=True)

    #: Whether or not to hide the entries used by the rules.
    hide_entries = Bool(True).tag(pref=True)

    def try_apply(self, new_entry, monitor):
        """If all suffixes are found for a single task, create a new entry
        and hide the components if asked to.

        """
        entries = monitor.database_entries
        for suffix in self.suffixes:
            # Check whether the new entry match one suffix
            if new_entry.endswith(suffix):
                entry_path, entry_name = new_entry.rsplit('/', 1)

                # Getting the prefix of the entry (remove the found suffix)
                prefix = entry_path + '/' + entry_name.replace('_' + suffix,
                                                               '_')
                # Find all entries with the same prefix.
                prefixed_entries = [entry for entry in entries
                                    if entry.startswith(prefix)]

                # Check if all the entries needed to apply the rule exists.
                if all(any(entry.endswith(suffix)
                           for entry in prefixed_entries)
                       for suffix in self.suffixes):

                    # Create the name of the entry.
                    name_prefix = entry_name.replace('_' + suffix, '')
                    name = name_prefix + '_' + self.new_entry_suffix
                    path = entry_path + '/' + name

                    # Create the right formatting by replacing the rule fields
                    # by the full name of the entries.
                    formatting = self.new_entry_formatting
                    for suffix in self.suffixes:
                        formatting = formatting.replace(suffix,
                                                        prefix + suffix)

                    # Create a list of all the dependencies.
                    depend = [prefix + suffix
                              for suffix in self.suffixes]

                    # Create the monitor entry and add it to the list of
                    # displayed entries.
                    entry = MonitoredEntry(name=name, path=path,
                                           formatting=formatting,
                                           depend_on=depend)
                    monitor.displayed_entries.append(entry)

                    # If requested hide all the entries redundant with the
                    # one created by the rule.
                    if self.hide_entries:
                        for prefixed_entry in prefixed_entries:
                            for entry in monitor.displayed_entries:
                                if entry.path == prefixed_entry:
                                    monitor.hidden_entries.append(entry)
                                    monitor.displayed_entries.remove(entry)
                                    break
                else:
                    break
