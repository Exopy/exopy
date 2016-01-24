# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Container objects used to encapsulate info about drivers, instruments, etc

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from collection import defaultdict

from atom.api import Atom, Unicode, Dict, Callable


class DriverInfos(Atom):
    """Object summarizing the information about a driver.

    """
    #: Actual class to use as driver.
    cls = Callable()

    #: Infos allowing to identify the instrument this driver is targetting.
    infos = Dict()

    #: Starter id
    starter = Unicode()

    #: Connection information.
    connections = Dict()

    #: Settings information.
    settings = Dict()

    def validate(self, plugin):
        """Validate that starter, connections, settings ids are all known.

        Parameters
        ----------
        plugin :
            Instrument plugin instance holding the starters (connections,
            settings) definitions.

        Returns
        -------
        result : bool
            Boolean indicating if allids are indeed known.

        unknown : dict
            Mapping listing by categories (starter, connections, settings) the
            unkown ids.

        """
        result = True
        unknown = defaultdict(set)

        if self.starter not in plugin.starters:
            result = False
            unknown['starter'].add(self.starter)

        for k in self.connections.keys():
            if k not in plugin.connections:
                result = False
                unknown['connections'].add(k)

        for k in self.settings.keys():
            if k not in plugin.settings:
                result = False
                unknown['settings'].add(k)

        return result, unknown


class InstrumentModelInfos():
    """
    """
    pass