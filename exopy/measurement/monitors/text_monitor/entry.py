# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Entries that can be displayed by the text monitor.

"""
from atom.api import (Str, List)
from enaml.application import deferred_call

from exopy.utils.atom_util import HasPrefAtom


class MonitoredEntry(HasPrefAtom):
    """Entry to display by the text monitor.

    """
    #: User understandable name of the monitored entry.
    name = Str().tag(pref=True)

    #: Full name of the entry as found or built from the database.
    path = Str().tag(pref=True)

    #: Formatting of the entry.
    formatting = Str().tag(pref=True)

    #: Current value that the monitor should display.
    value = Str()

    #: List of database entries the entry depend_on.
    depend_on = List().tag(pref=True)

    def update(self, database_vals):
        """ Method updating the value of the entry given the current state of
        the database.

        """
        # TODO :  handle evaluation delimited by $. Imply a try except
        vals = {d: database_vals[d] for d in self.depend_on}
        new_val = self.formatting.format(**vals)
        deferred_call(setattr, self, 'value', new_val)
