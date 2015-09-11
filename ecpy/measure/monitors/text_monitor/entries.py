# -*- coding: utf-8 -*-
# =============================================================================
# module : entries.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
from atom.api import (Unicode, List)
from enaml.application import deferred_call
from hqc_meas.utils.atom_util import HasPrefAtom


class MonitoredEntry(HasPrefAtom):
    """ Entry to display by the text monitor.

    """
    # User understandable name of the monitor entry.
    name = Unicode().tag(pref=True)

    # Full name of the entry as found or built from the database.
    path = Unicode().tag(pref=True)

    # Formatting of the entry.
    formatting = Unicode().tag(pref=True)

    # Current value that the monitor should display.
    value = Unicode()

    # List of database entries the entry depend_on.
    depend_on = List().tag(pref=True)

    def update(self, database_vals):
        """ Method updating the value of the entry given the current state of
        the database.

        """
        # TODO :  handle evaluation delimited by $
        vals = {d: database_vals[d] for d in self.depend_on}
        new_val = self.formatting.format(**vals)
        deferred_call(setattr, self, 'value', new_val)
