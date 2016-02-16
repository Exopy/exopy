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
from itertools import chain

from atom.api import (Atom, Unicode, Dict, Callable, List, Property, Typed,
                      Bool)


class DriverInfos(Atom):
    """Object summarizing the information about a driver.

    """
    #: Id of the driver built on the class name and the top-level package
    id = Unicode()

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


class SeriesInfos(Atom):
    """Container object used to store series infos.

    """
    #: Name of the serie.
    name = Unicode()

    #: List of all declared instrument models.
    #: This object should not be manipulated by user code.
    instruments = List()

    #: Expose the known instruments only of the matching kind.
    kind = Unicode('All')

    def add_model(self, model):
        """Add a model to the serie and update the instruments list.

        """
        self._models.append(model)
        self.instruments = self._list_instruments()

    def remove_model(self, model):
        """Remove a model from the serie and update the instruments list.

        """
        self._models.remove(model)
        self.instruments = self._list_instruments()

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: All known instrument models.
    _models = List()

    def _post_setattr_kind(self, old, new):
        """Regenerate the list of models.

        """
        self.instruments = self._list_instruments()

    def _list_instruments(self, models):
        """List all the known models matching the expected kind.

        Parameters
        ----------

        """
        f = lambda x: x.kind == self.kind if self.kind != 'All' else None

        return filter(f, models)


class ManufaturerInfos(SeriesInfos):
    """Container object used to store manufacturer infos.

    Notes
    -----
    Models are stored by series in instruments member if use_series is True

    """
    #: All known series for this manufacturer.
    #: This object should not be manipulated by user code.
    series = List()

    #: Expose the known instrument by series.
    use_series = Bool(True)

    #: Known aliases for the manufacturer.
    aliases = List()

    def add_serie(self, serie):
        """Add a new serie and regenerate the instruments list.

        """
        self.series = self.serie[:] + [serie]
        self._list_instruments(())

    def remove_serie(self, serie):
        """Remove a serie and regenerate the instrument list.

        """
        s = self.serie[:]
        s.remove(serie)
        self.series = s
        self._list_instruments(())

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    def _post_setattr_use_series(self, old, new):
        """Update the list of models when the usage of series is modified.

        """
        self._list_instruments(())

    def _post_setattr_kind(self, old, new):
        """Regenerate the list of models.

        """
        for s in self.series:
            s.kind = new
        super(ManufaturerInfos, self)._post_setattr_kind(old, new)

    def _list_instruments(self, models):
        """Build the list of models using either series or not.

        """
        if not self.use_series:
            models = chain(self._models, *[s.instruments for s in self.series])
            return super(ManufaturerInfos, self)._list_instruments(models)
        else:
            models = super(ManufaturerInfos, self)._list_instruments()
            return [s for s in self.series if s.instruments] + models


class InstrumentModelInfos(Atom):
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

    #: Id of the model.
    id = Property(cached=True)

    def find_matching_drivers(self, connection_id, settings_id=None):
        """Find the matching driver implementation.

        Parameters
        ----------
        connection_id : unicode
            Connection id for which to for a matching driver.

        settings_id : unicode, optional
            Settings id for which to find a matching id.

        """
        drivers = [d for d in self.drivers if connection_id in d.connections]
        if settings_id:
            drivers = [d for d in drivers if settings_id in d.settings]
        return drivers

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    def _get_id(self):
        """Getter for the id property.

        """
        return self.manufacturer + '.' + self.model


class ProfileInfos(Atom):
    """Details about a profile.

    This is used as a cache to avoid reloading all the profile everytime.

    """
    #: Path to the .ini file holding the full infos.
    path = Unicode()

    #: Supported model
    model = Typed(InstrumentModelInfos)
