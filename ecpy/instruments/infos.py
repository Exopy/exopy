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

from atom.api import Atom, Unicode, Dict, Callable, List


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


# XXXX
class InstrumentModelInfos():
    """Details about a particular model based on all the available drivers.

    """
    #: Instrument manufacturer (this is the real manufacturer not an alias).
    manufacturer = Unicode()

    #: Instrument model.
    model = Unicode()

    #: Instrument serie.
    serie = Unicode()

    #: Instrument kind.
    kind = Unicode()

    #: List of supported drivers.
    drivers = List()

    #: Supported connections (all drivers connections infos are merged).
    connections = Dict()

    #: Supported settings (all drivers settings infos are merged).
    settings = Dict()

    def find_matching_driver(self, connection_id, settings_id):
        """
        """
        pass
